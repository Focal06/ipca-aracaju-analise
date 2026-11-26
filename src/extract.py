import json
import time
from datetime import datetime, timezone
from pathlib import Path
import requests

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://apisidra.ibge.gov.br/values"

# Tabelas do IPCA por mudança de ponderação (POF)
TABELAS = {
    "1419": {
        "descricao": "IPCA - Série histórica 2012-2019 (POF 2008-2009)",
        "periodo": "201401-201912",
    },
    "7060": {
        "descricao": "IPCA - Série a partir de jan/2020 (POF 2017-2018)",
        "periodo": "all",
    },
}

# Variáveis SIDRA:
# 63 = Variação mensal (%)
# 2265 = Variação acumulada em 12 meses (%)
# 66 = Peso mensal (%)
VARIAVEIS = "63,2265,66"

# Classificação c315 (Geral + 9 grupos do IPCA):
# 7169: Índice geral | 7170: Alimentação e bebidas | 7445: Habitação
# 7486: Artigos de residência | 7558: Vestuário | 7625: Transportes
# 7660: Saúde e cuidados pessoais | 7712: Despesas pessoais
# 7766: Educação | 7786: Comunicação
GRUPOS_C315 = "7169,7170,7445,7486,7558,7625,7660,7712,7766,7786"

# Localidades: Brasil (n1/1) e Municípios capitais do Nordeste no IPCA (n6)
# 2800308: Aracaju | 2927408: Salvador | 2611606: Recife
# 2304400: Fortaleza | 2111300: São Luís
LOCALIDADES = [
    ("n1", "1", "Brasil"),
    ("n6", "2800308", "Aracaju"),
    ("n6", "2927408", "Salvador"),
    ("n6", "2611606", "Recife"),
    ("n6", "2304400", "Fortaleza"),
    ("n6", "2111300", "Sao_Luis"),
]


def extrair_sidra():
    metadados = {
        "data_extracao_utc": datetime.now(timezone.utc).isoformat(),
        "fonte": "IBGE - Sistema IBGE de Recuperação Automática (SIDRA)",
        "requisicoes": [],
    }

    for tabela_id, info in TABELAS.items():
        periodo = info["periodo"]
        for nivel, cod_loc, nome_loc in LOCALIDADES:
            url = (
                f"{BASE_URL}/t/{tabela_id}"
                f"/{nivel}/{cod_loc}"
                f"/v/{VARIAVEIS}"
                f"/p/{periodo}"
                f"/c315/{GRUPOS_C315}"
                f"/d/v63%202,v2265%202,v66%204"
            )

            print(f"Coletando Tabela {tabela_id} | {nome_loc} ({periodo})...")
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            dados = resp.json()

            arquivo_saida = RAW_DIR / f"ipca_t{tabela_id}_{nome_loc.lower()}.json"
            with open(arquivo_saida, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)

            metadados["requisicoes"].append(
                {
                    "tabela": tabela_id,
                    "descricao": info["descricao"],
                    "localidade": nome_loc,
                    "codigo_territorial": f"{nivel}/{cod_loc}",
                    "periodo_solicitado": periodo,
                    "url": url,
                    "registros_retornados": len(dados) - 1,  # desconta cabeçalho SIDRA
                    "arquivo_raw": str(arquivo_saida),
                }
            )
            time.sleep(0.5)  # evita sobrecarga na API do IBGE

    meta_path = RAW_DIR / "metadata_extracao.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadados, f, ensure_ascii=False, indent=2)

    print(f"\nExtração concluída! Metadados salvos em {meta_path}")


if __name__ == "__main__":
    extrair_sidra()