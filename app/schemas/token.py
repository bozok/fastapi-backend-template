from sqlmodel import SQLModel


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    email: str | None = None  # Corresponds to 'sub' claim in JWT
