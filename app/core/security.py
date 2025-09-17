import string
import random
from fastapi import HTTPException, Request, status
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_random_password(length: int) -> str:
    all_chars = string.ascii_letters + string.digits
    return "".join(random.choice(all_chars) for i in range(length))


def ip_filter(allowed_ips: list):
    def dependency(request: Request):
        client_ip = request.client.host
        print(client_ip)
        if client_ip not in allowed_ips:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="IP address not allowed"
            )
        return client_ip

    return dependency
