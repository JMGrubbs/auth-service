from pydantic import BaseModel, EmailStr, Field


class AuthorizationContext(BaseModel):
    client_id: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    redirect_uri: str = Field(min_length=10, max_length=2048)
    state: str = Field(min_length=8, max_length=512)
    code_challenge: str = Field(min_length=43, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    code_challenge_method: str = Field(pattern=r"^S256$")


class AuthorizationRequest(AuthorizationContext):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class AuthorizationResponse(BaseModel):
    redirect_url: str


class TokenRequest(BaseModel):
    grant_type: str = Field(default="authorization_code", pattern=r"^authorization_code$")
    code: str = Field(min_length=32, max_length=256)
    client_id: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    redirect_uri: str = Field(min_length=10, max_length=2048)
    code_verifier: str = Field(min_length=43, max_length=128, pattern=r"^[A-Za-z0-9._~-]+$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ClientResponse(BaseModel):
    client_id: str
    name: str
