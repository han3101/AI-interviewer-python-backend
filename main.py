from fastapi import FastAPI, status
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import os

app = FastAPI()

@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    return {"Hello": "World"}


@app.post("/upload")
async def handle_form_upload(file: UploadFile = File(...)):
    print(file.filename)
    file_location = f"transcripts/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())
    return JSONResponse(content={"info": "File saved", "filename": file.filename}, status_code=200)