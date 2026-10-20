"""Compara tamanhos: CSV original vs 79 colunas (CSV/Parquet) vs tabela pós-merge.

Uso (na raiz do projeto, com o venv ativo):
    python test_compressao_dados.py

Requer pyarrow para gravar Parquet:
    pip install pyarrow
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

import evasao

PASTA_SAIDA = evasao.RAIZ / "dados" / "compressao_teste"
ANOS = (evasao.ANO_INICIAL, evasao.ANO_FINAL)


def mb(caminho: Path) -> float:
    return caminho.stat().st_size / (1024 * 1024)


def exigir_pyarrow() -> None:
    try:
        import pyarrow  # noqa: F401
    except ImportError:
        print(
            "pyarrow não está instalado. Instale com:\n"
            "  pip install pyarrow\n"
            "e rode o script de novo.",
            file=sys.stderr,
        )
        sys.exit(1)


def formatar_linha(rotulo: str, caminho: Path, segundos: float | None = None) -> str:
    tempo = f"  ({segundos:.1f}s)" if segundos is not None else ""
    return f"{rotulo:<48} {mb(caminho):8.1f} MB{tempo}"


def gerar_pos_merge(cursos: dict[int, pd.DataFrame]) -> list[tuple[str, Path, float | None]]:
    """Gera a tabela já mesclada e com evasão calculada."""
    t0 = time.perf_counter()
    ofertas = evasao.calcular_evasao(cursos[ANOS[0]], cursos[ANOS[1]])
    t_merge = time.perf_counter() - t0

    parquet_merge = PASTA_SAIDA / "ofertas_pos_merge.parquet"
    t0 = time.perf_counter()
    ofertas.to_parquet(parquet_merge, index=False, compression="zstd")
    t_parquet = time.perf_counter() - t0

    csv_merge = PASTA_SAIDA / "ofertas_pos_merge.csv"
    t0 = time.perf_counter()
    ofertas.to_csv(csv_merge, index=False, sep=";", encoding="utf-8")
    t_csv = time.perf_counter() - t0

    print(
        f"\nPós-merge: {len(ofertas):,} linhas × {ofertas.shape[1]} colunas "
        f"(calcular_evasao {t_merge:.1f}s)"
    )
    return [
        ("CSV pós-merge", csv_merge, t_csv),
        ("Parquet pós-merge (zstd)", parquet_merge, t_parquet),
    ]


def main() -> None:
    exigir_pyarrow()
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    print(f"Saída: {PASTA_SAIDA}\n")

    resultados: list[tuple[str, Path, float | None]] = []
    cursos: dict[int, pd.DataFrame] = {}

    for ano in ANOS:
        print(f"--- Ano {ano} ---")
        origem = evasao.caminho_cursos(ano)
        if not origem.is_file():
            print(f"Baixando microdados {ano}...")
            evasao.garantir_microdados(ano)

        t0 = time.perf_counter()
        cursos[ano] = evasao.ler_cursos(ano)
        t_leitura = time.perf_counter() - t0
        print(
            f"Lido com usecols ({len(evasao.COLUNAS_CURSO)} cols): "
            f"{len(cursos[ano]):,} linhas em {t_leitura:.1f}s"
        )

        csv_slim = PASTA_SAIDA / f"cursos_{ano}_79cols.csv"
        t0 = time.perf_counter()
        cursos[ano].to_csv(csv_slim, index=False, sep=";", encoding="utf-8")
        t_csv = time.perf_counter() - t0

        parquet_slim = PASTA_SAIDA / f"cursos_{ano}_79cols.parquet"
        t0 = time.perf_counter()
        cursos[ano].to_parquet(parquet_slim, index=False, compression="zstd")
        t_parquet = time.perf_counter() - t0

        resultados.extend(
            [
                (f"original CSV {ano}", origem, None),
                (f"CSV slim 79 cols {ano}", csv_slim, t_csv),
                (f"Parquet 79 cols {ano} (zstd)", parquet_slim, t_parquet),
            ]
        )

    print("\n--- Pós-merge (calcular_evasao) ---")
    resultados.extend(gerar_pos_merge(cursos))

    print("\n=== Comparativo de tamanhos ===")
    for rotulo, caminho, segundos in resultados:
        print(formatar_linha(rotulo, caminho, segundos))

    original_total = sum(mb(evasao.caminho_cursos(ano)) for ano in ANOS)
    parquet_anos = sum(
        mb(PASTA_SAIDA / f"cursos_{ano}_79cols.parquet") for ano in ANOS
    )
    parquet_merge = mb(PASTA_SAIDA / "ofertas_pos_merge.parquet")
    print(
        f"\nResumo:\n"
        f"  Originais (2 CSVs):           {original_total:8.1f} MB\n"
        f"  Parquet 79 cols (2 anos):     {parquet_anos:8.1f} MB"
        f"  ({100 * parquet_anos / original_total:.1f}% do original)\n"
        f"  Parquet pós-merge (1 arquivo):{parquet_merge:8.1f} MB"
        f"  ({100 * parquet_merge / original_total:.1f}% do original)"
    )


if __name__ == "__main__":
    main()
