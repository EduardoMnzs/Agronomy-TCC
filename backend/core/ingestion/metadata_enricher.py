"""
MetadataEnricher: enriquece os metadados de cada chunk após o split,
adicionando campos semânticos (tema, bioma, secao) sem custo de LLM —
usando regras determinísticas baseadas em palavras-chave do domínio agronômico.

Campos adicionados a cada Document.metadata:
  - tema    : categoria semântica principal do chunk
  - bioma   : bioma detectado no texto (Cerrado, Amazônia…)
  - secao   : título da seção inferido pelo padrão de heading (opcional)

O campo is_table (bool) já é atribuído pelo PDFProcessor e propagado aqui.

Notas de implementação:
  - Word boundaries via (?<!\w) / (?!\w) no lugar de \b para suporte pleno
    a caracteres acentuados (ex: "calcário", "Mato Grosso").
  - Regex pré-compilada no escopo global — compilada uma vez na inicialização
    do módulo, não a cada chamada de função.
  - Busca case-insensitive com re.IGNORECASE | re.UNICODE.
"""

import re
import logging
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


# Helpers de compilação
def _word_pattern(kw: str) -> str:
    """
    Envolve uma palavra-chave com lookahead/lookbehind Unicode para word boundary.

    Usa (?<!\w) e (?!\w) em vez de \b porque \b no Python usa apenas [A-Za-z0-9_]
    para definir 'caractere de palavra', tratando letras acentuadas (á, ç, ã…)
    como não-palavras e produzindo falsos positivos em frases como
    'Mato Grosso do Sul' vs 'Mato Grosso' ou 'ph' vs 'glyphosate'.
    """
    escaped = re.escape(kw)
    return rf"(?<!\w){escaped}(?!\w)"


def _compile_rules(
    rules: list[tuple[str, list[str]]]
) -> list[tuple[str, re.Pattern | None]]:
    """
    Compila cada lista de palavras-chave numa única regex alternada.
    Keywords são ordenadas por comprimento decrescente para que termos mais
    específicos (ex: 'adubação foliar') sejam tentados antes dos mais curtos
    ('adubação'), evitando matches prematuros dentro de alternativas.
    Retorna None para o tema fallback (sem keywords).
    """
    compiled = []
    for tema, keywords in rules:
        if not keywords:
            compiled.append((tema, None))
        else:
            sorted_kws = sorted(keywords, key=len, reverse=True)
            pattern = "|".join(_word_pattern(kw) for kw in sorted_kws)
            compiled.append((tema, re.compile(pattern, re.IGNORECASE | re.UNICODE)))
    return compiled


def _compile_biomas(
    biomas: dict[str, list[str]]
) -> list[tuple[str, re.Pattern]]:
    """
    Compila o dicionário de biomas preservando a ordem de inserção.
    Keywords são ordenadas por comprimento decrescente dentro de cada bioma
    para que 'mato grosso do sul' seja tentado antes de 'mato grosso'.
    A ordem dos biomas no dict determina prioridade entre biomas — biomas com
    termos mais específicos devem vir antes (ex: Pantanal antes de Cerrado).
    """
    compiled = []
    for bioma, keywords in biomas.items():
        sorted_kws = sorted(keywords, key=len, reverse=True)
        pattern = "|".join(_word_pattern(kw) for kw in sorted_kws)
        compiled.append((bioma, re.compile(pattern, re.IGNORECASE | re.UNICODE)))
    return compiled


# Definição das regras
_TEMA_RULES_RAW: list[tuple[str, list[str]]] = [
    ("Análise de Solo", 
        [
            "ph", "acidez", "calagem", "calcário", "saturação de bases", "ctc", "argila",
            "matéria orgânica", "fertilidade", "laudo", "textura do solo",
            "mehlich", "resina", "extrator", "análise de solo", "amostra de solo",
            "interpretação de resultados", "saturação por bases", "saturação por al",
        ]
    ),
    ("Nutrição e Adubação", 
        [
            "nitrogênio", "fósforo", "potássio", "micronutriente", "adubação", "fertilizante",
            "ureia", "npk", "sulfato", "boro", "zinco", "manganês", "adubação foliar",
            "recomendação de adubação", "dose de fertilizante",
        ]
    ),
    ("Defensivos Agrícolas", 
        [
            "herbicida", "fungicida", "inseticida", "agrotóxico", "defensivo", "nematicida",
            "acaricida", "bula", "dose", "carência", "resistência",
        ]
    ),
    ("Sementes e Genética", 
        [
            "cultivar", "semente", "germoplasma", "híbrido", "variedade", "melhoramento",
            "biotecnologia", "ogm", "transgênico",
        ]
    ),
    ("Irrigação e Clima", 
        [
            "irrigação", "precipitação", "evapotranspiração", "déficit hídrico", "chuva",
            "temperatura", "umidade", "clima", "zarc",
        ]
    ),
    ("Maquinário Agrícola", 
        [
            "pulverizador", "colheitadeira", "trator", "plantadeira", "semeadora",
            "pulverização", "calibração", "bico", "vazão", "jacto",
        ]
    ),
    ("Pragas e Doenças", 
        [
            "praga", "doença", "fungo", "bactéria", "vírus", "nematóide", "percevejo",
            "lagarta", "ferrugem", "mancha", "tombamento",
        ]
    ),
    ("Legislação e Certificação", 
        [
            "instrução normativa", "resolução", "portaria", "decreto", "mapa", "anvisa",
            "ibama", "registro", "certificação", "rastreabilidade",
        ]
    ),
    ("Geral", []), # fallback
]

