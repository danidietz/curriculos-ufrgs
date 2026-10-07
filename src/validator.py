"""
validator.py — Valida a integridade dos dados após o carregamento.

Detecta problemas antes de tentar renderizar visualizações.
"""
import pandas as pd
from dataclasses import dataclass


@dataclass
class Problema:
    nivel: str        # "erro" | "aviso"
    curso: str
    codigo: str
    mensagem: str


def validar(df: pd.DataFrame) -> list[Problema]:
    """
    Recebe o DataFrame consolidado de todas as entradas e retorna
    lista de problemas encontrados.
    """
    problemas: list[Problema] = []

    # Todos os códigos válidos conhecidos
    codigos_validos = set(df["codigo"].dropna().unique())

    for _, row in df.iterrows():
        curso = row["curso"]
        codigo = row["codigo"]
        nome = row["nome"]

        # 1. Componente sem código real
        if str(codigo).startswith("SEM_CODIGO_"):
            problemas.append(Problema(
                nivel="aviso", curso=curso, codigo=codigo,
                mensagem=f"Componente '{nome}' não possui código no sistema."
            ))

        # 2. Etapa inválida (não inteiro positivo e não None)
        etapa = row.get("etapa")
        if etapa is not None and (not isinstance(etapa, (int, float)) or etapa < 1):
            problemas.append(Problema(
                nivel="erro", curso=curso, codigo=codigo,
                mensagem=f"Etapa inválida: '{etapa}'"
            ))

        # 3. Pré-requisitos que não existem na base do curso
        prereqs = row.get("prereqs", [])
        if isinstance(prereqs, list):
            for pre in prereqs:
                if pre not in codigos_validos:
                    problemas.append(Problema(
                        nivel="aviso", curso=curso, codigo=codigo,
                        mensagem=f"Pré-requisito '{pre}' não encontrado na base de dados."
                    ))

        # 4. Carga horária zerada para componente não-vínculo
        ch = row.get("carga_horaria", 0)
        if ch == 0 and not str(codigo).startswith("VAE"):
            problemas.append(Problema(
                nivel="aviso", curso=curso, codigo=codigo,
                mensagem=f"Carga horária zero para '{nome}'."
            ))

    # 5. Duplicatas (mesmo código e curso)
    dupl = df[df.duplicated(subset=["curso", "codigo"], keep=False)]
    for _, row in dupl.iterrows():
        problemas.append(Problema(
            nivel="erro", curso=row["curso"], codigo=row["codigo"],
            mensagem="Código duplicado no mesmo curso."
        ))

    return problemas


def resumo_validacao(problemas: list[Problema]) -> dict:
    erros = [p for p in problemas if p.nivel == "erro"]
    avisos = [p for p in problemas if p.nivel == "aviso"]
    return {
        "total": len(problemas),
        "erros": len(erros),
        "avisos": len(avisos),
        "lista": problemas,
    }
