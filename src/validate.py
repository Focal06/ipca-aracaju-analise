from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

PARQUET_PATH = Path("data/processed/ipca_aracaju_comparativo.parquet")
REPORT_PATH = Path("reports/relatorio_qualidade.md")
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

COD_INDICE_GERAL = "7169"
GRUPOS_ESPERADOS = {
    "7170",
    "7445",
    "7486",
    "7558",
    "7625",
    "7660",
    "7712",
    "7766",
    "7786",
}


def rodar_validacoes():
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo {PARQUET_PATH} não encontrado. Rode src/transform.py antes."
        )

    df = pd.read_parquet(PARQUET_PATH)
    df["data_ref"] = pd.to_datetime(df["data_ref"])

    resultados = []

    duplicatas = int(
        df.duplicated(subset=["data_ref", "localidade", "grupo_codigo"]).sum()
    )
    resultados.append(
        {
            "teste": "Ausência de duplicatas por (data_ref, localidade, grupo)",
            "status": "APROVADO" if duplicatas == 0 else "FALHA",
            "detalhe": f"{duplicatas} linha(s) duplicada(s) encontrada(s).",
        }
    )

    nulos_var = int(df["var_mensal"].isna().sum())
    nulos_peso = int(df["peso_mensal"].isna().sum())
    ok_nulos = (nulos_var == 0) and (nulos_peso == 0)
    resultados.append(
        {
            "teste": "Completude de var_mensal e peso_mensal (sem nulos)",
            "status": "APROVADO" if ok_nulos else "ALERTA",
            "detalhe": f"Nulos em var_mensal: {nulos_var} | Nulos em peso_mensal: {nulos_peso}.",
        }
    )

    df_grupos = df[df["grupo_codigo"].isin(GRUPOS_ESPERADOS)].copy()
    soma_pesos = (
        df_grupos.groupby(["localidade", "data_ref"], as_index=False)["peso_mensal"]
        .sum()
    )
    fora_faixa_peso = soma_pesos[
        (soma_pesos["peso_mensal"] < 99.5) | (soma_pesos["peso_mensal"] > 100.5)
    ]
    resultados.append(
        {
            "teste": "Soma dos pesos dos 9 grupos próxima de 100% (99.5%–100.5%)",
            "status": "APROVADO" if len(fora_faixa_peso) == 0 else "ALERTA",
            "detalhe": (
                f"{len(fora_faixa_peso)} recorte(s) (localidade/mês) fora da faixa "
                f"(média geral: {soma_pesos['peso_mensal'].mean():.4f}%)."
            ),
        }
    )

    t1419_max = df[df["tabela_sidra"] == "1419"]["data_ref"].max()
    t7060_min = df[df["tabela_sidra"] == "7060"]["data_ref"].min()
    transicao_ok = (
        pd.notna(t1419_max)
        and pd.notna(t7060_min)
        and t1419_max == pd.Timestamp("2019-12-01")
        and t7060_min == pd.Timestamp("2020-01-01")
    )
    resultados.append(
        {
            "teste": "Transição limpa Tabela 1419 (2019-12) -> Tabela 7060 (2020-01)",
            "status": "APROVADO" if transicao_ok else "ALERTA",
            "detalhe": (
                f"Máx Tabela 1419: {t1419_max.strftime('%Y-%m') if pd.notna(t1419_max) else 'N/A'} | "
                f"Mín Tabela 7060: {t7060_min.strftime('%Y-%m') if pd.notna(t7060_min) else 'N/A'}."
            ),
        }
    )

    df_grupos["contrib_estimada"] = (
        df_grupos["peso_mensal"] * df_grupos["var_mensal"]
    ) / 100.0
    soma_contrib = (
        df_grupos.groupby(["localidade", "data_ref"], as_index=False)[
            "contrib_estimada"
        ]
        .sum()
    )

    df_geral = df[df["grupo_codigo"] == COD_INDICE_GERAL][
        ["localidade", "data_ref", "var_mensal"]
    ].rename(columns={"var_mensal": "var_geral"})

    comp_geral = pd.merge(
        soma_contrib, df_geral, on=["localidade", "data_ref"], how="inner"
    )
    comp_geral["erro_abs"] = (
        comp_geral["contrib_estimada"] - comp_geral["var_geral"]
    ).abs()
    erro_max = float(comp_geral["erro_abs"].max()) if len(comp_geral) > 0 else 0.0
    erro_medio = float(comp_geral["erro_abs"].mean()) if len(comp_geral) > 0 else 0.0

    resultados.append(
        {
            "teste": "Consistência soma das contribuições vs. variação do Índice Geral",
            "status": "APROVADO" if erro_max <= 0.15 else "ALERTA",
            "detalhe": f"Erro absoluto médio: {erro_medio:.4f} p.p. | Máximo: {erro_max:.4f} p.p.",
        }
    )

    data_min = df["data_ref"].min().strftime("%Y-%m")
    data_max = df["data_ref"].max().strftime("%Y-%m")
    locs = ", ".join(sorted(df["localidade"].unique()))
    gerado_em = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    linhas_md = [
        "# Relatório de Qualidade dos Dados — IPCA (Aracaju e Comparativos)",
        "",
        f"- **Gerado em:** {gerado_em}",
        f"- **Arquivo validado:** `{PARQUET_PATH}`",
        f"- **Total de registros:** {len(df):,}",
        f"- **Período coberto:** {data_min} a {data_max}",
        f"- **Localidades:** {locs}",
        "",
        "## Resultados dos Testes Automatizados",
        "",
        "| Teste de Qualidade | Status | Detalhes |",
        "| --- | --- | --- |",
    ]

    for r in resultados:
        linhas_md.append(f"| {r['teste']} | **{r['status']}** | {r['detalhe']} |")

    linhas_md.extend(
        [
            "",
            "## Observações Metodológicas",
            "- Pequenas diferenças entre a soma dos grupos e o índice geral ocorrem por arredondamento nativo das séries divulgadas no SIDRA e pela mudança metodológica da POF entre as tabelas 1419 (até 2019) e 7060 (a partir de 2020).",
            "- Este relatório atende à Etapa 4 (Carga e Qualidade) do pipeline.",
        ]
    )

    REPORT_PATH.write_text("\n".join(linhas_md), encoding="utf-8")
    print(f"Relatório de qualidade salvo em {REPORT_PATH}")
    for r in resultados:
        print(f"[{r['status']}] {r['teste']}: {r['detalhe']}")


if __name__ == "__main__":
    rodar_validacoes()
