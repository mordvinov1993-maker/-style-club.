from pathlib import Path
from fastapi.responses import FileResponse
import os

from fastapi import FastAPI
from dotenv import load_dotenv
from database import create_database, spin_wheel
from pydantic import BaseModel

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = FastAPI()
create_database()
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import HTTPException


def check_telegram_data(init_data):
    data = dict(parse_qsl(init_data))

    received_hash = data.pop("hash", None)

    if not received_hash:
        return None

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return None

    auth_date = int(data.get("auth_date", 0))

    if time.time() - auth_date > 86400:
        return None

    return json.loads(data["user"])

@app.get("/")
async def home():
    return FileResponse(
        Path(__file__).parent / "wheel_game" / "index.html"
    )
class SpinRequest(BaseModel):
    init_data: str


@app.post("/spin")
async def spin(request: SpinRequest):
    telegram_user = check_telegram_data(request.init_data)

    if not telegram_user:
        raise HTTPException(
            status_code=401,
            detail="Ошибка проверки Telegram"
        )

    telegram_id = telegram_user["id"]

    status, prize = spin_wheel(telegram_id)

    if status == "already_spun":
        return {
            "status": "already_spun",
            "message": "Сегодня ты уже крутил колесо!"
        }

    if status == "no_user":
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    return {
        "status": "success",
        "prize": prize
    }

