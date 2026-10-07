"""
Modelos de dados do sistema de currículos.
Separados da lógica de leitura para facilitar troca de fonte futura.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Componente:
    """
    Informações intrínsecas da disciplina/componente curricular.
    Atributos que NÃO dependem do curso (identificação e ementa).
    """
    codigo: str
    nome: str
    natureza: Optional[str] = None   # HUM, INT, TEC, CFU — só disponível no BICT


@dataclass
class EntradaMatriz:
    """
    Relação entre um componente e um curso específico.
    Todos os atributos aqui podem variar por curso.
    """
    curso: str
    codigo: str
    nome: str
    etapa: Optional[int]             # None = "Sem Etapa"
    carater: str                     # "Obrigatória" | "Eletiva"
    creditos: float
    carga_horaria: float
    che: float                       # Carga Horária de Extensão
    prereqs: list[str] = field(default_factory=list)   # lista de códigos
    natureza: Optional[str] = None
