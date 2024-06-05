from fastapi import FastAPI, status
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, interviewer

app = FastAPI()

# Define the list of origins that should be allowed to make requests to your API
origins = [
    "http://localhost:3000",  # Your frontend origin
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
    

@app.post("/end")
async def handle_interview():

    # Call interviewer method with terminal end_endInterview.txt
    response_path = interviewer.interviewer('end_endInterview.txt', 'end_endInterview.txt')

    # Wipe GPT memory and conversation
    interviewer.wipe_conversation()
    
    # Check if the MP3 file was successfully created
    if os.path.exists(response_path):
        return FileResponse(response_path, media_type='audio/mpeg', filename=os.path.basename(response_path))
    else:
        return JSONResponse(content={"error": "Failed to generate audio file"}, status_code=500)