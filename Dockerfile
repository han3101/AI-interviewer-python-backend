FROM python:3.11-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Create directories called transcripts and response
RUN mkdir transcripts response audio uploads
# Install any necessary packages specified in requirements.txt
# Include Uvicorn with standard requirements
RUN pip install --no-cache-dir -r requirements.txt uvicorn[standard]

RUN apt-get update && apt-get install -y ffmpeg

EXPOSE 8080

# Run the Uvicorn server when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]