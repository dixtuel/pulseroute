from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    is_owner: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccountDeleteRequest(BaseModel):
    password: str = Field(description="Account password for confirmation")
    confirmation: str = Field(
        default="DELETE",
        description="Confirmation text (must be 'DELETE') to prevent accidental deletions",
    )


class AccountDeleteResponse(BaseModel):
    status: str = "success"
    detail: str = "Account and all associated personal data permanently deleted in accordance with KVKK / GDPR."

