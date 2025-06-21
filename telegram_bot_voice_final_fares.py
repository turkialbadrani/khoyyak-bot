from dotenv import load_dotenv

load_dotenv()

import os
import telebot
from openai import OpenAI
from pydub import AudioSegment
from datetime import datetime
import requests

# 🔐 مفاتيح API
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # صوت: فارس

client = OpenAI(api_key=OPENAI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


# 🎙️ تحويل النص إلى صوت باستخدام ElevenLabs
def speak_to_voice(text, filename="response.ogg"):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.85,
                "style": 0.8,
                "use_speaker_boost": True
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
        else:
            print(
                f"❌ ElevenLabs Error: {response.status_code} - {response.text}"
            )
    except Exception as e:
        print(f"⚠️ تعذر توليد الصوت: {e}")


# 🧠 توليد رد GPT
def get_khoyyak_reply(user_input):
    persona = '''
    أنت خويّ تركي، خويّ ذيب، يعرفه الكل بلقبه: الصيلد.
    رجل راقٍ، صريح، أسلوبه نجدّي واضح، يحب الطقطقة المحترمة.
    يعرف عياله: عزام، روين، فارس، لارين.
    ويعرف ربعه: عابد (أبو محمد)، ماجد (أبو محمد)، حسين (أبو ريان)، عبدالرحمن (أبو مازن)، عادل (أبو فيصل)، عبدالله (أبو إبراهيم)، نايف (أبو شهد)، محمد (أبو بدر)، فاضل (العامل).
    يرد على خويه بأسلوب رجال ناضج فيه هيبة ووناسة.
    '''
    try:
        response = client.chat.completions.create(model="gpt-4o",
                                                  messages=[{
                                                      "role": "system",
                                                      "content": persona
                                                  }, {
                                                      "role":
                                                      "user",
                                                      "content":
                                                      user_input
                                                  }])
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ خطأ في توليد الرد: {e}")
        return "ما قدرت أرد الحين، جرّب بعد شوي يا خوي."


# 💬 الرد على الرسائل النصية
@bot.message_handler(content_types=["text"])
def handle_text(message):
    user_input = message.text
    reply_text = get_khoyyak_reply(user_input)
    bot.send_message(message.chat.id, reply_text)

    speak_to_voice(reply_text)
    try:
        with open("response.ogg", "rb") as voice:
            bot.send_voice(message.chat.id, voice)
    except Exception as e:
        print(f"❌ فشل إرسال الصوت: {e}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("sessions", exist_ok=True)
    with open(f"sessions/session_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write(f"👤 خويّك قال:\n{reply_text}\n")


# 🎧 الرد على التسجيلات الصوتية
@bot.message_handler(content_types=["voice"])
def handle_voice(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open("input.ogg", "wb") as f:
            f.write(downloaded_file)

        with open("input.ogg", "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1",
                                                            file=audio_file)

        user_input = transcript.text
        bot.send_message(message.chat.id, f"📝 قلت: {user_input}")

        reply_text = get_khoyyak_reply(user_input)
        bot.send_message(message.chat.id, reply_text)

        speak_to_voice(reply_text)
        with open("response.ogg", "rb") as voice:
            bot.send_voice(message.chat.id, voice)

    except Exception as e:
        print(f"❌ فشل الرد على الصوت: {e}")
        bot.send_message(message.chat.id,
                         "❌ ما قدرت أسمع صوتك، جرّب ترسله من جديد.")


# 🚀 تشغيل البوت
print("✅ خويّك جاهز بصوت واقعي من ElevenLabs.")
bot.polling()
