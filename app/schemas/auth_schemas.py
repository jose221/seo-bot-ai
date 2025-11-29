"""
Schemas de autenticación que replican exactamente los contratos
de la API externa de Herandro Services.
"""
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


# ============= LOGIN =============

class LoginRequest(BaseModel):
    """Request body para el endpoint de login"""
    model_config = ConfigDict(json_encoders={UUID: str})

    email: EmailStr
    password: str
    #project_id: Optional[UUID] = None
    token_name: Optional[str] = "SeoBotSession"
    expires_in_days: Optional[int] = 30


class LoginResponse(BaseModel):
    """Response del endpoint de login"""
    access_token: str
    token_type: str
    token_id: str
    user_id: str  # Se guardará como external_id en BD local
    user_email: str
    user_name: str
    tenant_id: Optional[str] = None  # Se guardará en BD local
    project_id: Optional[str] = None  # Se guardará en BD local
    expires_at: datetime
    scope: str


# ============= REGISTER =============

class RegisterRequest(BaseModel):
    """Request body para el endpoint de registro"""
    model_config = ConfigDict(json_encoders={UUID: str})

    city: str
    country_code: str
    email: EmailStr
    full_name: str
    password: str
    project_id: Optional[UUID] = None
    username: str


class RegisterResponse(BaseModel):
    """Response del endpoint de registro"""
    access_token: str
    token_type: str
    token_id: str
    user_id: str
    user_email: str
    user_name: str
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    expires_at: datetime
    scope: str


# ============= VERIFY TOKEN =============

class VerifyTokenResponse(BaseModel):
    """Response del endpoint de verificación de token"""
    access_token: str
    token_type: str
    token_id: str
    user_id: str
    user_email: str
    user_name: str
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    expires_at: datetime
    scope: str
