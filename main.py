import io
import os
import wave
from fastapi import FastAPI, Request, Response
from gtts import gTTS
import google.generativeai as genai

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@app.get("/")
def home():
    return {"status": "AI Box Backend is Running"}

@app.post("/chat")
async def chat_endpoint(request: Request):
    raw_audio = await request.body()
    if not raw_audio:
        return Response(status_code=400, content="No audio received")

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(raw_audio)
    
    wav_data = wav_io.getvalue()

    prompt = [
        "Transcribe this audio strictly and answer in 1-2 very short, natural sentences in Hindi or English.",
        {"mime_type": "audio/wav", "data": wav_data}
    ]
    response = model.generate_content(prompt)
    reply_text = response.text

    tts = gTTS(reply_text, lang='hi')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)

    return Response(content=mp3_fp.read(), media_type="audio/mpeg")
