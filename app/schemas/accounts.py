from datetime import datetime
from pydantic import BaseModel, field_validator, EmailStr, ConfigDict, Field
from pydantic_core import PydanticCustomError
from pydantic_core.core_schema import FieldValidationInfo

from app.utils.accounts import optimal_password
from app.utils.commons import strict_email


class UserBase(BaseModel):
    username: str
    email: EmailStr

    @field_validator('username')
    def validate_username_min_length(cls, v: str):
        if len(v) < 3:
            raise PydanticCustomError('value_error', '닉네임은 최소 3글자이상 이어야 합니다.')
        return v

    @field_validator('email', mode='before')
    def validate_email_strict(cls, v):
        email = strict_email(v)
        return email


class UserOrm(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserIn(UserBase):
    password: str
    confirmPassword: str

    @field_validator('username', 'password', 'confirmPassword', 'email')
    def not_empty(cls, v):
        if not v or not v.strip():
            # raise ValueError('빈 값은 허용되지 않습니다.')
            # 접두사 없이 메시지 그대로 내려감
            raise PydanticCustomError('empty_value', '빈 값은 허용되지 않습니다.')
        return v

    @field_validator("password")
    def password_validator(cls, password: str | None) -> str | None:
        if not password:
            return password
        optimal_password(password)
        return password

    @field_validator('confirmPassword')
    def passwords_match(cls, v, info: FieldValidationInfo):
        if 'password' in info.data and v != info.data['password']:
            # raise ValueError('비밀번호가 일치하지 않습니다')
            # 접두사 없이 메시지 그대로 내려감
            raise PydanticCustomError('empty_value', '비밀번호가 일치하지 않습니다.')
        return v


class UserOut(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: str | None = Field(None)
    email: EmailStr | None = None

    @field_validator('username')
    def validate_username_min_length(cls, v: str):
        if v is None:
            print("username is None")
            return None
        if isinstance(v, str) and v.strip() == '':
            return None
        if len(v) < 3:
            raise PydanticCustomError('value_error', '닉네임은 최소 3글자이상 이어야 합니다.')
        return v

    @field_validator('email', mode='before')
    def validate_email_none(cls, v):
        if v is None:
            print("email is None")
            return None
        if isinstance(v, str) and v.strip() == '':
            return None
        email = strict_email(v)
        return email

class UserResetPasswordIn(BaseModel):
    user_id: int
    password: str
    newpassword: str
    confirmPassword: str

    @field_validator('password', 'newpassword', 'confirmPassword')
    def not_empty(cls, v):
        if not v or not v.strip():
            # raise ValueError('빈 값은 허용되지 않습니다.')
            # 접두사 없이 메시지 그대로 내려감
            raise PydanticCustomError('empty_value', '빈 값은 허용되지 않습니다.')
        return v

    @field_validator("newpassword")
    def password_validator(cls, v: str | None) -> str | None:
        if not v:
            return v
        optimal_password(v)
        return v

    @field_validator('confirmPassword')
    def passwords_match(cls, v, info: FieldValidationInfo):
        if 'newpassword' in info.data and v != info.data['newpassword']:
            # raise ValueError('비밀번호가 일치하지 않습니다')
            # 접두사 없이 메시지 그대로 내려감
            raise PydanticCustomError('empty_value', '비밀번호가 일치하지 않습니다.')
        return v

class UserLostPasswordIn(BaseModel):
    email: EmailStr
    token: str
    newpassword: str
    confirmPassword: str

    @field_validator('email', mode='before')
    def validate_email_strict(cls, v):
        email = strict_email(v)
        return email

    @field_validator('token', 'newpassword', 'confirmPassword')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise PydanticCustomError('empty_value', '빈 값은 허용되지 않습니다.')
        return v

    @field_validator("newpassword")
    def password_validator(cls, v: str | None) -> str | None:
        if not v:
            return v
        optimal_password(v)
        return v

    @field_validator('confirmPassword')
    def passwords_match(cls, v, info: FieldValidationInfo):
        if 'newpassword' in info.data and v != info.data['newpassword']:
            # raise ValueError('비밀번호가 일치하지 않습니다')
            # 접두사 없이 메시지 그대로 내려감
            raise PydanticCustomError('empty_value', '비밀번호가 일치하지 않습니다.')
        return v


class UserPasswordUpdate(BaseModel):
    password: str | None = Field(None)

    @field_validator("password")
    def password_validator(cls, password: str | None) -> str | None:
        if not password:
            return password
        optimal_password(password)
        return password


class EmailRequest(BaseModel):
    email: EmailStr
    type:str

    @field_validator('email', mode='before')
    def validate_email_strict(cls, v):
        email = strict_email(v)
        return email


class VerifyRequest(BaseModel):
    type: str | None = None
    old_email: EmailStr | None = None
    email: EmailStr | None = None  # ← 이메일도 상황에 따라 비울 수 있게 None 허용
    authcode: str | None = None  # ← type에 따라 필수가 다르므로 None 허용
    password: str | None = None

    @field_validator('old_email', 'email', mode='before')
    def validate_email_strict(cls, v):
        """인증코드만 검증할 때는 old_email/email이 들어오지 않는다.
        이메일 변경할 때는 인증코드와 함께 old_email과 email이 들어온다.
        old_email과 email이 들어오지 않는 경우는 인증코드만 검증할 수 있도록 None을 반환"""
        if v is None or v == "":
            return None
        """# 그 외는 strict_email 통과"""
        email = strict_email(v)
        return email

