from pydantic import BaseModel

class RegisterIn(BaseModel):
    username: str
    password: str
    role: str = "user"

class LoginIn(BaseModel):
    username: str
    password: str

class TargetIn(BaseModel):
    name: str
    base_url: str
