from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import date, datetime

_STATUS_VALIDOS = {"PENDENTE", "APROVADO", "REJEITADO"}

class CatalogoBase(BaseModel):
    titulo: str = Field(..., min_length=2, max_length=255, description="O título identificador do arquivo ou dataset agronômico.")
    orgao_emissor: str = Field(..., min_length=2, max_length=100, description="Entidade por trás dos dados (Ex: MAPA, Embrapa, Jacto).")
    tipo_documento: str = Field(..., min_length=2, max_length=50, description="Designação original do formato inserido (Ex: PDF, API, Planilha Zarc).")
    categoria_agronomica: str = Field(..., min_length=2, max_length=100, description="Etiqueta Master de contexto (Ex: Climatologia, Defensivos, Insumos).")
    data_publicacao: Optional[date] = Field(None, description="A data em que a documentação oficial entrou em vigor.")
    url_ou_caminho_original: Optional[str] = Field(None, max_length=2048, description="Se for web externo ou caminho logico.")
    status_processamento: Optional[str] = Field("APROVADO", description="PENDENTE para análise LLM, APROVADO após curadoria.")
    caminho_temporario: Optional[str] = Field(None, description="Path do servidor de upload aguardando vetorização.")

    @field_validator("status_processamento")
    @classmethod
    def validar_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _STATUS_VALIDOS:
            raise ValueError(f"status_processamento deve ser um de: {_STATUS_VALIDOS}")
        return v

class CatalogoCreate(CatalogoBase):
    pass

class CatalogoUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=2, max_length=255)
    orgao_emissor: Optional[str] = Field(None, min_length=2, max_length=100)
    tipo_documento: Optional[str] = Field(None, min_length=2, max_length=50)
    categoria_agronomica: Optional[str] = Field(None, min_length=2, max_length=100)
    data_publicacao: Optional[date] = None
    url_ou_caminho_original: Optional[str] = Field(None, max_length=2048)
    status_processamento: Optional[str] = None
    caminho_temporario: Optional[str] = None

    @field_validator("status_processamento")
    @classmethod
    def validar_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _STATUS_VALIDOS:
            raise ValueError(f"status_processamento deve ser um de: {_STATUS_VALIDOS}")
        return v

class CatalogoResponse(CatalogoBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }
