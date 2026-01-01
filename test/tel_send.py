# tel_send.py
import requests
from config import telegram_token, telegram_chat_id, is_paper_trading


def _mode_prefix() -> str:
    """
    모의 / 실전 모드 구분 접두어
    """
    return "🧪 [모의]\n" if is_paper_trading else "🔴 [실전]\n"


def send_message(text: str):
    """
    텔레그램 텍스트 메시지 전송
    """
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

    payload = {
        "chat_id": telegram_chat_id,
        "text": _mode_prefix() + text,
    }

    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print("❌ 텔레그램 메시지 전송 실패:", e)


def send_photo(photo_path: str, caption: str | None = None):
    """
    텔레그램 사진 전송
    """
    url = f"https://api.telegram.org/bot{telegram_token}/sendPhoto"

    if caption:
        caption = _mode_prefix() + caption

    try:
        with open(photo_path, "rb") as f:
            files = {"photo": f}
            data = {
                "chat_id": telegram_chat_id,
                "caption": caption,
            }

            requests.post(url, data=data, files=files, timeout=10)

    except Exception as e:
        print("❌ 텔레그램 사진 전송 실패:", e)
