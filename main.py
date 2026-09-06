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

@app.route("/chat", methods=["GET", "POST", "OPTIONS"])
@app.route("/chat/", methods=["GET", "POST", "OPTIONS"])
async def chat_handler(request: Request):
    if request.method != "POST":
        return {"status": "Endpoint ready for POST raw PCM audio"}

    raw_audio = await request.body()
    if not raw_audio:
        return Response(status_code=400, content="No audio received")

    reply_text = "नमस्ते, मैं आपकी क्या मदद कर सकता हूँ?"

    try:
        if not model:
            reply_text = "कृपया रेंडर पर अपनी जेमिनी एपीआई की चेक करें।"
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
                "Transcribe this audio strictly and answer in 1 very short Hindi sentence.",
                {"mime_type": "audio/wav", "data": wav_data}
            ]
            response = model.generate_content(prompt)
            if response and response.text:
                reply_text = response.text.strip()
    except Exception as e:
        print(f"Error occurred: {e}")
        reply_text = "माफ़ कीजिये, ऑडियो प्रोसेस करने में समस्या हुई।"

    print(f"AI Response: {reply_text}")

    # Text to Speech MP3
    try:
        tts = gTTS(reply_text, lang='hi')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return Response(content=mp3_fp.read(), media_type="audio/mpeg")
    except Exception as e:
        print(f"TTS Error: {e}")
        return Response(status_code=500, content=str(e))
