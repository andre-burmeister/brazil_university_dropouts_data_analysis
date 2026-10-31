"""Compara tamanhos e regenera o Parquet usado pelo painel.

Uso (na raiz do projeto, com o venv ativo):
    python test_compressao_dados.py

Baixa os microdados do Inep se faltarem, gera artefatos em
dados/compressao_teste/ e atualiza dados/ofertas_pos_merge.parquet
(arquivo lido pelo app).
"""

from __future__ import annotations

import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import certifi
import pandas as pd

import evasao

PASTA_SAIDA = evasao.RAIZ / "dados" / "compressao_teste"
CAMINHO_CA_INEP = evasao.RAIZ / "certs" / "rnp_icpedu_gr46_ov_tls_ca_2025.crt"
URLS_MICRODADOS = {
    2023: "https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2023.zip",
    2024: "https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2024.zip",
}
USER_AGENT_INEP = (
    "Mozilla/5.0 (compatible; evasao-painel/1.0; +https://github.com/)"
)
TENTATIVAS_DOWNLOAD = 3
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


def contexto_ssl_inep() -> ssl.SSLContext:
    """Confia na CA intermediária RNP ICPEdu (o servidor do Inep não envia a cadeia completa)."""
    contexto = ssl.create_default_context(cafile=certifi.where())
    contexto.load_verify_locations(cafile=str(CAMINHO_CA_INEP))
    return contexto


def baixar_arquivo(url: str, destino: Path, contexto_ssl: ssl.SSLContext) -> None:
    pedido = urllib.request.Request(url, headers={"User-Agent": USER_AGENT_INEP})
    ultimo_erro: Exception | None = None
    for tentativa in range(1, TENTATIVAS_DOWNLOAD + 1):
        try:
            with urllib.request.urlopen(
                pedido, timeout=120, context=contexto_ssl
            ) as resposta, destino.open("wb") as saida:
                while True:
                    bloco = resposta.read(1024 * 1024)
                    if not bloco:
                        break
                    saida.write(bloco)
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as erro:
            ultimo_erro = erro
            destino.unlink(missing_ok=True)
            if tentativa < TENTATIVAS_DOWNLOAD:
                time.sleep(2 * tentativa)
    raise ultimo_erro  # type: ignore[misc]


def garantir_microdados(ano: int) -> Path:
    """Baixa o pacote do Inep e extrai só o CSV de cadastro de cursos, se faltar."""
    destino = evasao.caminho_cursos(ano)
    if destino.is_file():
        return destino

    url = URLS_MICRODADOS[ano]
    nome_csv = f"MICRODADOS_CADASTRO_CURSOS_{ano}.CSV"
    evasao.PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    destino.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        suffix=".zip", delete=False, dir=evasao.PASTA_DADOS
    ) as temporario:
        caminho_zip = Path(temporario.name)

    try:
        baixar_arquivo(url, caminho_zip, contexto_ssl_inep())

        with zipfile.ZipFile(caminho_zip) as arquivo_zip:
            membro = next(
                (
                    nome
                    for nome in arquivo_zip.namelist()
                    if Path(nome).name.upper() == nome_csv
                ),
                None,
            )
            if membro is None:
                raise FileNotFoundError(f"{nome_csv} não encontrado em {url}")
            with arquivo_zip.open(membro) as origem, destino.open("wb") as saida:
                while True:
                    bloco = origem.read(1024 * 1024)
                    if not bloco:
                        break
                    saida.write(bloco)
    finally:
        caminho_zip.unlink(missing_ok=True)

    return destino


def formatar_linha(rotulo: str, caminho: Path, segundos: float | None = None) -> str:
    tempo = f"  ({segundos:.1f}s)" if segundos is not None else ""
    return f"{rotulo:<48} {mb(caminho):8.1f} MB{tempo}"


def gerar_pos_merge(cursos: dict[int, pd.DataFrame]) -> list[tuple[str, Path, float | None]]:
    """Gera a tabela já mesclada e grava o Parquet do app."""
    t0 = time.perf_counter()
    ofertas = evasao.calcular_evasao(cursos[ANOS[0]], cursos[ANOS[1]])
    t_merge = time.perf_counter() - t0

    parquet_teste = PASTA_SAIDA / "ofertas_pos_merge.parquet"
    t0 = time.perf_counter()
    ofertas.to_parquet(parquet_teste, index=False, compression="zstd")
    t_parquet = time.perf_counter() - t0

    evasao.PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    ofertas.to_parquet(evasao.CAMINHO_OFERTAS, index=False, compression="zstd")

    csv_merge = PASTA_SAIDA / "ofertas_pos_merge.csv"
    t0 = time.perf_counter()
    ofertas.to_csv(csv_merge, index=False, sep=";", encoding="utf-8")
    t_csv = time.perf_counter() - t0

    print(
        f"\nPós-merge: {len(ofertas):,} linhas × {ofertas.shape[1]} colunas "
        f"(calcular_evasao {t_merge:.1f}s)"
    )
    print(f"Atualizado para o app: {evasao.CAMINHO_OFERTAS}")
    return [
        ("CSV pós-merge", csv_merge, t_csv),
        ("Parquet pós-merge (zstd)", parquet_teste, t_parquet),
        ("Parquet do app (zstd)", evasao.CAMINHO_OFERTAS, None),
    ]


def main() -> None:
    exigir_pyarrow()
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    print(f"Saída de teste: {PASTA_SAIDA}\n")

    resultados: list[tuple[str, Path, float | None]] = []
    cursos: dict[int, pd.DataFrame] = {}

    for ano in ANOS:
        print(f"--- Ano {ano} ---")
        origem = evasao.caminho_cursos(ano)
        if not origem.is_file():
            print(f"Baixando microdados {ano}...")
            garantir_microdados(ano)

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
    parquet_merge = mb(evasao.CAMINHO_OFERTAS)
    print(
        f"\nResumo:\n"
        f"  Originais (2 CSVs):           {original_total:8.1f} MB\n"
        f"  Parquet 79 cols (2 anos):     {parquet_anos:8.1f} MB"
        f"  ({100 * parquet_anos / original_total:.1f}% do original)\n"
        f"  Parquet do app (pós-merge):   {parquet_merge:8.1f} MB"
        f"  ({100 * parquet_merge / original_total:.1f}% do original)"
    )


if __name__ == "__main__":
    main()
