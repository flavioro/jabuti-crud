from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255, examples=["Flavio Rodrigues"])
    email: EmailStr = Field(..., examples=["flavio@example.com"])
    idade: int = Field(..., ge=0, le=130, examples=[30])


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr | None = None
    idade: int | None = Field(default=None, ge=0, le=130)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    limit: int
    offset: int


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database: str
    cache: str
