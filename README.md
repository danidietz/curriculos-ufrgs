# Currículos UFRGS — Sistema de Visualização Curricular

Sistema interativo para análise e visualização de matrizes curriculares.

## Instalação

```bash
# 1. Clone ou baixe o projeto
cd curriculos

# 2. Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt
```

## Execução

```bash
streamlit run app.py
```

O sistema abrirá automaticamente em `http://localhost:8501`.

## Atualizar os dados

1. Exporte a nova planilha do sistema UFRGS no mesmo formato
2. No menu lateral do app, clique em **"Substituir planilha de dados"**
3. Faça upload do novo arquivo `.xlsx`
4. O sistema recarrega automaticamente

Alternativamente, substitua o arquivo em `data/Curriculo_sistema_2026-2.xlsx`.

## Adicionar um novo curso

Basta adicionar uma **nova aba** na planilha Excel com a mesma estrutura das abas existentes:
- Linha de título de etapa: `Etapa 1`, `Etapa 2`, ...
- Linha de cabeçalho: `Código | Atividade de Ensino/Pré-Requisito | Caráter | Créditos | Carga Horária | CHE`
- Linhas de dados

O sistema detecta automaticamente qualquer nova aba como novo curso.
**Não é necessário modificar nenhum arquivo Python.**

## Estrutura do projeto

```
curriculos/
├── app.py                    # Interface Streamlit (ponto de entrada)
├── data/
│   └── Curriculo_sistema_2026-2.xlsx
├── src/
│   ├── models.py             # Dataclasses: Componente, EntradaMatriz
│   ├── loader.py             # Leitura do Excel (isolado para troca futura)
│   ├── processor.py          # Parsing e normalização dos dados
│   ├── validator.py          # Validação de integridade
│   └── views/
│       ├── matriz.py         # Grade curricular por etapas
│       ├── grafo.py          # Grafo de pré-requisitos (Plotly)
│       ├── distribuicao.py   # Gráficos CH e créditos
│       └── comparacao.py     # Comparação entre cursos
├── requirements.txt
└── README.md
```

## Conectar ao Google Sheets (futuro)

Em `src/loader.py`, a função `load_google_sheets()` está reservada.
Para ativar:
1. `pip install gspread google-auth`
2. Configure credenciais de serviço do Google Cloud
3. Substitua `load_excel()` por `load_google_sheets()` em `app.py`
A estrutura de retorno é idêntica — o resto do sistema não muda.

## Publicar no Streamlit Community Cloud

1. Suba o projeto para um repositório GitHub
2. Acesse https://share.streamlit.io
3. Conecte o repositório e aponte para `app.py`
4. O app estará disponível em URL pública

Para controle de acesso futuro, use **Streamlit Community Cloud + autenticação via Google**
ou migre para Streamlit in Snowflake / instância privada.
