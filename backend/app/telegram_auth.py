import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl, unquote

from fastapi import HTTPException, status


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict:
    """Validate Telegram WebApp initData per official spec."""
    if not init_data or not bot_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid init data")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid init data signature")

    auth_date = int(pairs.get("auth_date", "0"))
    if auth_date and time.time() - auth_date > max_age_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Init data expired")

    user_raw = pairs.get("user")
    if not user_raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User missing in init data")

    user = json.loads(unquote(user_raw) if "%" in user_raw else user_raw)
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    return {"telegram_user_id": int(user_id), "user": user}