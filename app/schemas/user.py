from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=125)
    full_name: str = Field(min_length=1, max_length=100)

class UserUpdate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)


class UserPatch(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_changes(self):
        changes = self.model_dump(exclude_unset=True)
        if not changes or any(value is None for value in changes.values()):
            raise ValueError("Provide at least one non-null field to update")
        return self

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


