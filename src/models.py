from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Componente:
    """Disciplina/componente curricular universal — atributos que não mudam entre cursos."""
    codigo: str
    nome: str
    natureza: Optional[str] = None  # HUM / INT / TEC / CFU — só no BICT


@dataclass
class EntradaMatriz:
    """Uma disciplina dentro de uma matriz curricular específica."""
    curso: str
    codigo: str
    nome: str
    etapa: Optional[int]        # None = "Sem Etapa"
    carater: str                # "Obrigatória" | "Eletiva"
    creditos: float
    carga_horaria: float
    che: float
    prereqs: list = field(default_factory=list)   # lista de códigos
    natureza: Optional[str] = None
    eixo: Optional[str] = None  # para BICT: eixo temático
