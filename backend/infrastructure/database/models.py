from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from infrastructure.database.session import Base

class CatalogoFontes(Base):
    __tablename__ = "catalogo_fontes"

    id = Column(Integer, primary_key=True, index=True)

    titulo = Column(String(255), nullable=False, index=True)
    orgao_emissor = Column(String(100), nullable=False)  # Ex: Embrapa, MAPA, Jacto, Syngenta, etc

    status_processamento = Column(String(50), nullable=False, default="APROVADO", server_default="APROVADO")
    caminho_temporario = Column(Text, nullable=True)

    tipo_documento = Column(String(50), nullable=False)  # Ex: PDF, SHP, CSV, API_Zarc
    categoria_agronomica = Column(String(100), nullable=False, index=True)  # Ex: Solos, Defensivos, Sementes, Clima
    data_publicacao = Column(Date, nullable=True)
    url_ou_caminho_original = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    csv_dados = relationship("CsvDados", back_populates="catalogo", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CatalogoFontes(id={self.id}, titulo='{self.titulo}')>"


class CsvDados(Base):
    """
    Armazena cada linha de um CSV ingerido como registro estruturado.
    A coluna `dados` persiste o payload dinâmico em JSON, evitando schema fixo
    para tabelas com estruturas variáveis (Zarc, defensivos, etc.).
    """
    __tablename__ = "csv_dados"

    id = Column(Integer, primary_key=True, index=True)
    id_fonte = Column(Integer, ForeignKey("catalogo_fontes.id", ondelete="CASCADE"), nullable=False, index=True)
    numero_linha = Column(Integer, nullable=False)
    dados = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    catalogo = relationship("CatalogoFontes", back_populates="csv_dados")

    def __repr__(self):
        return f"<CsvDados(id={self.id}, id_fonte={self.id_fonte}, linha={self.numero_linha})>"
