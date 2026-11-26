# Análise da Inflação de Aracaju vs. Média Nacional (IPCA 2014–Atual)

Projeto desenvolvido para a disciplina de Economia e Finanças (Prof. Sérgio Santana — Universidade Tiradentes - UNIT).

**Equipe:**
- Beatriz Santos Noronha
- Leandro Ribeiro de Siqueira Maciel Neto

## Pergunta de Pesquisa
    Quais grupos do IPCA explicam a diferença entre a inflação de Aracaju e a média nacional desde 2014?

## Estrutura do Projeto
- `src/extract.py`: Extração automatizada via API SIDRA (IBGE) das Tabelas 1419 (2014–2019) e 7060 (2020–atual) com registro de metadados (`data/raw/metadata_extracao.json`).
- `src/transform.py`: Limpeza, padronização temporal e exportação em formato colunar (`data/processed/ipca_aracaju_comparativo.parquet`).
- `src/validate.py`: Testes automatizados de qualidade (duplicatas, nulos, soma de pesos ~100%, transição POF 2019/2020 e consistência das contribuições) e geração de `reports/relatorio_qualidade.md`.
- `notebooks/`: Análise exploratória e decomposição da contribuição por grupo.
- `app.py`: Painel interativo comparando Aracaju, Brasil e capitais do Nordeste.

## Como Reproduzir o Pipeline

1. Clone o repositório:
   ```bash
   git clone [https://github.com/SEU-USUARIO/ipca-aracaju-analise.git](https://github.com/SEU-USUARIO/ipca-aracaju-analise.git)
   cd ipca-aracaju-analise

2. Crie e ative o ambiente virtual e instale as dependências:
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

3. Execute as etapas do pipeline na ordem:
    python src/extract.py
    python src/transform.py
    python src/validate.py