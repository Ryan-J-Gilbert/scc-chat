import jwt
from datetime import datetime, timedelta

SECRET_KEY = "super-secret-key"
print("MAKE SURE TO CHANGE JWT SECRET KEY!!!")
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60


def create_token(chat_id: str, username: str) -> str:
    payload = {
        "chat_id": chat_id,
        # "exp": datetime.utcnow() ,#+ timedelta(minutes=EXPIRATION_MINUTES),
        "username": username,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
