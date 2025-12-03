from pydantic import BaseModel, EmailStr, field_validator
from pydantic_core import PydanticCustomError

from app.utils.commons import strict_email


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator('email', mode='before')
    def validate_email_strict(cls, v):
        email = strict_email(v)
        return email

    @field_validator('password')
    def not_empty(cls, v):
        print(f"Login Request: ", v)
        if not v or not v.strip():
            # raise ValueError('빈 값은 허용되지 않습니다.')
            # 접두사 없이 메시지 그대로 내려감
            raise PydanticCustomError('empty_value', '빈 값은 허용되지 않습니다.')
        return v