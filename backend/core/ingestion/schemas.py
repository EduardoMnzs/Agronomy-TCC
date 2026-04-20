"""
Pydantic schemas para validação estrutural da extração de laudos agronômicos.

O ExtractionResult é o contrato entre o LLM Validator e o orquestrador.
Se o LLM consegue preenchê-lo com qualidade 'boa', a extração local é suficiente.
Se retorna 'falha', as tabelas estão truncadas/ilegíveis e o fallback é ativado.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ExtractionQuality(str, Enum):
    BOA = "boa"
    PARCIAL = "parcial"
    FALHA = "falha"


class NutrientEntry(BaseModel):
    nutriente: str
    valor: Optional[str] = None
    unidade: Optional[str] = None
    interpretacao: Optional[str] = None


class TabelaAgronomica(BaseModel):
    titulo: Optional[str] = None
    linhas: list[NutrientEntry] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """
    Resultado da tentativa do LLM de mapear o texto bruto para a estrutura
    de um laudo agronômico. Usado exclusivamente como sinal de qualidade —
    não é persistido no Qdrant.
    """
    qualidade: ExtractionQuality
    texto_principal: str = ""
    tabelas: list[TabelaAgronomica] = Field(default_factory=list)
    motivo_falha: Optional[str] = None
