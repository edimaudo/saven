
import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Initialize Wellness Environment
load_dotenv()
app = FastAPI(title="Saven Backend")

# Initialize the Gemini 3.1 Client
# We use v1alpha for the latest Multimodal Live capabilities
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={'api_version': 'v1alpha'}
)

# Saven's Core Persona & Configuration
LIVE_CONFIG = types.LiveConnectConfig(
    model="models/gemini-3.1-flash",
    response_modalities=["AUDIO"], # Saven speaks back
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede"))
    ),
    system_instruction="""You are Saven, a compassionate wellness expert. 
    Your goal is to HEAR the user's stress, HUG them with validating language, and HELP them with one small step. 
    Use a soft, steady tone. If the user is ranting, listen fully before responding."""
)

@app.websocket("/ws/saven-live")
async def saven_live_session(websocket: WebSocket):
    await websocket.accept()
    print("A new soul has entered Saven.")

    try:
        # Connect to Gemini 3.1 Live API
        async with client.aio.live.connect(model=LIVE_CONFIG.model, config=LIVE_CONFIG) as session:
            
            # Task 1: Receive Audio from Frontend -> Send to Gemini
            async def send_to_gemini():
                try:
                    async for message in websocket.iter_bytes():
                        # We send raw PCM audio data directly to Gemini
                        await session.send(input=message, end_of_turn=True)
                except Exception as e:
                    print(f"Audio Input Error: {e}")

            # Task 2: Receive Response from Gemini -> Send to Frontend
            async def receive_from_gemini():
                try:
                    async for response in session.receive():
                        # response.data contains the AI's generated audio bytes
                        if response.data:
                            await websocket.send_bytes(response.data)
                        
                        # Check for 'Tool Calls' (Future: Triggering the 'Visual Hug')
                        if response.server_content and response.server_content.model_turn:
                            print("Saven is thinking/generating...")
                except Exception as e:
                    print(f"Gemini Output Error: {e}")

            # Run both streams concurrently
            await asyncio.gather(send_to_gemini(), receive_from_gemini())

    except WebSocketDisconnect:
        print("User has left the haven.")
    except Exception as e:
        print(f"Critical Session Error: {e}")
