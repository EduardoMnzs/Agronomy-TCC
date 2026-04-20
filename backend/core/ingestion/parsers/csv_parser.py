import logging
from typing import Any, Dict
import pandas as pd
from core.ingestion.parsers.base import BaseParser
from infrastructure.database.models import CsvDados
from infrastructure.database.sync_session import get_sync_session

logger = logging.getLogger(__name__)

MAX_ROWS = 500_000
BATCH_SIZE = 1_000

class CSVParser(BaseParser):
    """
    Trilha de processamento para dados Tabulares (ex: Zarc, Tabelas de Defensivos).
    Persiste cada linha do CSV como registro JSON na tabela `csv_dados`,
    vinculado ao `id_fonte` do CatalogoFontes para rastreabilidade completa.
    """

    def process(self) -> Dict[str, Any]:
        id_fonte = self.metadata["id_fonte"]

        try:
            df = pd.read_csv(
                self.file_path,
                dtype=str,
                sep=None,
                engine="python",
                on_bad_lines="warn",
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo CSV não encontrado: {self.file_path}")
        except Exception as e:
            raise ValueError(f"Falha ao ler arquivo CSV '{self.file_path}': {e}") from e

        num_linhas = len(df)
        if num_linhas == 0:
            raise ValueError("Arquivo CSV está vazio.")
        if num_linhas > MAX_ROWS:
            raise ValueError(f"Arquivo CSV excede o limite de {MAX_ROWS} linhas ({num_linhas} encontradas).")

        df = df.where(pd.notna(df), other=None)

        registros_inseridos = 0

        with get_sync_session() as db:
            batch = []
            for idx, row in enumerate(df.to_dict(orient="records"), start=1):
                batch.append(CsvDados(
                    id_fonte=id_fonte,
                    numero_linha=idx,
                    dados=row,
                ))
                if len(batch) >= BATCH_SIZE:
                    db.bulk_save_objects(batch)
                    db.flush()
                    registros_inseridos += len(batch)
                    batch = []
                    logger.debug(f"CSV id_fonte={id_fonte}: {registros_inseridos}/{num_linhas} linhas persistidas")

            if batch:
                db.bulk_save_objects(batch)
                registros_inseridos += len(batch)

        logger.info(f"CSV id_fonte={id_fonte}: {registros_inseridos} linhas inseridas em csv_dados")

        return {
            "status": "sucesso",
            "tipo_parser": "CSVParser",
            "linhas_inseridas": registros_inseridos,
            "colunas": list(df.columns),
            "banco_alvo": "PostgreSQL (csv_dados)",
        }
