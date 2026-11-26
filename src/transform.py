from pathlib import Path
import json
import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

SAIDA_PARQUET = PROCESSED_DIR / "ipca_aracaju_comparativo.parquet"

MAPA_VARIAVEIS = {
    "63": "var_mensal",
    "2265": "var_12m",
    "66": "peso_mensal",
}

MAPA_LOCALIDADES = {
    "1": "Brasil",
    "2800308": "Aracaju",
    "2927408": "Salvador",
    "2611606": "Recife",
    "2304400": "Fortaleza",
    "2111300": "Sao_Luis",
}


def _para_float(valor):
    if valor is None:
        return None
    texto = str(valor).strip().replace(",", ".")
    if texto in {"", "-", "...", "X", ".."}:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def _parse_data_sidra(cod_periodo: str):
    cod_periodo = str(cod_periodo).strip()
    if len(cod_periodo) != 6 or not cod_periodo.isdigit():
        return pd.NaT
    ano = int(cod_periodo[:4])
    mes = int(cod_periodo[4:6])
    return pd.Timestamp(year=ano, month=mes, day=1)


def transformar_dados():
    arquivos = sorted(RAW_DIR.glob("ipca_t*.json"))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo ipca_t*.json encontrado em {RAW_DIR}. Rode src/extract.py primeiro."
        )

    registros = []
    for arq in arquivos:
        partes = arq.stem.split("_")
        tabela_id = partes[1].replace("t", "") if len(partes) > 1 else "desconhecida"

        with open(arq, "r", encoding="utf-8") as f:
            raw_json = json.load(f)

        if not isinstance(raw_json, list) or len(raw_json) < 2:
            continue

        linhas = raw_json[1:]

        for linha in linhas:
            cod_var = str(linha.get("D2C", "")).strip()
            nome_var = MAPA_VARIAVEIS.get(cod_var)
            if not nome_var:
                continue

            # No retorno do SIDRA para esses endpoints, localidade está em D1C/D1N e grupo (c315) em D4C/D4N
            cod_loc = str(linha.get("D1C", "")).strip()
            nome_loc = MAPA_LOCALIDADES.get(cod_loc, str(linha.get("D1N", "")).strip())

            data_ref = _parse_data_sidra(linha.get("D3C", ""))
            if pd.isna(data_ref):
                continue

            if data_ref < pd.Timestamp("2014-01-01"):
                continue
            if tabela_id == "1419" and data_ref > pd.Timestamp("2019-12-01"):
                continue
            if tabela_id == "7060" and data_ref < pd.Timestamp("2020-01-01"):
                continue

            registros.append(
                {
                    "data_ref": data_ref,
                    "ano": data_ref.year,
                    "mes": data_ref.month,
                    "tabela_sidra": tabela_id,
                    "localidade_codigo": cod_loc,
                    "localidade": nome_loc,
                    "grupo_codigo": str(linha.get("D4C", "")).strip(),
                    "grupo": str(linha.get("D4N", "")).strip(),
                    "variavel": nome_var,
                    "valor": _para_float(linha.get("V")),
                }
            )

    if not registros:
        raise ValueError("Nenhum registro válido foi extraído dos arquivos brutos.")

    df_long = pd.DataFrame(registros)

    df_wide = (
        df_long.pivot_table(
            index=[
                "data_ref",
                "ano",
                "mes",
                "tabela_sidra",
                "localidade_codigo",
                "localidade",
                "grupo_codigo",
                "grupo",
            ],
            columns="variavel",
            values="valor",
            aggfunc="first",
        )
        .reset_index()
        .sort_values(["localidade", "data_ref", "grupo_codigo"])
        .reset_index(drop=True)
    )

    df_wide.columns.name = None
    df_wide.to_parquet(SAIDA_PARQUET, index=False)
    print(f"Base tratada salva em {SAIDA_PARQUET} ({len(df_wide)} linhas).")


if __name__ == "__main__":
    transformar_dados()
