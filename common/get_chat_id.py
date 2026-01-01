import requests
import json
from config import telegram_token

url = f"https://api.telegram.org/bot{telegram_token}/getUpdates"
print(json.dumps(requests.get(url).json(), indent=4, ensure_ascii=False))