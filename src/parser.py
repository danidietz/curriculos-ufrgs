"""
Parser do campo 'Atividade de Ensino/Pré-Requisito'.

O sistema UFRGS exporta nome e pré-requisitos na mesma célula:
  'CÁLCULO II  - DIL01111 - ÁLGEBRA LINEAR  - e DIL01113 - CÁLCULO I  - e DIL01114 - FÍSICA I'

Padrão identificado:
  NOME_DISCIPLINA  - COD_PREREQ - NOME_PREREQ  - e COD_PREREQ - NOME_PREREQ ...

Estratégia: encontrar o primeiro código (regex DIL/DIR/VAE + dígitos)
e tudo antes dele é o nome; extrair todos os códigos como pré-requisitos.
"""
import re
from typing import Tuple

# Padrão de código: letras maiúsculas seguidas de dígitos (DIL01113, DIR04016, VAERE201...)
CODIGO_RE = re.compile(r'\b([A-Z]{2,}[0-9]{2,})\b')


def parse_campo_atividade(campo: str) -> Tuple[str, list[str]]:
    """
    Recebe o conteúdo bruto do campo 'Atividade de Ensino/Pré-Requisito'.
    Retorna (nome_limpo, lista_de_codigos_prereq).

    Exemplos:
      'MODELOS MATEMÁTICOS ELEMENTARES'
        → ('MODELOS MATEMÁTICOS ELEMENTARES', [])

      'CÁLCULO I  - DIL01101 - MODELOS MATEMÁTICOS ELEMENTARES'
        → ('CÁLCULO I', ['DIL01101'])

      'CÁLCULO II  - DIL01111 - ÁLGEBRA  - e DIL01113 - CÁLCULO I  - e DIL01114 - FÍSICA I'
        → ('CÁLCULO II', ['DIL01111', 'DIL01113', 'DIL01114'])
    """
    if not campo or not isinstance(campo, str):
        return ("", [])

    campo = campo.strip()
    codigos = CODIGO_RE.findall(campo)

    if not codigos:
        # Sem pré-requisitos — o campo inteiro é o nome
        return (campo.strip(), [])

    # O nome é tudo antes do primeiro código
    primeiro_codigo = codigos[0]
    idx = campo.find(primeiro_codigo)

    # Remove o separador ' - ' antes do código
    nome_bruto = campo[:idx]
    nome = re.sub(r'\s*-\s*$', '', nome_bruto).strip()

    # Pré-requisitos: todos os códigos encontrados
    prereqs = codigos

    return (nome, prereqs)


def normalizar_carater(valor: str) -> str:
    """Normaliza variações de grafia do caráter."""
    if not valor:
        return "Desconhecido"
    v = str(valor).strip()
    if "letiva" in v:   # Eletiva
        return "Eletiva"
    if "brigatória" in v or "brigatorio" in v.lower():
        return "Obrigatória"
    return v


def normalizar_etapa(valor) -> int | None:
    """Converte valor de etapa para int, retorna None para 'Sem Etapa'."""
    if valor is None or (isinstance(valor, str) and "sem" in valor.lower()):
        return None
    try:
        return int(float(str(valor)))
    except (ValueError, TypeError):
        return None
