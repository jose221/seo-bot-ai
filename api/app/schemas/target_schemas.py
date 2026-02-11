"""
Schemas para gestión de Targets (WebPages).
Define DTOs para crear y listar sitios web a auditar.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.models import AuditReport


class WebPageCreate(BaseModel):
  """Schema para crear un nuevo target"""
  url: str = Field(..., description="URL completa del sitio (incluir https://)")
  name: Optional[str] = Field(None, max_length=200, description="Nombre descriptivo")
  instructions: Optional[str] = Field(None, description="Instrucciones de navegación")
  tech_stack: Optional[str] = Field(None, max_length=500, description="Stack tecnológico")
  manual_html_content: Optional[str] = Field(None, description="Contenido HTML manual de la página")

  @validator('url')
  def validate_url(cls, v):
    """Validar que la URL sea válida y tenga protocolo"""
    if not v.startswith(('http://', 'https://')):
      raise ValueError('URL debe comenzar con http:// o https://')
    return v

  class Config:
    json_schema_extra = {
      "example": {
        "url": "https://example.com",
        "name": "Mi Sitio Principal",
        "instructions": "Esperar 2 segundos después de cargar",
        "tech_stack": "React + Next.js",
        "manual_html_content": "<html>...</html>"
      }
    }


class WebPageUpdate(BaseModel):
  """Schema para actualizar un target existente"""
  name: Optional[str] = Field(None, max_length=200)
  instructions: Optional[str] = None
  tech_stack: Optional[str] = Field(None, max_length=500)
  is_active: Optional[bool] = None
  manual_html_content: Optional[str] = None


class WebPageResponse(BaseModel):
  """Schema de respuesta para un target"""
  id: UUID
  user_id: UUID
  url: str
  name: Optional[str]
  instructions: Optional[str]
  tech_stack: Optional[str]
  manual_html_content: Optional[str]
  is_active: bool
  audit_reports: Optional[List[AuditReport]] = None

  class Config:
    from_attributes = True


class WebPageListItem(BaseModel):
  """Schema para items de lista de targets (sin contenido pesado)"""
  id: UUID
  user_id: UUID
  url: str
  name: Optional[str]
  instructions: Optional[str]
  tech_stack: Optional[str]
  is_active: bool
  audit_reports: Optional[List[AuditReport]] = None

  class Config:
    from_attributes = True


class WebPageListResponse(BaseModel):
  """Respuesta paginada de targets"""
  items: list[WebPageListItem]
  total: int
  page: int
  page_size: Optional[int] = None


class WebPageSearchItem(BaseModel):
  id: UUID
  url: str
  name: Optional[str]
  is_active: bool

class WebPageSearchResponse(BaseModel):
  items: List[WebPageSearchItem]
  total: int
  page: int
  page_size: Optional[int] = None
