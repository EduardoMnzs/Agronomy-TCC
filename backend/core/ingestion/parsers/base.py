from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseParser(ABC):
    """
    Contrato base estrito para ingestão de dados.
    Nenhuma fonte pode ser carregada sem validação de seus metadados.
    """
    
    def __init__(self, file_path: str, metadata: Dict[str, Any]):
        self.file_path = file_path
        self.metadata = metadata
        self._validate_contract()

    def _validate_contract(self):
        """
        Garante que a rastreabilidade está presente no pacote de dados.
        """
        if "id_fonte" not in self.metadata:
            raise ValueError(
                "Falha na Barreira de Ingestão: "
                "Todo arquivo processado deve conter o ID do CatalogoFontes ('id_fonte')."
            )

    @abstractmethod
    def process(self) -> dict:
        """
        Método a ser implementado por cada tipo de arquivo (PDF, CSV, SHP).
        Deve extrair e persistir os dados em seu banco especialista e retornar um resumo.
        """
        pass
