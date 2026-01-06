import requests

try:
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
except ImportError:
    # config 모듈이 설정되지 않은 경우
    TELEGRAM_BOT_TOKEN = None
    TELEGRAM_CHAT_ID = None


def send_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"⚠️  텔레그램 설정이 없습니다. 메시지 전송 건너뜀: {text[:50]}...")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        print(f"✅ 텔레그램 메시지 전송 성공")
    except Exception as e:
        print(f"❌ 텔레그램 메시지 전송 실패: {e}")
        print(f"   URL: {url}")
        print(f"   Chat ID: {TELEGRAM_CHAT_ID}")


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
