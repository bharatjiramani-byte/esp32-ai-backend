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
                # 8000Hz, 16-bit Mono PCM to WAV
                wav_io = io.BytesIO()
                with wave.open(wav_io, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(8000)
                    wav_file.writeframes(raw_audio)
                
                wav_data = wav_io.getvalue()

                prompt = [
                    (
                        "You are a friendly personal voice assistant with a Gujarati-Hindi tone. "
                        "Rule 1: Always start your response with 'हे भैला, बोलो ने! ' (or 'हे भैला, '). "
                        "Rule 2: Carefully listen to the question in the audio and give a clear, direct answer in 1 or 2 simple Hindi sentences. "
                        "Rule 3: If the user audio is silent, just hello, or unclear, say: 'हे भैला, बोलो ने! मैं सुन रहा हूँ, क्या काम है?'"
                    ),
                    {"mime_type": "audio/wav", "data": wav_data}
                ]
                response = model.generate_content(prompt)
                if response and response.text:
                    reply_text = response.text.strip()
                else:
                    reply_text = "हे भैला, बोलो ने! मैं सुन रहा हूँ, क्या काम है?"
        except Exception as e:
            print(f"Error: {e}")
            reply_text = "हे भैला, थोड़ा साफ़ आवाज़ में बोलो ने, आवाज़ कट गई थी।"

    print(f"AI Response: {reply_text}")

    try:
        tts = gTTS(reply_text, lang='hi')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return Response(content=mp3_fp.read(), media_type="audio/mpeg")
    except Exception as e:
        print(f"TTS Error: {e}")
        return Response(status_code=500, content="Audio conversion error")
