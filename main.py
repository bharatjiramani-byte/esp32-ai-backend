import io
import os
import wave
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
import google.generativeai as genai

app = FastAPI()

# Sabhi methods aur origins allow karein (Taaki 405/CORS kabhi na aaye)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@app.get("/")
def home():
    return {"status": "AI Box Backend is Running"}

# Sabhi methods (GET, POST, OPTIONS) ko ek hi jagah handle karein
@app.route("/chat", methods=["GET", "POST", "OPTIONS"])
@app.route("/chat/", methods=["GET", "POST", "OPTIONS"])
async def chat_handler(request: Request):
    if request.method != "POST":
        return {"status": "Endpoint ready for POST raw PCM audio"}

    raw_audio = await request.body()
    if not raw_audio:
        return Response(status_code=400, content="No audio received")

    # 8000Hz, 16-bit Mono PCM to WAV
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(8000)
        wav_file.writeframes(raw_audio)
    
    wav_data = wav_io.getvalue()

    # Gemini se audio process karein
    prompt = [
        "Transcribe the audio strictly and answer in 1-2 very short, direct sentences in Hindi or English.",
        {"mime_type": "audio/wav", "data": wav_data}
    ]
    response = model.generate_content(prompt)
    reply_text = response.text
    print(f"AI: {reply_text}")

    # gTTS se MP3 bana kar raw stream karein
    tts = gTTS(reply_text, lang='hi')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)

    return Response(content=mp3_fp.read(), media_type="audio/mpeg")
