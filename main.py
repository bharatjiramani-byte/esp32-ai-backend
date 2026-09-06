import io
import os
import wave
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
import google.generativeai as genai

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

# FastAPI me api_route use hota hai
@app.api_route("/chat", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/chat/", methods=["GET", "POST", "OPTIONS"])
async def chat_handler(request: Request):
    if request.method != "POST":
        return {"status": "Chat endpoint is ready for POST audio"}

    raw_audio = await request.body()
    if not raw_audio or len(raw_audio) < 1000:
        return Response(status_code=400, content="Audio buffer too small or empty")

    reply_text = "नमस्ते, मैं आपकी क्या सहायता कर सकता हूँ?"

    try:
        if not model:
            reply_text = "कृपया रेंडर पर जेमिनी एपीआई की सेट करें।"
        else:
            # 8000Hz, 16-bit Mono PCM to WAV
            wav_io = io.BytesIO()
            with wave.open(wav_io, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(8000)
                wav_file.writeframes(raw_audio)
            
            wav_data = wav_io.getvalue()

            prompt = [
    "You are a voice assistant in a physical smart box. Listen carefully to the user speech in this audio, understand the question, and provide a clear, helpful direct answer in 1 or 2 Hindi sentences.",
    {"mime_type": "audio/wav", "data": wav_data}
]
            response = model.generate_content(prompt)
            if response and response.text:
                reply_text = response.text.strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        reply_text = "माफ़ कीजिये, आपकी बात समझने में परेशानी हुई।"

    print(f"AI Response: {reply_text}")

    try:
        tts = gTTS(reply_text, lang='hi')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return Response(content=mp3_fp.read(), media_type="audio/mpeg")
    except Exception as e:
        print(f"TTS Error: {e}")
        return Response(status_code=500, content="TTS conversion failed")