_BIOMA_KEYWORDS_RAW: dict[str, list[str]] = {
    # Ordem de prioridade: Termos mais específicos/longos devem vir em biomas anteriores.
    "Pantanal":       ["pantanal", "mato grosso do sul"],
    "Cerrado":        ["cerrado", "savana", "chapada", "soja cerrado", "mato grosso", "goiás"],
    "Amazônia":       ["amazônia", "floresta amazônica", "pará", "amazonas", "acre", "rondônia"],
    "Caatinga":       ["caatinga", "semiárido", "nordeste", "seca"],
    "Mata Atlântica": ["mata atlântica", "litoral", "são paulo", "paraná", "santa catarina"],
    "Pampa":          ["pampa", "rio grande do sul", "campo nativo", "pecuária gaúcha"],
}

# Pré-compilação
_TEMA_COMPILED:  list[tuple[str, re.Pattern | None]] = _compile_rules(_TEMA_RULES_RAW)
_BIOMA_COMPILED: list[tuple[str, re.Pattern ]]        = _compile_biomas(_BIOMA_KEYWORDS_RAW)

# Padrão para detectar headings/seções (ex: "1. Introdução", "2. Metodologia", etc.)
_HEADING_RE = re.compile(
    r"^(?:\d+[\.\)]\s+)?([A-ZÁÉÍÓÚÃÕÂÊÎÔÛÀÈÌÒÙÇ][A-ZÁÉÍÓÚÃÕÂÊÎÔÛÀÈÌÒÙÇ\s]{3,60})$",
    re.MULTILINE | re.UNICODE,
)

# Funções internas
def _detect_tema(text: str) -> str:
    for tema, pattern in _TEMA_COMPILED:
        if pattern is None:
            return tema
        if pattern.search(text):
            logger.debug(f"Tema detectado: '{tema}'")
            return tema
    return "Geral"


def _detect_bioma(text: str) -> str:
    for bioma, pattern in _BIOMA_COMPILED:
        if pattern.search(text):
            logger.debug(f"Bioma detectado: '{bioma}'")
            return bioma
    return "Não identificado"


def _detect_secao(text: str) -> str:
    match = _HEADING_RE.search(text)
    if match:
        return match.group(1).strip().title()
    return ""


def enrich_chunks(chunks: list[Document]) -> list[Document]:
    """
    Recebe a lista de chunks (pós-split) e adiciona campos semânticos.
    O campo is_table já vem do PDFProcessor e é preservado intacto.
    """
    for chunk in chunks:
        text = chunk.page_content
        chunk.metadata["tema"] = _detect_tema(text)
        chunk.metadata["bioma"] = _detect_bioma(text)

        secao = _detect_secao(text)
        if secao:
            chunk.metadata["secao"] = secao

    _propagate_tema_to_tables(chunks)

    logger.debug(f"MetadataEnricher: {len(chunks)} chunks enriquecidos.")
    return chunks


def _propagate_tema_to_tables(chunks: list[Document]) -> None:
    """
    Tabelas frequentemente contêm apenas dados numéricos sem palavras-chave
    de tema. Propaga o tema do chunk de texto anterior (mesma página) para
    tabelas classificadas como 'Geral'.

    Seguro contra ausência de metadado 'page' (retorna None → chave None
    no dict, sem KeyError).
    """
    last_tema_by_page: dict[int | None, str] = {}

    for chunk in chunks:
        page = chunk.metadata.get("page")
        is_table = chunk.metadata.get("is_table", False)

        if not is_table:
            tema = chunk.metadata.get("tema", "Geral")
            if tema != "Geral":
                last_tema_by_page[page] = tema
        else:
            if chunk.metadata.get("tema") == "Geral" and page in last_tema_by_page:
                chunk.metadata["tema"] = last_tema_by_page[page]
                logger.debug(
                    f"Tabela página {page}: tema herdado → '{chunk.metadata['tema']}'"
                )
