import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
    }

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ 텔레그램 메시지 전송 실패: {e}")


def send_photo(photo_path: str, caption: str = None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

    try:
        with open(photo_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TELEGRAM_CHAT_ID}
            if caption:
                data["caption"] = caption

            requests.post(url, files=files, data=data, timeout=10)
    except Exception as e:
        print(f"❌ 텔레그램 사진 전송 실패: {e}")
