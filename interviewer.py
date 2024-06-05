import os
from os import PathLike
from time import time
import asyncio
from typing import Union

from dotenv import load_dotenv
import openai
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

# Load the .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Initialize openAI and elevenlabs clients
gpt_client = openai.Client(api_key=OPENAI_API_KEY)
client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
)

context = "You are an AI interviewer called Katy. You are interviewing a candidate for a software engineering position. Keep your responses to no more than 2-3 sentences."
conversation = {"Conversation": []}

def gpt_chat(prompt: str) -> str:
    """
    Send a prompt to the GPT-3 API and return the response.

    Args:
        - state: The current state of the app.
        - prompt: The prompt to send to the API.

    Returns:
        The response from the API.
    """
    response = gpt_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"{prompt}",
            }
        ],
        model="gpt-3.5-turbo",
    )
    return response.choices[0].message.content

# Interviewer does the interview
# Calls GPT and runs through elevenlabs to get audio, it will return the path to the audio file
def interviewer(urlPath: str, filename: str, ) -> str:
    global context # TODO store context separately

    current_time = time()

    # Read transcript file
    if os.path.exists(urlPath):
        with open(urlPath, 'r', encoding='utf-8') as file:
            file_content = file.read()
    else:
        print(f"The file {urlPath} does not exist.")

    # Pass to gpt to get response
    context += f"\nCandidate: {file_content} \nKaty: "
    response = gpt_chat(context)
    context += response

    print(f"Gpt Time taken: {time() - current_time}")

    # Pass to elevenlabs to get audio
    audio = client.text_to_speech.convert(
        voice_id="XfNU2rGpBa01ckF309OY", # Katy's voice is actually Nichalia Schwartz
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=response,
        model_id="eleven_turbo_v2",
    )

    print(f"Elevenlabs Time taken: {time() - current_time}")

    # Create audio filename with same timestamp for tracebility
    # Split the filename at the underscore '_'
    parts = filename.split('_')

    # Change the prefix and the extension
    new_filename = 'response_' + parts[1].replace('.txt', '.mp3')
    save_file_path = f"response/{new_filename}"

    # Writing the audio to a file
    with open(save_file_path, "wb") as f:
        for chunk in audio:
            if chunk:
                f.write(chunk)

    print(f"{save_file_path}: A new audio file was saved successfully!")

    print(f"Total Time taken: {time() - current_time}")
    # Return the path of the saved audio file
    return save_file_path


def wipe_conversation():
    global context, conversation
    conversation = {"Conversation": []}
    context = "You are an AI interviewer called Katy. You are interviewing a candidate for a software engineering position. Keep your responses to no more than 2-3 sentences."
    


# interviewer('transcripts/Transcript_1717569998419.txt', 'Transcript_1717569998419.txt')