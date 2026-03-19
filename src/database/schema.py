from pydantic import BaseModel, Field, EmailStr
from typing import Annotated, List, Dict, Any, Optional


class UserBase(BaseModel):
    name: Annotated[str, Field(..., description="Name of the User")]
    email: Annotated[EmailStr, Field(..., description="Email of the User")]
    preferences: Annotated[
        List[Dict[str, Any]], Field(default_factory=list, description="User Preferences")
    ]


class UserCreate(UserBase):
    pass


class UserGet(UserBase):
    id: int

    class Config:
        from_attributes = True  


class UpdatePreferences(BaseModel):
    email: EmailStr = Field(..., description="Email of the user to update")
    preferences: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Updated preferences list"
    )


class UserLookup(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the user")
    email: Optional[EmailStr] = Field(default=None, description="Email of the user")