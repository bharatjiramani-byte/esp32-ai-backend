import io
import os
import wave
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
import google.generativeai as genai
import miniaudio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

@app.get("/")
def home():
    return {"status": "AI Box Backend is Running"}

@app.api_route("/chat", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/chat/", methods=["GET", "POST", "OPTIONS"])
async def chat_handler(request: Request):
    if request.method != "POST":
        return {"status": "Endpoint ready for POST raw PCM audio"}

    raw_audio = await request.body()
    if not raw_audio or len(raw_audio) < 1000:
        reply_text = "हे भैला, बोलो ने! आपकी आवाज़ नहीं आई।"
    else:
        try:
            if not model:
                reply_text = "हे भैला, रेंडर पर अपनी जेमिनी एपीआई की चेक करो।"
            else:
                # 8000Hz, 16-bit Mono PCM to WAV for Gemini
                wav_io = io.BytesIO()
                with wave.open(wav_io, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(8000)
                    wav_file.writeframes(raw_audio)

                prompt = [
                    (
                        "You are a friendly personal voice assistant with a Gujarati-Hindi tone. "
                        "Rule 1: Always start your response with 'हे भैला, बोलो ने! ' (or 'हे भैला, '). "
                        "Rule 2: Carefully listen to the question in the audio and give a clear, direct answer in 1 or 2 simple Hindi sentences. "
                        "Rule 3: If the user audio is silent, just hello, or unclear, say: 'हे भैला, बोलो ने! मैं सुन रहा हूँ, क्या काम है?'"
                    ),
                    {"mime_type": "audio/wav", "data": wav_io.getvalue()}
                ]
                response = model.generate_content(prompt)
                reply_text = response.text.strip() if (response and response.text) else "हे भैला, बोलो ने! मैं सुन रहा हूँ।"
        except Exception as e:
            print(f"Error: {e}")
            reply_text = "हे भैला, थोड़ा साफ़ आवाज़ में बोलो ने।"

    print(f"AI Response: {reply_text}")

    # Generate MP3 from gTTS
    tts = gTTS(reply_text, lang='hi')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_bytes = mp3_fp.getvalue()

    # Decode MP3 to raw 16-bit signed PCM (16000Hz Mono)
    decoded = miniaudio.mp3_read_s16(mp3_bytes)
    resampled_pcm = miniaudio.resample_s16(
        decoded.samples, 
        sample_rate_in=decoded.sample_rate, 
        sample_rate_out=16000, 
        channels_in=decoded.nchannels, 
        channels_out=1
    )

    # Return raw PCM byte stream directly to ESP32
    return Response(content=resampled_pcm.tobytes(), media_type="application/octet-stream")
