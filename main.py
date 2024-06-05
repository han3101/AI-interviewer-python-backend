from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, interviewer, asyncio
import shutil, subprocess, s3
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# Define the list of origins that should be allowed to make requests to your API
origins = [
    "http://localhost:3000",  # Your frontend origin
    "http://192.168.86.200:3000", # My personal frontend IP
    "https://apriora-sprint-hans-projects-299e57dd.vercel.app",
    "https://apriora-sprint.vercel.app",
    "https://apriora-sprint-lxbv53r8h-hans-projects-299e57dd.vercel.app",
    "http://20.9.136.70:3000",
    "http://localhost:3001"
]

# Add the CORS middleware to your FastAPI application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    return {"Hello": "World"}


@app.post("/upload")
async def handle_form_upload(file: UploadFile = File(...)):
    print(file.filename)
    file_location = f"transcripts/{file.filename}"
    
    # Ensure directory exists
    os.makedirs("transcripts", exist_ok=True)
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())

    print(f"File saved: {file_location}")
    return JSONResponse(content={"info": "File saved", "filename": file.filename}, status_code=200)

# Interview engine
@app.post("/interview")
async def handle_interview(file: UploadFile = File(...)):
    file_location = f"transcripts/{file.filename}"
    
    # Ensure directory exists
    os.makedirs("transcripts", exist_ok=True)
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())

    # Call interviewer method
    response_path = interviewer.interviewer(file_location, file.filename)

    # Check if the MP3 file was successfully created
    if os.path.exists(response_path):
        return FileResponse(response_path, media_type='audio/mpeg', filename=os.path.basename(response_path))
    else:
        return JSONResponse(content={"error": "Failed to generate audio file"}, status_code=500)
    

# Upload audio file, convert from webM to mp3 and upload to S3
@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    try:
        # Save uploaded file to disk or process as needed
        file_location = f"uploads/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())
        return JSONResponse(status_code=200, content={"message": "File uploaded successfully", "filePath": file_location})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
    

@app.post("/end")
async def end_interview(background_tasks: BackgroundTasks):

    # Load pre_recorded ending
    response_path = 'pre_recorded_audio/end_interview.mp3'

    # Wipe GPT memory and conversation
    interviewer.wipe_conversation()

    # Convert webm to mp3
    convert_webm_to_mp3('uploads')

    # Schedule the upload of all files to run in the background
    background_tasks.add_task(async_upload_files, 'audio')
    background_tasks.add_task(async_upload_files, 'response')
    background_tasks.add_task(async_upload_files, 'transcripts')

    # Clear transcripts
    clear_directories(['uploads'])

    
    # Check if the MP3 file was successfully created
    if os.path.exists(response_path):
        return FileResponse(response_path, media_type='audio/mpeg', filename=os.path.basename(response_path))
    else:
        return JSONResponse(content={"error": "Failed to generate audio file"}, status_code=500)
    

@app.post("/begin")
async def begin_interview():

    # Load pre_recorded ending
    response_path = 'pre_recorded_audio/begin_interview.mp3'

    # Wipe GPT memory and conversation
    interviewer.wipe_conversation()
    
    # Check if the MP3 file was successfully created
    if os.path.exists(response_path):
        return FileResponse(response_path, media_type='audio/mpeg', filename=os.path.basename(response_path))
    else:
        return JSONResponse(content={"error": "Failed to generate audio file"}, status_code=500)
    
@app.get("/get_files")
def get_files():
    bucket_name = 'apriora'
    files = s3.print_files(bucket_name)

    sorted_files = sort_and_format_files(files)
    if sorted_files is not None:
        return JSONResponse(content=sorted_files, status_code=200)
    else:
        return JSONResponse(content={"error": "Failed to get files from bucket"}, status_code=500)
    
@app.delete("/delete_interview")
def delete_interview():
    bucket_name = 'apriora'
    files = s3.print_files(bucket_name)
    if files is not None:
        for file in files:
            s3.delete_file(bucket_name, file)
        return JSONResponse(content={"message": "All files deleted successfully"}, status_code=200)
    else:
        return JSONResponse(content={"error": "Failed to delete files from bucket"}, status_code=500)

    




# ========================= Helper functions =========================
def clear_directories(dirs):
    """Clear all files in the specified list of directories."""
    for directory in dirs:
        # Check if the directory exists
        if os.path.exists(directory):
            # Remove all files and subdirectories in the directory
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)  # Remove files and links
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)  # Remove directories
            print(f"Cleared all items in {directory}.")
        else:
            print(f"Directory {directory} does not exist.")


def convert_webm_to_mp3(directory):
    """
    Convert all WebM audio files in the specified directory to MP3 format using ffmpeg.

    Parameters:
    directory (str): Path to the directory containing WebM files.
    """
    # List all files in the given directory
    for filename in os.listdir(directory):
        # Check if the file is a WebM file
        if filename.endswith(".WebM"):
            # Full path to the source WebM file
            webm_path = os.path.join(directory, filename)
            # Generate a new file name with .mp3 extension
            mp3_path = os.path.join('audio', os.path.splitext(filename)[0] + ".mp3")
            
            # Command to use ffmpeg to convert the audio format
            command = ['ffmpeg', '-i', webm_path, '-vn', '-ab', '192k', '-ar', '44100', '-y', mp3_path]
            
            try:
                # Execute the ffmpeg command
                subprocess.run(command, check=True)
                print(f"Converted '{webm_path}' to '{mp3_path}' successfully.")
            except subprocess.CalledProcessError:
                print(f"Failed to convert '{webm_path}'. ffmpeg error.")
            except Exception as e:
                print(f"An error occurred while converting '{webm_path}': {str(e)}")


async def async_upload_files(directory):
    """Asynchronously upload all .mp3 files in the specified directory to an S3 bucket."""
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor()

    # List files in the directory
    audio_files = [os.path.join(directory, file) for file in os.listdir(directory)]

    # Create asynchronous upload tasks
    tasks = []
    for audio_file in audio_files:
        # Schedule synchronous upload function to run in a separate thread
        task = loop.run_in_executor(executor, s3.upload_file, audio_file, 'apriora', audio_file)
        tasks.append(task)

    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

    # Clear the directory after uploading
    clear_directories([directory])

    # Cleanup executor
    executor.shutdown(wait=True)
    print("All files have been uploaded.")

def sort_and_format_files(files):
    base_url = "https://pub-c75380cac0bd497dabf63c820b8d729a.r2.dev/"
    file_map = {}

    # Process each file to organize by timestamp
    for file in files:
        parts = file.split('_')
        file_type = parts[0].split('/')[0]  # Extract the prefix like 'transcripts'
        timestamp = parts[1].split('.')[0]  # Extract the timestamp part

        # Ensure timestamp is numeric
        if not timestamp.isdigit():
            continue

        if timestamp not in file_map:
            file_map[timestamp] = {}

        # Convert file path to a URL format
        url_path = file.replace('/', '%2F')
        full_url = base_url + url_path

        # Organize files by type under each timestamp
        if 'transcript' in file_type:
            file_map[timestamp]['transcript'] = full_url
        elif 'response' in file_type:
            file_map[timestamp]['response'] = full_url
        elif 'audio' in file_type:
            file_map[timestamp]['audio'] = full_url

    # Create a new dictionary with sorted timestamps
    sorted_timestamps = sorted(file_map.keys())  # Sort keys numerically
    sorted_file_map = {ts: file_map[ts] for ts in sorted_timestamps}

    return sorted_file_map
