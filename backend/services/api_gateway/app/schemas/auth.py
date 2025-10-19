from pydantic import BaseModel, EmailStr


class UserLoginRequest(BaseModel):
    username: str  # Email address (using str to avoid validation issues)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: str
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    role: str | None = None
    default_location: str | None = None
    location: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    user: UserProfile | None = None


class DeviceTokenRequest(BaseModel):
    device_id: str
    device_secret: str
