"""Taxa de evasão entre os censos de 2023 e 2024 e os gráficos do painel."""

from pathlib import Path
import copy
import json
import zlib

import altair as alt
import branca.colormap as cm
import folium
import numpy as np
import pandas as pd
from branca.element import MacroElement, Template

RAIZ = Path(__file__).resolve().parent
PASTA_DADOS = RAIZ / "dados"
CAMINHO_GEOJSON = RAIZ / "geo" / "brazil_states.geojson"
ANO_INICIAL = 2023
ANO_FINAL = 2024

MODALIDADE = {1: "Presencial", 2: "A distância"}
ORGANIZACAO = {
    1: "Universidade",
    2: "Centro universitário",
    3: "Faculdade",
    4: "Instituto Federal de Educação, Ciência e Tecnologia",
    5: "Centro Federal de Educação Tecnológica",
}
CATEGORIA = {
    1: "Pública federal",
    2: "Pública estadual",
    3: "Pública municipal",
    4: "Privada com fins lucrativos",
    5: "Privada sem fins lucrativos",
    7: "Especial",
}
AREA_PADRAO = "Ciências naturais, matemática e estatística"

CHAVES_OFERTA = ["CO_IES", "CO_CURSO", "CO_MUNICIPIO", "TP_DIMENSAO"]
SUFIXOS_GRUPO = [
    "FEM",
    "MASC",
    "0_17",
    "18_24",
    "25_29",
    "30_34",
    "35_39",
    "40_49",
    "50_59",
    "60_MAIS",
    "BRANCA",
    "PRETA",
    "PARDA",
    "AMARELA",
    "INDIGENA",
    "CORND",
    "DEFICIENTE",
    "RESERVA_VAGA",
    "PROCESCPUBLICA",
    "PROCESCPRIVADA",
    "PROCNAOINFORMADA",
]
# O segundo grupo destes pares é o total menos o subgrupo.
COMPLEMENTOS_GRUPO = [
    ("SEM_DEFICIENTE", "DEFICIENTE"),
    ("SEM_RESERVA", "RESERVA_VAGA"),
]
COLUNAS_CURSO = [
    *CHAVES_OFERTA,
    "NO_CURSO",
    "CO_CINE_ROTULO",
    "NO_CINE_ROTULO",
    "SG_UF",
    "NO_UF",
    "NO_CINE_AREA_GERAL",
    "TP_MODALIDADE_ENSINO",
    "TP_ORGANIZACAO_ACADEMICA",
    "TP_CATEGORIA_ADMINISTRATIVA",
    "QT_MAT",
    "QT_ING",
    "QT_CONC",
    *[
        f"QT_{prefixo}_{sufixo}"
        for sufixo in SUFIXOS_GRUPO
        for prefixo in ("MAT", "CONC", "ING")
    ],
]
QUANTIDADES = ["QT_MAT_2023", "QT_CONC_2023", "QT_EVAS"]
COR_TEXTO = "#14222b"
COR_TEXTO_BARRA = "#ffffff"
CORES_AREA = {
    "Agricultura, silvicultura, pesca e veterinária": "#3d6b22",
    "Artes e humanidades": "#9d3c66",
    "Ciências naturais, matemática e estatística": "#0f766e",
    "Ciências sociais, comunicação e informação": "#1d4e89",
    "Computação e Tecnologias da Informação e Comunicação (TIC)": "#4338ca",
    "Educação": "#0e7490",
    "Engenharia, produção e construção": "#c2410c",
    "Negócios, administração e direito": "#a16207",
    "Programas básicos": "#475569",
    "Saúde e bem-estar": "#7e22ce",
    "Serviços": "#9f1239",
    "Sem área": "#57534e",
}
COR_FUNDO_MAPA = "#f6f4ef"
COR_SEM_DADOS = "#b7b1a8"
COR_CONTORNO = "#4e4842"
COR_SELECAO = "#0e7c74"
CORES_TAXA = ["#ffffcc", "#fed976", "#fd8d3c", "#e31a1c", "#800026"]
CORES_DIFERENCA = ["#0f766e", "#99d1cb", "#f7f7f7", "#fdbe85", "#e31a1c"]
TAXA_GERAL = "GERAL"
ROTULO_TAXA_GERAL = "Taxa geral"
MIN_MATRICULAS_FAIXA = 100
EIXOS_VOLUME = {
    "instituicoes": "Número de instituições",
    "matriculas": "Matrículas em 2023",
}
GRANULACAO = {
    "curso": "Curso",
    "area": "Área do conhecimento",
}
METRICAS_MAPA = {
    "taxa": {
        "rotulo": "Taxa de evasão",
        "coluna": "taxa_pct",
        "titulo_legenda": "Taxa de evasão (%)",
        "formato": "percentual",
        "sufixo": "%",
    },
    "matriculas": {
        "rotulo": "Alunos matriculados por mil habitantes",
        "coluna": "MAT_POR_MIL",
        "titulo_legenda": "Matrículas por mil hab.",
        "formato": "decimal",
        "sufixo": " por mil",
    },
    "instituicoes": {
        "rotulo": "Instituições por milhão de habitantes",
        "coluna": "IES_POR_MILHAO",
        "titulo_legenda": "Instituições por milhão",
        "formato": "decimal",
        "sufixo": " por milhão",
    },
    "municipios": {
        "rotulo": "Porcentagem de municípios com IES",
        "coluna": "PCT_MUN_IES",
        "titulo_legenda": "Municípios com IES (%)",
        "formato": "percentual",
        "sufixo": "%",
    },
}
# População: estimativa do IBGE em 1º de julho de 2024 (SIDRA, tabela 6579).
# Municípios: 5.570 em 2024. Mato Grosso tinha 141; Boa Esperança do Norte entrou em 2025.
# A tupla é (código da UF, população, municípios).
REFERENCIA_UF = {
    "RO": (11, 1_746_227, 52),
    "AC": (12, 880_631, 22),
    "AM": (13, 4_281_209, 62),
    "RR": (14, 716_793, 15),
    "PA": (15, 8_664_306, 144),
    "AP": (16, 802_837, 16),
    "TO": (17, 1_577_342, 139),
    "MA": (21, 7_010_960, 217),
    "PI": (22, 3_375_646, 224),
    "CE": (23, 9_233_656, 184),
    "RN": (24, 3_446_071, 167),
    "PB": (25, 4_145_040, 223),
    "PE": (26, 9_539_029, 185),
    "AL": (27, 3_220_104, 102),
    "SE": (28, 2_291_077, 75),
    "BA": (29, 14_850_513, 417),
    "MG": (31, 21_322_691, 853),
    "ES": (32, 4_102_129, 78),
    "RJ": (33, 17_219_679, 92),
    "SP": (35, 45_973_194, 645),
    "PR": (41, 11_824_665, 399),
    "SC": (42, 8_058_441, 295),
    "RS": (43, 11_229_915, 497),
    "MS": (50, 2_901_895, 79),
    "MT": (51, 3_836_399, 141),
    "GO": (52, 7_350_483, 246),
    "DF": (53, 2_982_818, 1),
}


def _grupo(identificador, rotulo, cor):
    return {"id": identificador, "rotulo": rotulo, "cor": cor}


COMPARACOES = {
    "sexo": {
        "rotulo": "Mulheres e homens",
        "modo": "diferenca",
        "texto_diferenca": "mulheres − homens",
        "legenda": "Mulheres − homens (p.p.)",
        "grupos": [
            _grupo("FEM", "Mulheres", CORES_DIFERENCA[-1]),
            _grupo("MASC", "Homens", CORES_DIFERENCA[0]),
        ],
        "diferenca": ("FEM", "MASC"),
    },
    "idade": {
        "rotulo": "Faixas de idade",
        "modo": "categoria",
        "grupos": [
            _grupo("0_17", "Até 17 anos", "#0e7490"),
            _grupo("18_24", "18 a 24 anos", "#1d4e89"),
            _grupo("25_29", "25 a 29 anos", "#4338ca"),
            _grupo("30_34", "30 a 34 anos", "#0f766e"),
            _grupo("35_39", "35 a 39 anos", "#3d6b22"),
            _grupo("40_49", "40 a 49 anos", "#a16207"),
            _grupo("50_59", "50 a 59 anos", "#c2410c"),
            _grupo("60_MAIS", "60 anos ou mais", "#9f1239"),
        ],
    },
    "raca": {
        "rotulo": "Cor ou raça",
        "modo": "categoria",
        "grupos": [
            _grupo("BRANCA", "Branca", "#1d4e89"),
            _grupo("PRETA", "Preta", "#7e22ce"),
            _grupo("PARDA", "Parda", "#c2410c"),
            _grupo("AMARELA", "Amarela", "#a16207"),
            _grupo("INDIGENA", "Indígena", "#3d6b22"),
            _grupo("CORND", "Não declarada", "#57534e"),
        ],
    },
    "deficiencia": {
        "rotulo": "Alunos com ou sem deficiência",
        "modo": "diferenca",
        "texto_diferenca": "com deficiência − sem deficiência",
        "legenda": "Com deficiência − sem deficiência (p.p.)",
        "grupos": [
            _grupo("DEFICIENTE", "Com deficiência", CORES_DIFERENCA[-1]),
            _grupo("SEM_DEFICIENTE", "Sem deficiência", CORES_DIFERENCA[0]),
        ],
        "diferenca": ("DEFICIENTE", "SEM_DEFICIENTE"),
    },
    "cotas": {
        "rotulo": "Alunos cotistas ou não cotistas",
        "modo": "diferenca",
        "texto_diferenca": "cotistas − não cotistas",
        "legenda": "Cotistas − não cotistas (p.p.)",
        "grupos": [
            _grupo("RESERVA_VAGA", "Cotistas", CORES_DIFERENCA[-1]),
            _grupo("SEM_RESERVA", "Não cotistas", CORES_DIFERENCA[0]),
        ],
        "diferenca": ("RESERVA_VAGA", "SEM_RESERVA"),
    },
    "escola": {
        "rotulo": "Escola pública ou particular",
        "modo": "diferenca",
        "texto_diferenca": "escola pública − particular",
        "legenda": "Escola pública − particular (p.p.)",
        "nota": "Quem não informou a escola aparece nas barras e fica de fora desta diferença.",
        "grupos": [
            _grupo("PROCESCPUBLICA", "Escola pública", CORES_DIFERENCA[-1]),
            _grupo("PROCESCPRIVADA", "Escola particular", CORES_DIFERENCA[0]),
            _grupo("PROCNAOINFORMADA", "Não informada", "#57534e"),
        ],
        "diferenca": ("PROCESCPUBLICA", "PROCESCPRIVADA"),
    },
}


def caminho_cursos(ano):
    return (
        PASTA_DADOS
        / f"microdados_censo_da_educacao_superior_{ano}"
        / "dados"
        / f"MICRODADOS_CADASTRO_CURSOS_{ano}.CSV"
    )


def ler_cursos(ano):
    return pd.read_csv(
        caminho_cursos(ano),
        sep=";",
        encoding="latin-1",
        usecols=COLUNAS_CURSO,
        low_memory=False,
    )


def calcular_evasao(cursos_inicial, cursos_final):
    """Estima saídas entre os dois censos, em cada oferta de curso.

    matrículas_2023 - concluintes_2023 - matrículas_2024 + ingressantes_2024
    """
    esquerda = cursos_inicial.copy()
    direita = cursos_final.copy()
    for tabela in (esquerda, direita):
        tabela["CO_MUNICIPIO"] = tabela["CO_MUNICIPIO"].fillna(-1)

    renomear_esquerda = {"QT_MAT": "QT_MAT_2023", "QT_CONC": "QT_CONC_2023"}
    renomear_direita = {"QT_MAT": "QT_MAT_2024", "QT_ING": "QT_ING_2024"}
    for sufixo in SUFIXOS_GRUPO:
        renomear_esquerda[f"QT_MAT_{sufixo}"] = f"QT_MAT_{sufixo}_2023"
        renomear_esquerda[f"QT_CONC_{sufixo}"] = f"QT_CONC_{sufixo}_2023"
        renomear_direita[f"QT_MAT_{sufixo}"] = f"QT_MAT_{sufixo}_2024"
        renomear_direita[f"QT_ING_{sufixo}"] = f"QT_ING_{sufixo}_2024"
    esquerda = esquerda.rename(columns=renomear_esquerda)
    direita = direita.rename(columns=renomear_direita)
    colunas_direita = ["QT_MAT_2024", "QT_ING_2024"]
    for sufixo in SUFIXOS_GRUPO:
        colunas_direita.extend([f"QT_MAT_{sufixo}_2024", f"QT_ING_{sufixo}_2024"])
    pares = esquerda.merge(
        direita[CHAVES_OFERTA + colunas_direita],
        on=CHAVES_OFERTA,
        how="inner",
    )
    pares["CO_MUNICIPIO"] = pares["CO_MUNICIPIO"].replace(-1, pd.NA)
    quantidades = ["QT_MAT_2023", "QT_CONC_2023", "QT_MAT_2024", "QT_ING_2024"]
    for sufixo in SUFIXOS_GRUPO:
        quantidades.extend(
            [
                f"QT_MAT_{sufixo}_2023",
                f"QT_CONC_{sufixo}_2023",
                f"QT_MAT_{sufixo}_2024",
                f"QT_ING_{sufixo}_2024",
            ]
        )
    pares[quantidades] = pares[quantidades].fillna(0)
    evasao_total = (
        pares["QT_MAT_2023"] - pares["QT_CONC_2023"] - pares["QT_MAT_2024"] + pares["QT_ING_2024"]
    )
    contagens = {"QT_EVAS": evasao_total}
    for sufixo in SUFIXOS_GRUPO:
        contagens[f"QT_EVAS_{sufixo}"] = (
            pares[f"QT_MAT_{sufixo}_2023"]
            - pares[f"QT_CONC_{sufixo}_2023"]
            - pares[f"QT_MAT_{sufixo}_2024"]
            + pares[f"QT_ING_{sufixo}_2024"]
        )
    for destino, origem in COMPLEMENTOS_GRUPO:
        contagens[f"QT_MAT_{destino}_2023"] = pares["QT_MAT_2023"] - pares[f"QT_MAT_{origem}_2023"]
        contagens[f"QT_EVAS_{destino}"] = evasao_total - contagens[f"QT_EVAS_{origem}"]
    pares = pd.concat([pares, pd.DataFrame(contagens, index=pares.index)], axis=1)
    descartar = [f"QT_ING_{sufixo}" for sufixo in SUFIXOS_GRUPO]
    for sufixo in SUFIXOS_GRUPO:
        descartar.extend(
            [
                f"QT_CONC_{sufixo}_2023",
                f"QT_MAT_{sufixo}_2024",
                f"QT_ING_{sufixo}_2024",
            ]
        )
    pares = pares.drop(columns=descartar)
    pares["NO_CINE_AREA_GERAL"] = pares["NO_CINE_AREA_GERAL"].fillna("Sem área")
    # O nome livre (NO_CURSO) varia entre instituições. O código CINE identifica o curso.
    pares["CO_CINE_ROTULO"] = (
        pares["CO_CINE_ROTULO"].astype("string").str.strip().str.strip('"')
    )
    pares["NO_CINE_ROTULO"] = pares["NO_CINE_ROTULO"].fillna("Sem rótulo").astype("string").str.strip()
    return pares


def carregar_ofertas():
    return calcular_evasao(ler_cursos(ANO_INICIAL), ler_cursos(ANO_FINAL))


def carregar_geojson():
    return json.loads(CAMINHO_GEOJSON.read_text(encoding="utf-8"))


def filtrar_ofertas(ofertas, modalidades, organizacao, categoria):
    recorte = ofertas[ofertas["TP_MODALIDADE_ENSINO"].isin(modalidades)]
    if organizacao is not None:
        recorte = recorte[recorte["TP_ORGANIZACAO_ACADEMICA"] == organizacao]
    if categoria is not None:
        recorte = recorte[recorte["TP_CATEGORIA_ADMINISTRATIVA"] == categoria]
    return recorte


def agregar_taxa(df, chaves):
    """Soma as contagens e só depois divide. A taxa fica ponderada pelas matrículas."""
    agrupado = df.groupby(chaves, dropna=False)[QUANTIDADES].sum().reset_index()
    agrupado["TX_EVAS"] = agrupado["QT_EVAS"] / agrupado["QT_MAT_2023"].replace(0, pd.NA)
    return agrupado


def resumir_ofertas(ofertas):
    """Agrega cursos e áreas a partir das ofertas já elegíveis."""
    cursos = agregar_taxa(ofertas, ["CO_CINE_ROTULO"])
    cursos = cursos.merge(_rotulo_do_curso(ofertas), on="CO_CINE_ROTULO", how="left")
    cursos = cursos.merge(_area_predominante(ofertas), on="CO_CINE_ROTULO", how="left")
    areas = agregar_taxa(cursos, ["NO_CINE_AREA_GERAL"]) if not cursos.empty else cursos.iloc[0:0]
    return {
        "ofertas": ofertas,
        "cursos": cursos.dropna(subset=["TX_EVAS"]),
        "areas": areas.dropna(subset=["TX_EVAS"]) if "TX_EVAS" in areas.columns else areas,
    }


def _estados_vazios():
    return pd.DataFrame(
        columns=[
            "SG_UF",
            "NO_UF",
            *QUANTIDADES,
            "TX_EVAS",
            "QT_IES",
            "QT_MUN_IES",
            "POPULACAO",
            "N_MUNICIPIOS",
            "MAT_POR_MIL",
            "IES_POR_MILHAO",
            "PCT_MUN_IES",
        ]
    )


def _referencia_uf():
    return pd.DataFrame(
        [
            {
                "SG_UF": sigla,
                "CO_UF": codigo,
                "POPULACAO": populacao,
                "N_MUNICIPIOS": municipios,
            }
            for sigla, (codigo, populacao, municipios) in REFERENCIA_UF.items()
        ]
    )


def _municipios_com_ies(ofertas):
    """Municípios da própria UF com ao menos uma oferta no recorte."""
    locais = ofertas.dropna(subset=["CO_MUNICIPIO", "SG_UF"]).copy()
    if locais.empty:
        return pd.DataFrame(columns=["SG_UF", "QT_MUN_IES"])
    codigo_municipio = (
        locais["CO_MUNICIPIO"].astype("int64").astype(str).str.zfill(7).str[:2].astype(int)
    )
    codigo_uf = locais["SG_UF"].map({sigla: dados[0] for sigla, dados in REFERENCIA_UF.items()})
    locais = locais[codigo_municipio == codigo_uf]
    if locais.empty:
        return pd.DataFrame(columns=["SG_UF", "QT_MUN_IES"])
    return locais.groupby("SG_UF", dropna=False)["CO_MUNICIPIO"].nunique().rename("QT_MUN_IES").reset_index()


def _taxas_territoriais(estados):
    """Matrículas por mil habitantes, instituições por milhão e cobertura municipal."""
    estados = estados.merge(_referencia_uf(), on="SG_UF", how="left")
    estados["MAT_POR_MIL"] = estados["QT_MAT_2023"] / estados["POPULACAO"] * 1_000
    estados["IES_POR_MILHAO"] = estados["QT_IES"] / estados["POPULACAO"] * 1_000_000
    estados["PCT_MUN_IES"] = estados["QT_MUN_IES"] / estados["N_MUNICIPIOS"] * 100
    return estados


def _estados_de_ofertas(ofertas):
    """Soma a taxa, as instituições e a cobertura municipal por UF."""
    if ofertas.empty:
        return _estados_vazios()
    no_estado = ofertas[ofertas["SG_UF"].notna()]
    if no_estado.empty:
        return _estados_vazios()
    estados = agregar_taxa(no_estado, ["SG_UF", "NO_UF"])
    instituicoes = (
        no_estado.groupby("SG_UF", dropna=False)["CO_IES"].nunique().rename("QT_IES").reset_index()
    )
    estados = estados.merge(instituicoes, on="SG_UF", how="left")
    estados = estados.merge(_municipios_com_ies(no_estado), on="SG_UF", how="left")
    estados["QT_IES"] = estados["QT_IES"].fillna(0)
    estados["QT_MUN_IES"] = estados["QT_MUN_IES"].fillna(0)
    return _taxas_territoriais(estados)


def preparar_recorte(ofertas, modalidades, matriculas_minimas, excluir_sem_concluintes, organizacao, categoria):
    filtradas = filtrar_ofertas(ofertas, modalidades, organizacao, categoria)
    por_codigo = agregar_taxa(filtradas, ["CO_CINE_ROTULO"])
    mascara = por_codigo["QT_MAT_2023"] >= matriculas_minimas
    if excluir_sem_concluintes:
        mascara = mascara & (por_codigo["QT_CONC_2023"] > 0)
    codigos = set(por_codigo.loc[mascara, "CO_CINE_ROTULO"])
    elegiveis = filtradas[filtradas["CO_CINE_ROTULO"].isin(codigos)]
    return {
        **resumir_ofertas(elegiveis),
        "elegiveis": elegiveis,
        "estados": _estados_de_ofertas(elegiveis),
    }


def estados_da_area(recorte, area):
    """Recalcula o mapa com os cursos cuja área predominante, no Brasil, é a escolhida."""
    if not area:
        return recorte["estados"]
    cursos = recorte["cursos"]
    if cursos.empty or "NO_CINE_AREA_GERAL" not in cursos.columns:
        return _estados_vazios()
    nomes = cursos["NO_CINE_AREA_GERAL"].fillna("Sem área")
    codigos = set(cursos.loc[nomes == area, "CO_CINE_ROTULO"])
    ofertas = recorte["elegiveis"]
    return _estados_de_ofertas(ofertas[ofertas["CO_CINE_ROTULO"].isin(codigos)])


def visao_uf(recorte, uf):
    """Recalcula cursos e áreas com as ofertas do estado. A elegibilidade segue a do Brasil."""
    if not uf:
        return recorte
    ofertas = recorte["elegiveis"]
    ofertas = ofertas.loc[ofertas["SG_UF"] == uf].copy()
    return {**recorte, **resumir_ofertas(ofertas)}


def taxas_dos_grupos(ofertas, comparacao):
    """Uma linha por grupo. A taxa divide a soma das saídas pela soma das matrículas."""
    registros = []
    for grupo in comparacao["grupos"]:
        identificador = grupo["id"]
        if ofertas.empty:
            matriculas = 0.0
            evadidos = 0.0
        else:
            matriculas = float(ofertas[f"QT_MAT_{identificador}_2023"].sum())
            evadidos = float(ofertas[f"QT_EVAS_{identificador}"].sum())
        if matriculas <= 0:
            continue
        registros.append(
            {
                "grupo": grupo["rotulo"],
                "id": identificador,
                "cor": grupo["cor"],
                "QT_MAT_2023": matriculas,
                "QT_EVAS": evadidos,
                "TX_EVAS": evadidos / matriculas,
            }
        )
    return pd.DataFrame(
        registros,
        columns=["grupo", "id", "cor", "QT_MAT_2023", "QT_EVAS", "TX_EVAS"],
    )


def estados_dos_grupos(ofertas, comparacao):
    """Taxas por UF. Na diferença, os dois grupos precisam ter matrícula."""
    identificadores = [grupo["id"] for grupo in comparacao["grupos"]]
    colunas = []
    for identificador in identificadores:
        colunas.extend([f"QT_MAT_{identificador}_2023", f"QT_EVAS_{identificador}"])
    base = ofertas[ofertas["SG_UF"].notna()] if not ofertas.empty else ofertas
    if base.empty:
        somas = pd.DataFrame(columns=["SG_UF", "NO_UF", *colunas])
    else:
        somas = base.groupby(["SG_UF", "NO_UF"], dropna=False)[colunas].sum().reset_index()
    for identificador in identificadores:
        matriculas = somas[f"QT_MAT_{identificador}_2023"]
        somas[f"TX_{identificador}"] = somas[f"QT_EVAS_{identificador}"] / matriculas.where(matriculas > 0)
    if comparacao["modo"] == "diferenca":
        esquerda, direita = comparacao["diferenca"]
        somas["diferenca_pp"] = (somas[f"TX_{esquerda}"] - somas[f"TX_{direita}"]) * 100
        return somas
    grupos = []
    taxas = []
    matriculas_grupo = []
    evadidos_grupo = []
    for _, linha in somas.iterrows():
        melhor = None
        for grupo in comparacao["grupos"]:
            identificador = grupo["id"]
            taxa = linha[f"TX_{identificador}"]
            matriculas = linha[f"QT_MAT_{identificador}_2023"]
            if pd.isna(taxa):
                continue
            if melhor is None or taxa > melhor[0] or (taxa == melhor[0] and matriculas > melhor[1]):
                melhor = (taxa, matriculas, grupo["rotulo"], linha[f"QT_EVAS_{identificador}"])
        if melhor is None:
            grupos.append(pd.NA)
            taxas.append(pd.NA)
            matriculas_grupo.append(pd.NA)
            evadidos_grupo.append(pd.NA)
        else:
            grupos.append(melhor[2])
            taxas.append(melhor[0])
            matriculas_grupo.append(melhor[1])
            evadidos_grupo.append(melhor[3])
    somas["grupo"] = grupos
    somas["TX_EVAS"] = taxas
    somas["QT_MAT_2023"] = matriculas_grupo
    somas["QT_EVAS"] = evadidos_grupo
    return somas


def _rotulo_do_curso(ofertas):
    if ofertas.empty:
        return pd.DataFrame(columns=["CO_CINE_ROTULO", "NO_CINE_ROTULO"])
    rotulos = (
        ofertas.groupby("CO_CINE_ROTULO", dropna=False)["NO_CINE_ROTULO"]
        .agg(lambda serie: serie.dropna().iloc[0] if serie.dropna().size else "Sem rótulo")
        .reset_index()
    )
    return rotulos


def _area_predominante(ofertas):
    if ofertas.empty:
        return pd.DataFrame(columns=["CO_CINE_ROTULO", "NO_CINE_AREA_GERAL"])
    totais = (
        ofertas.groupby(["CO_CINE_ROTULO", "NO_CINE_AREA_GERAL"], dropna=False)["QT_MAT_2023"]
        .sum()
        .reset_index()
    )
    escolhida = totais.groupby("CO_CINE_ROTULO", dropna=False)["QT_MAT_2023"].idxmax()
    return totais.loc[escolhida, ["CO_CINE_ROTULO", "NO_CINE_AREA_GERAL"]].reset_index(drop=True)


def com_instituicoes(ofertas, cursos, areas):
    """Conta instituições distintas. Na área, vale a área predominante do curso."""
    cursos = cursos.copy()
    areas = areas.copy()
    if ofertas.empty or cursos.empty:
        cursos["QT_IES"] = 0
        if not areas.empty:
            areas["QT_IES"] = 0
        return cursos, areas
    por_curso = ofertas.groupby("CO_CINE_ROTULO", dropna=False)["CO_IES"].nunique()
    cursos["QT_IES"] = cursos["CO_CINE_ROTULO"].map(por_curso).fillna(0).astype(int)
    predominante = _area_predominante(ofertas).rename(
        columns={"NO_CINE_AREA_GERAL": "area_predominante"}
    )
    com_area = ofertas.merge(predominante, on="CO_CINE_ROTULO", how="left")
    por_area = com_area.groupby("area_predominante", dropna=False)["CO_IES"].nunique()
    areas["QT_IES"] = areas["NO_CINE_AREA_GERAL"].map(por_area).fillna(0).astype(int)
    return cursos, areas


def _colunas_grupo(identificadores):
    colunas = ["QT_MAT_2023", "QT_EVAS"]
    for identificador in identificadores:
        colunas.extend([f"QT_MAT_{identificador}_2023", f"QT_EVAS_{identificador}"])
    return colunas


def _aplicar_taxas(tabela, identificadores):
    matriculas = tabela["QT_MAT_2023"]
    tabela["TX_EVAS"] = tabela["QT_EVAS"] / matriculas.where(matriculas > 0)
    for identificador in identificadores:
        do_grupo = tabela[f"QT_MAT_{identificador}_2023"]
        tabela[f"TX_{identificador}"] = tabela[f"QT_EVAS_{identificador}"] / do_grupo.where(do_grupo > 0)
    return tabela


def taxas_por_entidade(ofertas, identificadores):
    """Soma as contagens por curso e por área predominante, e só depois divide."""
    colunas = _colunas_grupo(identificadores)
    vazios = pd.DataFrame(columns=["CO_CINE_ROTULO", "NO_CINE_ROTULO", "NO_CINE_AREA_GERAL", *colunas])
    if ofertas.empty:
        return vazios, vazios.iloc[0:0]
    cursos = ofertas.groupby("CO_CINE_ROTULO", dropna=False)[colunas].sum().reset_index()
    cursos = cursos.merge(_rotulo_do_curso(ofertas), on="CO_CINE_ROTULO", how="left")
    cursos = cursos.merge(_area_predominante(ofertas), on="CO_CINE_ROTULO", how="left")
    cursos = _aplicar_taxas(cursos, identificadores)
    areas = (
        cursos.groupby("NO_CINE_AREA_GERAL", dropna=False)[colunas].sum().reset_index()
        if not cursos.empty
        else cursos.iloc[0:0]
    )
    if not areas.empty:
        areas = _aplicar_taxas(areas, identificadores)
    return cursos, areas


def _taxa_do_eixo(tabela, identificador):
    if identificador == TAXA_GERAL:
        return tabela["TX_EVAS"] * 100
    return tabela[f"TX_{identificador}"] * 100


def pares_de_grupos(ofertas, id_x, id_y):
    """Uma linha por curso e por área, com as duas taxas em percentual."""
    identificadores = [identificador for identificador in (id_x, id_y) if identificador != TAXA_GERAL]
    cursos, areas = taxas_por_entidade(ofertas, identificadores)

    def preparar(tabela, coluna_nome):
        if tabela.empty:
            return tabela
        plot = tabela.copy()
        plot["NO_CINE_AREA_GERAL"] = plot["NO_CINE_AREA_GERAL"].fillna("Sem área")
        plot["nome"] = plot[coluna_nome]
        plot["taxa_x"] = _taxa_do_eixo(plot, id_x)
        plot["taxa_y"] = _taxa_do_eixo(plot, id_y)
        return plot.dropna(subset=["taxa_x", "taxa_y", "QT_MAT_2023"])

    return preparar(cursos, "NO_CINE_ROTULO"), preparar(areas, "NO_CINE_AREA_GERAL")


def serie_idade(ofertas):
    """Uma linha por área e faixa. Faixa com pouca matrícula fica sem taxa e corta a linha."""
    grupos = COMPARACOES["idade"]["grupos"]
    identificadores = [grupo["id"] for grupo in grupos]
    _, areas = taxas_por_entidade(ofertas, identificadores)
    colunas = ["NO_CINE_AREA_GERAL", "faixa", "ordem", "taxa_pct", "QT_MAT_FAIXA", "QT_MAT_AREA"]
    if areas.empty:
        return pd.DataFrame(columns=colunas)
    registros = []
    for _, linha in areas.iterrows():
        area = linha["NO_CINE_AREA_GERAL"]
        if pd.isna(area):
            area = "Sem área"
        for ordem, grupo in enumerate(grupos):
            matriculas = float(linha[f"QT_MAT_{grupo['id']}_2023"])
            taxa = linha[f"TX_{grupo['id']}"]
            taxa_pct = None if matriculas < MIN_MATRICULAS_FAIXA or pd.isna(taxa) else float(taxa) * 100
            registros.append(
                {
                    "NO_CINE_AREA_GERAL": area,
                    "faixa": grupo["rotulo"],
                    "ordem": ordem,
                    "taxa_pct": taxa_pct,
                    "QT_MAT_FAIXA": matriculas,
                    "QT_MAT_AREA": float(linha["QT_MAT_2023"]),
                }
            )
    return pd.DataFrame(registros, columns=colunas)


def percentil_ponderado(taxas, pesos, proporcao):
    """Taxa do curso em que a matrícula acumulada alcança a proporção pedida."""
    taxas = np.asarray(taxas, dtype=float)
    pesos = np.asarray(pesos, dtype=float)
    ordem = np.argsort(taxas, kind="mergesort")
    taxas = taxas[ordem]
    pesos = pesos[ordem]
    acumulado = np.cumsum(pesos)
    total = float(acumulado[-1]) if len(acumulado) else 0.0
    if total <= 0:
        return np.nan
    indice = int(np.searchsorted(acumulado, proporcao * total, side="left"))
    return float(taxas[min(indice, len(taxas) - 1)])


def quartis_ponderados(cursos):
    """Quartis da taxa por área, pesados pelas matrículas. Bigodes na regra de Tukey."""
    colunas = ["NO_CINE_AREA_GERAL", "q1", "mediana", "q3", "bigode_inf", "bigode_sup"]
    if cursos.empty:
        return pd.DataFrame(columns=colunas)
    registros = []
    base = cursos.dropna(subset=["TX_EVAS", "QT_MAT_2023"]).copy()
    base = base[base["QT_MAT_2023"] > 0]
    base["NO_CINE_AREA_GERAL"] = base["NO_CINE_AREA_GERAL"].fillna("Sem área")
    for area, bloco in base.groupby("NO_CINE_AREA_GERAL", dropna=False):
        taxas = bloco["TX_EVAS"].to_numpy(dtype=float) * 100
        pesos = bloco["QT_MAT_2023"].to_numpy(dtype=float)
        q1 = percentil_ponderado(taxas, pesos, 0.25)
        mediana = percentil_ponderado(taxas, pesos, 0.50)
        q3 = percentil_ponderado(taxas, pesos, 0.75)
        intervalo = q3 - q1
        cerca_inf = q1 - 1.5 * intervalo
        cerca_sup = q3 + 1.5 * intervalo
        dentro = taxas[(taxas >= cerca_inf) & (taxas <= cerca_sup)]
        if len(dentro) == 0:
            bigode_inf, bigode_sup = q1, q3
        else:
            bigode_inf, bigode_sup = float(dentro.min()), float(dentro.max())
        registros.append(
            {
                "NO_CINE_AREA_GERAL": area,
                "q1": q1,
                "mediana": mediana,
                "q3": q3,
                "bigode_inf": bigode_inf,
                "bigode_sup": bigode_sup,
            }
        )
    return pd.DataFrame(registros, columns=colunas)


def inteiro(valor):
    return f"{int(round(valor)):,}".replace(",", ".")


def percentual(valor):
    return f"{valor * 100:.1f}".replace(".", ",") + "%"


def pontos(valor):
    texto = _decimal(abs(valor))
    if valor > 0:
        return "+" + texto + " p.p."
    if valor < 0:
        return "-" + texto + " p.p."
    return "0,0 p.p."


def _escala_areas():
    """A mesma área recebe a mesma cor nos dois gráficos."""
    return alt.Scale(domain=list(CORES_AREA), range=list(CORES_AREA.values()))


def _selecao_de_area():
    """Um clique escolhe a área. Outro clique na mesma solta. Um clique novo troca."""
    return alt.selection_point(
        name="area_clicada",
        fields=["NO_CINE_AREA_GERAL"],
        empty=True,
        toggle=(
            "datum && length(data('area_clicada_store')) && "
            "data('area_clicada_store')[0].values[0] == datum.NO_CINE_AREA_GERAL"
        ),
    )


def grafico_barras(dados, coluna_nome, titulo, selecionavel=False):
    plot = dados.dropna(subset=["TX_EVAS"]).copy()
    plot["NO_CINE_AREA_GERAL"] = plot["NO_CINE_AREA_GERAL"].fillna("Sem área")
    plot["taxa_pct"] = plot["TX_EVAS"] * 100
    plot["rotulo"] = plot["taxa_pct"].map(lambda valor: _decimal(valor) + "%")
    plot["x_nome"] = plot["taxa_pct"].where(plot["taxa_pct"] < 0, 0.0)
    plot["matriculas_txt"] = plot["QT_MAT_2023"].map(inteiro)
    plot["evadidos_txt"] = plot["QT_EVAS"].map(inteiro)
    selecao = _selecao_de_area() if selecionavel else None
    opacidade = alt.condition(selecao, alt.value(1), alt.value(0.28)) if selecao is not None else None
    titulos = {
        "NO_CURSO": "Curso",
        "NO_CINE_ROTULO": "Curso",
        "NO_CINE_AREA_GERAL": "Área do conhecimento",
    }
    dicas = [alt.Tooltip(f"{coluna_nome}:N", title=titulos.get(coluna_nome, coluna_nome))]
    if coluna_nome != "NO_CINE_AREA_GERAL":
        dicas.append(alt.Tooltip("NO_CINE_AREA_GERAL:N", title="Área do conhecimento"))
    dicas.extend(
        [
            alt.Tooltip("taxa_pct:Q", title="Taxa de evasão (%)", format=".1f"),
            alt.Tooltip("matriculas_txt:N", title="Matrículas em 2023"),
            alt.Tooltip("evadidos_txt:N", title="Evadidos estimados"),
        ]
    )
    ordem = plot.sort_values(["taxa_pct", coluna_nome], ascending=[False, True])[coluna_nome].tolist()
    xmin = min(0, float(plot["taxa_pct"].min()))
    xmax = float(plot["taxa_pct"].max())
    folga = max(xmax - xmin, 1) * 0.18
    dominio_x = [xmin, xmax + folga]
    eixo_y = alt.Y(f"{coluna_nome}:N", sort=ordem, axis=None, title=None)

    extra = {"opacity": opacidade} if opacidade is not None else {}
    marca_barra = {"cornerRadiusEnd": 4, "height": 22, "fillOpacity": 1}
    marca_nome = {
        "align": "left",
        "baseline": "middle",
        "dx": 8,
        "fontSize": 12,
        "fontWeight": 600,
        "color": COR_TEXTO_BARRA,
        "limit": alt.expr("max(1, abs(scale('x', datum.taxa_pct) - scale('x', 0)) - 16)"),
    }
    marca_taxa = {"align": "left", "dx": 6, "fontSize": 12, "color": COR_TEXTO}
    if selecionavel:
        marca_barra["cursor"] = "pointer"
        marca_nome["cursor"] = "pointer"
        marca_taxa["cursor"] = "pointer"
    barras = alt.Chart(plot).mark_bar(**marca_barra).encode(
        y=eixo_y,
        x=alt.X(
            "taxa_pct:Q",
            title="Taxa de evasão (%)",
            scale=alt.Scale(domain=dominio_x, nice=False),
            axis=alt.Axis(format=".0f"),
        ),
        color=alt.Color(
            "NO_CINE_AREA_GERAL:N",
            title="Área do conhecimento",
            scale=_escala_areas(),
            legend=None,
        ),
        tooltip=dicas,
        **extra,
    )
    nomes = alt.Chart(plot).mark_text(**marca_nome).encode(
        y=eixo_y,
        x=alt.X("x_nome:Q", scale=alt.Scale(domain=dominio_x, nice=False), axis=None),
        text=f"{coluna_nome}:N",
        tooltip=dicas,
        **extra,
    )
    taxas = alt.Chart(plot).mark_text(**marca_taxa).encode(
        y=eixo_y,
        x=alt.X("taxa_pct:Q", scale=alt.Scale(domain=dominio_x, nice=False), axis=None),
        text="rotulo:N",
        tooltip=dicas,
        **extra,
    )
    if selecao is not None:
        # O nome em cada camada entra no clique. O Altair, sozinho, só liga a primeira.
        barras = barras.properties(name="clique_barra")
        nomes = nomes.properties(name="clique_nome")
        taxas = taxas.properties(name="clique_taxa")
        camadas = (barras + nomes + taxas).add_params(selecao)
        camadas.params[0].views = ["clique_barra", "clique_nome", "clique_taxa"]
    else:
        camadas = barras + nomes + taxas
    if xmin < 0:
        zero = alt.Chart(pd.DataFrame({"taxa_pct": [0]})).mark_rule(
            color="#c5bfb4", strokeDash=[4, 3]
        ).encode(x=alt.X("taxa_pct:Q", scale=alt.Scale(domain=dominio_x, nice=False)))
        camadas = zero + camadas

    return (
        camadas.properties(
            title=alt.Title(titulo, anchor="start", fontSize=16, fontWeight=600),
            width="container",
            height=alt.Step(34),
            padding={"right": 64, "left": 8, "top": 8, "bottom": 4},
            autosize=alt.AutoSizeParams(type="fit-x", contains="padding", resize=True),
        )
        .configure_view(strokeWidth=0)
        .configure_axis(labelFontSize=12, titleFontSize=13)
    )


def grafico_barras_grupos(dados, comparacao, titulo):
    plot = dados.dropna(subset=["TX_EVAS"]).copy()
    plot["taxa_pct"] = plot["TX_EVAS"] * 100
    plot["rotulo_taxa"] = plot["taxa_pct"].map(lambda valor: _decimal(valor) + "%")
    plot["x_nome"] = plot["taxa_pct"].where(plot["taxa_pct"] < 0, 0.0)
    plot["matriculas_txt"] = plot["QT_MAT_2023"].map(inteiro)
    plot["evadidos_txt"] = plot["QT_EVAS"].map(inteiro)
    dicas = [
        alt.Tooltip("grupo:N", title="Grupo"),
        alt.Tooltip("taxa_pct:Q", title="Taxa de evasão (%)", format=".1f"),
        alt.Tooltip("matriculas_txt:N", title="Matrículas em 2023"),
        alt.Tooltip("evadidos_txt:N", title="Evadidos estimados"),
    ]
    ordem = plot.sort_values(["taxa_pct", "grupo"], ascending=[False, True])["grupo"].tolist()
    xmin = min(0, float(plot["taxa_pct"].min()))
    xmax = float(plot["taxa_pct"].max())
    folga = max(xmax - xmin, 1) * 0.18
    dominio_x = [xmin, xmax + folga]
    eixo_y = alt.Y("grupo:N", sort=ordem, axis=None, title=None)
    escala = alt.Scale(
        domain=[grupo["rotulo"] for grupo in comparacao["grupos"]],
        range=[grupo["cor"] for grupo in comparacao["grupos"]],
    )
    barras = alt.Chart(plot).mark_bar(cornerRadiusEnd=4, height=22, fillOpacity=1).encode(
        y=eixo_y,
        x=alt.X(
            "taxa_pct:Q",
            title="Taxa de evasão (%)",
            scale=alt.Scale(domain=dominio_x, nice=False),
            axis=alt.Axis(format=".0f"),
        ),
        color=alt.Color("grupo:N", scale=escala, legend=None),
        tooltip=dicas,
    )
    nomes = alt.Chart(plot).mark_text(
        align="left",
        baseline="middle",
        dx=8,
        fontSize=12,
        fontWeight=600,
        color=COR_TEXTO_BARRA,
        limit=alt.expr("max(1, abs(scale('x', datum.taxa_pct) - scale('x', 0)) - 16)"),
    ).encode(
        y=eixo_y,
        x=alt.X("x_nome:Q", scale=alt.Scale(domain=dominio_x, nice=False), axis=None),
        text="grupo:N",
        tooltip=dicas,
    )
    taxas = alt.Chart(plot).mark_text(align="left", dx=6, fontSize=12, color=COR_TEXTO).encode(
        y=eixo_y,
        x=alt.X("taxa_pct:Q", scale=alt.Scale(domain=dominio_x, nice=False), axis=None),
        text="rotulo_taxa:N",
        tooltip=dicas,
    )
    camadas = barras + nomes + taxas
    if xmin < 0:
        zero = alt.Chart(pd.DataFrame({"taxa_pct": [0]})).mark_rule(
            color="#c5bfb4", strokeDash=[4, 3]
        ).encode(x=alt.X("taxa_pct:Q", scale=alt.Scale(domain=dominio_x, nice=False)))
        camadas = zero + camadas
    return (
        camadas.properties(
            title=alt.Title(titulo, anchor="start", fontSize=16, fontWeight=600),
            width="container",
            height=alt.Step(34),
            padding={"right": 64, "left": 8, "top": 8, "bottom": 4},
            autosize=alt.AutoSizeParams(type="fit-x", contains="padding", resize=True),
        )
        .configure_view(strokeWidth=0)
        .configure_axis(labelFontSize=12, titleFontSize=13)
    )


def _ordem_areas(presentes):
    presentes = set(presentes)
    conhecidas = [area for area in CORES_AREA if area in presentes]
    extras = sorted(presentes - set(conhecidas))
    return conhecidas + extras


def _deslocamento_ponto(codigo):
    """Desvio estável, em pixels, para os cursos não caírem todos no mesmo ponto."""
    valor = zlib.crc32(str(codigo).encode("utf-8")) % 1000
    return valor / 999 * 32 - 16


def _cor_area(legenda):
    return alt.Color(
        "NO_CINE_AREA_GERAL:N",
        title="Área do conhecimento",
        scale=_escala_areas(),
        legend=legenda,
    )


def _legenda_tamanho():
    """Círculos e texto na cor que o painel clareia no modo escuro."""
    return alt.Legend(
        title="Matrículas em 2023",
        symbolFillColor=COR_TEXTO,
        symbolStrokeColor=COR_TEXTO,
        labelColor=COR_TEXTO,
        titleColor=COR_TEXTO,
    )


def _tamanho_matriculas(dados, maior=640):
    """A área do círculo é proporcional às matrículas. O raio segue a raiz quadrada."""
    topo = float(pd.to_numeric(dados["QT_MAT_2023"], errors="coerce").max())
    if pd.isna(topo) or topo <= 0:
        topo = 1.0
    return alt.Size(
        "QT_MAT_2023:Q",
        title="Matrículas em 2023",
        scale=alt.Scale(domain=[0, topo], range=[0, maior], zero=True),
        legend=_legenda_tamanho(),
    )


def _codificacao_tamanho(dados, maior, variavel, fixo=180):
    if variavel:
        return _tamanho_matriculas(dados, maior)
    return alt.value(fixo)


def _fechar_grafico(camadas, titulo, altura, padding=None, largura=None):
    propriedades = {
        "title": alt.Title(titulo, anchor="start", fontSize=16, fontWeight=600),
        "height": altura,
        "padding": padding or {"right": 16, "left": 8, "top": 8, "bottom": 8},
    }
    if largura is None:
        propriedades["width"] = "container"
        propriedades["autosize"] = alt.AutoSizeParams(type="fit-x", contains="padding", resize=True)
    else:
        propriedades["width"] = largura
        propriedades["autosize"] = alt.AutoSizeParams(type="pad", resize=False)
    return (
        camadas.properties(**propriedades)
        .configure_view(strokeWidth=0)
        .configure_axis(labelFontSize=12, titleFontSize=13)
        .configure_legend(labelFontSize=11, titleFontSize=12)
    )


def _dominio_taxa(*series):
    """O eixo da taxa começa em 0 e não passa de 100. O topo acompanha os dados."""
    topos = []
    for serie in series:
        numeros = pd.to_numeric(pd.Series(serie), errors="coerce").dropna()
        if not numeros.empty:
            topos.append(float(numeros.max()))
    if not topos:
        return [0.0, 100.0]
    topo = max(max(topos), 0.0)
    folga = max(topo, 1.0) * 0.06
    return [0.0, min(100.0, topo + folga)]


def grafico_dispersao_volume(dados, eixo_x, por_area, titulo, tamanho_variavel=True):
    plot = dados.dropna(subset=["TX_EVAS"]).copy()
    plot["NO_CINE_AREA_GERAL"] = plot["NO_CINE_AREA_GERAL"].fillna("Sem área")
    plot["taxa_pct"] = plot["TX_EVAS"] * 100
    plot["matriculas_txt"] = plot["QT_MAT_2023"].map(inteiro)
    plot["instituicoes_txt"] = plot["QT_IES"].map(inteiro)
    dominio_taxa = _dominio_taxa(plot["taxa_pct"])
    coluna_x = "QT_IES" if eixo_x == "instituicoes" else "QT_MAT_2023"
    titulo_x = "Instituições" if eixo_x == "instituicoes" else "Matrículas em 2023"
    nome = "NO_CINE_AREA_GERAL" if por_area else "NO_CINE_ROTULO"
    dicas = [alt.Tooltip(f"{nome}:N", title="Área do conhecimento" if por_area else "Curso")]
    if not por_area:
        dicas.append(alt.Tooltip("NO_CINE_AREA_GERAL:N", title="Área do conhecimento"))
    dicas.extend(
        [
            alt.Tooltip("taxa_pct:Q", title="Taxa de evasão (%)", format=".1f"),
            alt.Tooltip("matriculas_txt:N", title="Matrículas em 2023"),
            alt.Tooltip("instituicoes_txt:N", title="Instituições"),
        ]
    )
    destaque = alt.selection_point(
        fields=["NO_CINE_AREA_GERAL"],
        on="click",
        empty="all",
        toggle=True,
    )
    pontos = (
        alt.Chart(plot)
        .mark_circle(clip=True)
        .encode(
            x=alt.X(f"{coluna_x}:Q", title=titulo_x),
            y=alt.Y(
                "taxa_pct:Q",
                title="Taxa de evasão (%)",
                scale=alt.Scale(domain=dominio_taxa, nice=False, zero=True),
            ),
            size=_codificacao_tamanho(plot, 2560, tamanho_variavel),
            color=_cor_area(alt.Legend()),
            opacity=alt.condition(
                destaque,
                alt.value(0.92 if tamanho_variavel else 0.7),
                alt.value(0.15),
            ),
            tooltip=dicas,
        )
        .add_params(destaque)
    )
    return _fechar_grafico(pontos, titulo, 460)


def _eixo_area_horizontal(ordem):
    return alt.Y(
        "NO_CINE_AREA_GERAL:N",
        sort=ordem,
        title=None,
        axis=alt.Axis(labelLimit=280, labelFontSize=12),
    )


def _eixo_taxa(inferior, superior):
    """O mesmo campo em todas as camadas, senão um axis nulo apaga a escala."""
    return alt.X(
        "taxa_pct:Q",
        title="Taxa de evasão (%)",
        scale=alt.Scale(domain=[inferior, superior], nice=False, zero=False),
        axis=alt.Axis(format=".0f", grid=True, labelFontSize=12, titleFontSize=13),
    )


def _faixa_taxa(stats, inicio, fim):
    quadro = stats.loc[:, ["NO_CINE_AREA_GERAL", inicio, fim]].copy()
    return quadro.rename(columns={inicio: "taxa_pct", fim: "taxa_fim"})


def _ponto_taxa(stats, coluna):
    quadro = stats.loc[:, ["NO_CINE_AREA_GERAL", coluna]].copy()
    return quadro.rename(columns={coluna: "taxa_pct"})


def grafico_boxplot_areas(cursos, titulo, tamanho_variavel=True):
    pontos = cursos.dropna(subset=["TX_EVAS"]).copy()
    pontos["NO_CINE_AREA_GERAL"] = pontos["NO_CINE_AREA_GERAL"].fillna("Sem área")
    pontos["taxa_pct"] = pontos["TX_EVAS"] * 100
    pontos["matriculas_txt"] = pontos["QT_MAT_2023"].map(inteiro)
    pontos["deslocamento"] = pontos["CO_CINE_ROTULO"].map(_deslocamento_ponto)
    stats = quartis_ponderados(pontos)
    ordem = _ordem_areas(pontos["NO_CINE_AREA_GERAL"])
    series_taxa = [pontos["taxa_pct"]]
    if not stats.empty:
        series_taxa.append(stats["bigode_sup"])
    inferior, superior = _dominio_taxa(*series_taxa)
    dicas = [
        alt.Tooltip("NO_CINE_ROTULO:N", title="Curso"),
        alt.Tooltip("NO_CINE_AREA_GERAL:N", title="Área do conhecimento"),
        alt.Tooltip("taxa_pct:Q", title="Taxa de evasão (%)", format=".1f"),
        alt.Tooltip("matriculas_txt:N", title="Matrículas em 2023"),
    ]
    bigodes = alt.Chart(_faixa_taxa(stats, "bigode_inf", "bigode_sup")).mark_rule(
        strokeWidth=1.5, clip=True
    ).encode(
        y=_eixo_area_horizontal(ordem),
        x=_eixo_taxa(inferior, superior),
        x2=alt.X2("taxa_fim:Q"),
        color=_cor_area(None),
    )
    inicios = _ponto_taxa(stats, "bigode_inf")
    fins = _ponto_taxa(stats, "bigode_sup")
    topos = pd.concat([inicios, fins], ignore_index=True)
    tampas = alt.Chart(topos).mark_tick(
        orient="vertical", size=16, thickness=1.5, clip=True
    ).encode(
        y=_eixo_area_horizontal(ordem),
        x=_eixo_taxa(inferior, superior),
        color=_cor_area(None),
    )
    caixas = alt.Chart(_faixa_taxa(stats, "q1", "q3")).mark_bar(
        size=28, opacity=0.22, clip=True
    ).encode(
        y=_eixo_area_horizontal(ordem),
        x=_eixo_taxa(inferior, superior),
        x2=alt.X2("taxa_fim:Q"),
        color=_cor_area(None),
    )
    medianas = alt.Chart(_ponto_taxa(stats, "mediana")).mark_tick(
        orient="vertical", size=28, thickness=2.5, clip=True
    ).encode(
        y=_eixo_area_horizontal(ordem),
        x=_eixo_taxa(inferior, superior),
        color=_cor_area(None),
    )
    circulos = alt.Chart(pontos).mark_circle(
        opacity=0.9 if tamanho_variavel else 0.7
    ).encode(
        y=_eixo_area_horizontal(ordem),
        yOffset=alt.YOffset(
            "deslocamento:Q",
            scale=alt.Scale(domain=[-16, 16], range=[-7, 7]),
        ),
        x=_eixo_taxa(inferior, superior),
        size=_codificacao_tamanho(pontos, 640, tamanho_variavel, fixo=45),
        color=_cor_area(None),
        tooltip=dicas,
    )
    return _fechar_grafico(
        bigodes + tampas + caixas + medianas + circulos,
        titulo,
        alt.Step(52),
        padding={"right": 28, "left": 8, "top": 8, "bottom": 28},
    )


LADO_DISPERSAO = 560


def _escala_par(dominio):
    return alt.Scale(domain=dominio, nice=False, zero=False)


def _marca_eixo():
    return alt.Axis(format=".0f", grid=True, labelFontSize=12, titleFontSize=13)


def grafico_dispersao_grupos(dados, titulo, rotulo_x, rotulo_y, por_area, tamanho_variavel=True):
    plot = dados.copy()
    plot["NO_CINE_AREA_GERAL"] = plot["NO_CINE_AREA_GERAL"].fillna("Sem área")
    plot["matriculas_txt"] = plot["QT_MAT_2023"].map(inteiro)
    dominio = _dominio_taxa(plot["taxa_x"], plot["taxa_y"])
    titulo_x = f"Taxa de evasão, {rotulo_x} (%)"
    titulo_y = f"Taxa de evasão, {rotulo_y} (%)"
    dicas = [alt.Tooltip("nome:N", title="Área do conhecimento" if por_area else "Curso")]
    if not por_area:
        dicas.append(alt.Tooltip("NO_CINE_AREA_GERAL:N", title="Área do conhecimento"))
    dicas.extend(
        [
            alt.Tooltip("taxa_x:Q", title=f"{rotulo_x} (%)", format=".1f"),
            alt.Tooltip("taxa_y:Q", title=f"{rotulo_y} (%)", format=".1f"),
            alt.Tooltip("matriculas_txt:N", title="Matrículas em 2023"),
        ]
    )
    destaque = alt.selection_point(
        fields=["NO_CINE_AREA_GERAL"],
        on="click",
        empty="all",
        toggle=True,
    )

    def eixo_x():
        return alt.X(
            "taxa_x:Q",
            title=titulo_x,
            scale=_escala_par(dominio),
            axis=_marca_eixo(),
        )

    def eixo_y():
        return alt.Y(
            "taxa_y:Q",
            title=titulo_y,
            scale=_escala_par(dominio),
            axis=_marca_eixo(),
        )

    diagonal = alt.Chart(pd.DataFrame({"taxa_x": dominio, "taxa_y": dominio})).mark_line(
        strokeDash=[6, 4], color="#c5bfb4", clip=True
    ).encode(x=eixo_x(), y=eixo_y())
    pontos = (
        alt.Chart(plot)
        .mark_circle(clip=True)
        .encode(
            x=eixo_x(),
            y=eixo_y(),
            size=_codificacao_tamanho(plot, 640, tamanho_variavel),
            color=_cor_area(alt.Legend()),
            opacity=alt.condition(
                destaque,
                alt.value(0.92 if tamanho_variavel else 0.7),
                alt.value(0.15),
            ),
            tooltip=dicas,
        )
        .add_params(destaque)
    )
    camadas = diagonal + pontos
    if por_area:
        nomes = alt.Chart(plot).mark_text(
            align="left", dx=8, fontSize=11, color=COR_TEXTO, clip=True
        ).encode(
            x=eixo_x(),
            y=eixo_y(),
            text="nome:N",
            tooltip=dicas,
        )
        camadas = camadas + nomes
    return _fechar_grafico(
        camadas,
        titulo,
        LADO_DISPERSAO,
        largura=LADO_DISPERSAO,
        padding={"right": 16, "left": 8, "top": 8, "bottom": 8},
    )


def grafico_linhas_idade(dados, titulo):
    plot = dados.copy()
    plot["NO_CINE_AREA_GERAL"] = plot["NO_CINE_AREA_GERAL"].fillna("Sem área")
    plot["matriculas_faixa_txt"] = plot["QT_MAT_FAIXA"].map(inteiro)
    plot["matriculas_area_txt"] = plot["QT_MAT_AREA"].map(inteiro)
    ordem = [grupo["rotulo"] for grupo in COMPARACOES["idade"]["grupos"]]
    dominio_taxa = _dominio_taxa(plot["taxa_pct"])
    topo = float(pd.to_numeric(plot["QT_MAT_AREA"], errors="coerce").max())
    if pd.isna(topo) or topo <= 0:
        topo = 1.0
    dicas = [
        alt.Tooltip("NO_CINE_AREA_GERAL:N", title="Área do conhecimento"),
        alt.Tooltip("faixa:N", title="Faixa de idade"),
        alt.Tooltip("taxa_pct:Q", title="Taxa de evasão (%)", format=".1f"),
        alt.Tooltip("matriculas_faixa_txt:N", title="Matrículas na faixa"),
        alt.Tooltip("matriculas_area_txt:N", title="Matrículas na área"),
    ]

    def eixo_x():
        return alt.X("faixa:N", sort=ordem, title="Faixa de idade")

    def eixo_y():
        return alt.Y(
            "taxa_pct:Q",
            title="Taxa de evasão (%)",
            scale=alt.Scale(domain=dominio_taxa, nice=False, zero=True),
        )

    linhas = alt.Chart(plot).mark_line(
        opacity=0.4, clip=True, invalid="break-paths-filter-domains"
    ).encode(
        x=eixo_x(),
        y=eixo_y(),
        color=_cor_area(alt.Legend()),
        strokeWidth=alt.StrokeWidth(
            "QT_MAT_AREA:Q",
            scale=alt.Scale(domain=[0, topo], range=[0, 16], zero=True),
            legend=None,
        ),
        tooltip=dicas,
    )
    visiveis = plot.dropna(subset=["taxa_pct"])
    circulos = alt.Chart(visiveis).mark_circle(size=48, opacity=0.55, clip=True).encode(
        x=eixo_x(),
        y=eixo_y(),
        color=_cor_area(None),
        tooltip=dicas,
    )
    return _fechar_grafico(linhas + circulos, titulo, 460)


def _decimal(valor):
    return f"{valor:.1f}".replace(".", ",")


def _caixa_geojson(geojson):
    longitudes, latitudes = [], []

    def percorrer(coordenadas):
        if coordenadas and isinstance(coordenadas[0], (int, float)):
            longitudes.append(coordenadas[0])
            latitudes.append(coordenadas[1])
            return
        for parte in coordenadas:
            percorrer(parte)

    for feicao in geojson["features"]:
        percorrer(feicao["geometry"]["coordinates"])
    return [[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]]


def nome_uf(geojson, sigla):
    for feicao in geojson["features"]:
        if feicao["properties"]["sigla"] == sigla:
            return feicao["properties"]["name"]
    return sigla


def _ponto_no_anel(lng, lat, anel):
    dentro = False
    if len(anel) < 3:
        return False
    xj, yj = anel[-1][0], anel[-1][1]
    for ponto in anel:
        xi, yi = ponto[0], ponto[1]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            dentro = not dentro
        xj, yj = xi, yi
    return dentro


def _ponto_no_poligono(lng, lat, aneis):
    if not aneis or not _ponto_no_anel(lng, lat, aneis[0]):
        return False
    return all(not _ponto_no_anel(lng, lat, buraco) for buraco in aneis[1:])


def estado_no_ponto(geojson, lat, lng):
    """Sigla do estado que contém o ponto, ou None se o clique caiu fora."""
    if lat is None or lng is None:
        return None
    for feicao in geojson["features"]:
        for poligono in feicao["geometry"]["coordinates"]:
            if _ponto_no_poligono(lng, lat, poligono):
                return feicao["properties"]["sigla"]
    return None


def _caixa_legenda(conteudo):
    return f"""
    <div id="legenda-mapa" style="
        position: fixed; z-index: 9999; left: 16px; bottom: 16px;
        border-radius: 12px;
        padding: 10px 12px 8px; font-family: sans-serif; font-size: 12px;
        box-shadow: 0 1px 2px rgba(20, 34, 43, 0.06);
    ">
        {conteudo}
    </div>
    """


def _marca_cor(cor):
    return (
        "<span style=\""
        "width: 12px; height: 12px; border-radius: 3px; display: inline-block; "
        f"background: {cor}; border: 1px solid {COR_CONTORNO};"
        "\"></span>"
    )


def formatar_metrica_mapa(metrica, valor):
    info = METRICAS_MAPA[metrica]
    texto = inteiro(valor) if info["formato"] == "inteiro" else _decimal(valor)
    return texto + info.get("sufixo", "")


def _legenda_taxa(vmin, vmax, titulo="Taxa de evasão (%)", cores=None, com_sinal=False, inteiros=False):
    paleta = list(cores or CORES_TAXA)
    paradas = ", ".join(paleta)
    meio = (vmin + vmax) / 2

    def marca(valor):
        if inteiros:
            return inteiro(valor)
        texto = _decimal(valor)
        if com_sinal and valor > 0:
            return "+" + texto
        return texto

    largura = 300 if inteiros else 168
    return _caixa_legenda(
        f"""
        <div style="font-weight: 650; margin-bottom: 6px;">{titulo}</div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div>
                <div style="
                    width: {largura}px; height: 10px; border-radius: 999px;
                    background: linear-gradient(to right, {paradas});
                "></div>
                <div style="display: flex; justify-content: space-between; margin-top: 3px; font-size: 11px;">
                    <span>{marca(vmin)}</span>
                    <span>{marca(meio)}</span>
                    <span>{marca(vmax)}</span>
                </div>
            </div>
            <div style="width: 1px; align-self: stretch; background: color-mix(in srgb, currentColor 18%, transparent);"></div>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 11px;">
                {_marca_cor(COR_SEM_DADOS)}
                sem dados
            </div>
        </div>
        """
    )


def _legenda_categorias(grupos):
    linhas = []
    for grupo in grupos:
        linhas.append(
            "<div style=\"display: flex; align-items: center; gap: 6px; margin-top: 4px;\">"
            f"{_marca_cor(grupo['cor'])}<span>{grupo['rotulo']}</span></div>"
        )
    linhas.append(
        "<div style=\"display: flex; align-items: center; gap: 6px; margin-top: 4px;\">"
        f"{_marca_cor(COR_SEM_DADOS)}<span>sem dados</span></div>"
    )
    miolo = "".join(linhas)
    return _caixa_legenda(
        f"<div style=\"font-weight: 650; margin-bottom: 2px;\">Maior taxa de evasão</div>{miolo}"
    )


def _malha_estados(geojson):
    limites = copy.deepcopy(geojson)
    siglas = pd.DataFrame(
        {
            "SG_UF": [feicao["properties"]["sigla"] for feicao in limites["features"]],
            "nome_estado": [feicao["properties"]["name"] for feicao in limites["features"]],
        }
    )
    return limites, siglas


def _texto_ou_traco(valor, formatar):
    if pd.isna(valor):
        return "—"
    return formatar(valor)


def _montar_mapa(limites, uf_selecionada, legenda_html, campos, aliases):
    mapa = folium.Map(
        location=[-14.2, -51.9],
        zoom_start=4,
        tiles=None,
        zoom_control=False,
        attribution_control=False,
        dragging=False,
        scrollWheelZoom=False,
        doubleClickZoom=False,
        touchZoom=False,
        boxZoom=False,
        keyboard=False,
    )
    mapa.get_root().html.add_child(
        folium.Element(
            "<style>"
            ".leaflet-container { background: var(--background-color, #f6f4ef); }"
            ".leaflet-interactive { cursor: pointer; }"
            "#legenda-mapa {"
            "  background: var(--secondary-background-color, #ffffff);"
            "  color: var(--text-color, #14222b);"
            "  border: 1px solid color-mix(in srgb, var(--text-color, #14222b) 14%, transparent);"
            "}"
            "</style>"
        )
    )
    if legenda_html:
        mapa.get_root().html.add_child(folium.Element(legenda_html))

    def estilo(feicao):
        selecionado = uf_selecionada and feicao["properties"]["sigla"] == uf_selecionada
        return {
            "fillColor": feicao["properties"]["cor"],
            "color": COR_SELECAO if selecionado else COR_CONTORNO,
            "weight": 6 if selecionado else 1.1,
            "fillOpacity": 1,
        }

    def destaque(feicao):
        selecionado = uf_selecionada and feicao["properties"]["sigla"] == uf_selecionada
        return {
            "weight": 7 if selecionado else 2.4,
            "color": COR_SELECAO if selecionado else COR_TEXTO,
            "fillOpacity": 1,
        }

    folium.GeoJson(
        limites,
        style_function=estilo,
        highlight_function=destaque,
        tooltip=folium.GeoJsonTooltip(fields=campos, aliases=aliases, sticky=True),
    ).add_to(mapa)
    mapa.fit_bounds(_caixa_geojson(limites), padding=(16, 16))
    mapa.add_child(_LigarCliqueEstado())
    mapa.add_child(_TrazerEstadoFrente(uf_selecionada))
    mapa.add_child(_EncaixarNoTopo())
    mapa.add_child(_TravarZoom())
    return mapa


def mapa_estados(estados, geojson, uf_selecionada=None, metrica="taxa"):
    """Pinta cada estado pela métrica escolhida."""
    info = METRICAS_MAPA[metrica]
    limites, siglas = _malha_estados(geojson)
    dados = siglas.merge(estados, on="SG_UF", how="left")
    dados["taxa_pct"] = dados["TX_EVAS"] * 100
    for coluna_extra in ("QT_IES", "QT_MAT_2023", "MAT_POR_MIL", "IES_POR_MILHAO", "PCT_MUN_IES"):
        if coluna_extra not in dados.columns:
            dados[coluna_extra] = pd.NA

    coluna = info["coluna"]
    por_sigla = {campo: dados.set_index("SG_UF")[campo].to_dict() for campo in (
        "taxa_pct",
        "QT_MAT_2023",
        "QT_IES",
        "MAT_POR_MIL",
        "IES_POR_MILHAO",
        "PCT_MUN_IES",
    )}
    coloridos = dados.dropna(subset=[coluna])
    escala = None
    if not coloridos.empty:
        valores = coloridos[coluna].astype(float)
        vmin = float(valores.min())
        vmax = float(valores.max())
        if vmin == vmax:
            vmin -= 0.5
            vmax += 0.5
        escala = cm.LinearColormap(CORES_TAXA, vmin=vmin, vmax=vmax)

    for feicao in limites["features"]:
        sigla = feicao["properties"]["sigla"]
        taxa = por_sigla["taxa_pct"].get(sigla)
        valor = por_sigla[coluna].get(sigla)
        if escala is not None and pd.notna(valor):
            feicao["properties"]["cor"] = escala.rgb_hex_str(float(valor))
        else:
            feicao["properties"]["cor"] = COR_SEM_DADOS
        feicao["properties"]["taxa"] = _decimal(taxa) + "%" if pd.notna(taxa) else "sem dados"
        feicao["properties"]["mat_por_mil"] = _texto_ou_traco(por_sigla["MAT_POR_MIL"].get(sigla), _decimal)
        feicao["properties"]["ies_por_milhao"] = _texto_ou_traco(
            por_sigla["IES_POR_MILHAO"].get(sigla), _decimal
        )
        feicao["properties"]["municipios"] = _texto_ou_traco(
            por_sigla["PCT_MUN_IES"].get(sigla), lambda v: _decimal(v) + "%"
        )
        feicao["properties"]["matriculas"] = _texto_ou_traco(por_sigla["QT_MAT_2023"].get(sigla), inteiro)
        feicao["properties"]["instituicoes"] = _texto_ou_traco(por_sigla["QT_IES"].get(sigla), inteiro)

    legenda = (
        _legenda_taxa(
            escala.vmin,
            escala.vmax,
            titulo=info["titulo_legenda"],
            inteiros=info["formato"] == "inteiro",
        )
        if escala is not None
        else None
    )
    mapa = _montar_mapa(
        limites,
        uf_selecionada,
        legenda,
        ["name", "sigla", "taxa", "mat_por_mil", "ies_por_milhao", "municipios", "matriculas", "instituicoes"],
        [
            "Estado:",
            "UF:",
            "Taxa de evasão:",
            "Matrículas por mil hab.:",
            "Instituições por milhão:",
            "Municípios com IES:",
            "Matrículas em 2023:",
            "Instituições:",
        ],
    )
    return mapa, dados.dropna(subset=[coluna])


def mapa_grupos(por_estado, geojson, comparacao, uf_selecionada=None):
    limites, siglas = _malha_estados(geojson)
    dados = siglas.merge(por_estado, on="SG_UF", how="left")
    if comparacao["modo"] == "diferenca":
        return _mapa_diferenca(limites, dados, comparacao, uf_selecionada)
    return _mapa_categoria(limites, dados, comparacao, uf_selecionada)


def _mapa_diferenca(limites, dados, comparacao, uf_selecionada):
    esquerda, direita = comparacao["diferenca"]
    rotulos = {grupo["id"]: grupo["rotulo"] for grupo in comparacao["grupos"]}
    dados = dados.copy()
    dados["taxa_esquerda"] = dados[f"TX_{esquerda}"] * 100
    dados["taxa_direita"] = dados[f"TX_{direita}"] * 100
    coloridos = dados.dropna(subset=["diferenca_pp"])
    escala = None
    if not coloridos.empty:
        limite = float(coloridos["diferenca_pp"].abs().max())
        if limite == 0:
            limite = 0.5
        escala = cm.LinearColormap(CORES_DIFERENCA, vmin=-limite, vmax=limite)

    diferenca_por_sigla = dados.set_index("SG_UF")["diferenca_pp"].to_dict()
    taxa_esquerda = dados.set_index("SG_UF")[f"TX_{esquerda}"].to_dict()
    taxa_direita = dados.set_index("SG_UF")[f"TX_{direita}"].to_dict()
    matriculas_esquerda = dados.set_index("SG_UF")[f"QT_MAT_{esquerda}_2023"].to_dict()
    matriculas_direita = dados.set_index("SG_UF")[f"QT_MAT_{direita}_2023"].to_dict()
    for feicao in limites["features"]:
        sigla = feicao["properties"]["sigla"]
        diferenca = diferenca_por_sigla.get(sigla)
        if escala is not None and pd.notna(diferenca):
            feicao["properties"]["cor"] = escala.rgb_hex_str(float(diferenca))
            feicao["properties"]["diferenca"] = pontos(float(diferenca))
        else:
            feicao["properties"]["cor"] = COR_SEM_DADOS
            feicao["properties"]["diferenca"] = "sem dados"
        feicao["properties"]["taxa_esquerda"] = _texto_ou_traco(taxa_esquerda.get(sigla), percentual)
        feicao["properties"]["taxa_direita"] = _texto_ou_traco(taxa_direita.get(sigla), percentual)
        feicao["properties"]["mat_esquerda"] = _texto_ou_traco(matriculas_esquerda.get(sigla), inteiro)
        feicao["properties"]["mat_direita"] = _texto_ou_traco(matriculas_direita.get(sigla), inteiro)

    legenda = None
    if escala is not None:
        legenda = _legenda_taxa(
            escala.vmin,
            escala.vmax,
            titulo=comparacao["legenda"],
            cores=CORES_DIFERENCA,
            com_sinal=True,
        )
    mapa = _montar_mapa(
        limites,
        uf_selecionada,
        legenda,
        ["name", "sigla", "diferenca", "taxa_esquerda", "taxa_direita", "mat_esquerda", "mat_direita"],
        [
            "Estado:",
            "UF:",
            "Diferença:",
            f"Taxa {rotulos[esquerda]}:",
            f"Taxa {rotulos[direita]}:",
            f"Matrículas {rotulos[esquerda]}:",
            f"Matrículas {rotulos[direita]}:",
        ],
    )
    return mapa, dados.dropna(subset=["diferenca_pp"])


def _mapa_categoria(limites, dados, comparacao, uf_selecionada):
    cor_por_grupo = {grupo["rotulo"]: grupo["cor"] for grupo in comparacao["grupos"]}
    grupo_por_sigla = dados.set_index("SG_UF")["grupo"].to_dict()
    taxa_por_sigla = dados.set_index("SG_UF")["TX_EVAS"].to_dict()
    matriculas_por_sigla = dados.set_index("SG_UF")["QT_MAT_2023"].to_dict()
    for feicao in limites["features"]:
        sigla = feicao["properties"]["sigla"]
        grupo = grupo_por_sigla.get(sigla)
        taxa = taxa_por_sigla.get(sigla)
        if pd.notna(grupo) and pd.notna(taxa):
            feicao["properties"]["cor"] = cor_por_grupo[grupo]
            feicao["properties"]["grupo"] = grupo
            feicao["properties"]["taxa"] = percentual(float(taxa))
        else:
            feicao["properties"]["cor"] = COR_SEM_DADOS
            feicao["properties"]["grupo"] = "sem dados"
            feicao["properties"]["taxa"] = "sem dados"
        feicao["properties"]["matriculas"] = _texto_ou_traco(matriculas_por_sigla.get(sigla), inteiro)

    dados = dados.copy()
    dados["taxa_pct"] = dados["TX_EVAS"] * 100
    mapa = _montar_mapa(
        limites,
        uf_selecionada,
        _legenda_categorias(comparacao["grupos"]),
        ["name", "sigla", "grupo", "taxa", "matriculas"],
        ["Estado:", "UF:", "Grupo com maior taxa:", "Taxa de evasão:", "Matrículas em 2023:"],
    )
    return mapa, dados.dropna(subset=["TX_EVAS"])


class _LigarCliqueEstado(MacroElement):
    """Guarda a sigla do estado clicado para o painel ler no retorno do mapa."""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
            var mapa = {{ this._parent.get_name() }};
            function ligarClique(camada) {
                camada.on("click", function (evento) {
                    var alvo = evento.target || camada;
                    var feicao = (alvo && alvo.feature) || (evento.layer && evento.layer.feature) || camada.feature;
                    var ponto = evento.latlng;
                    if (!feicao || !feicao.properties || !ponto || !window.__GLOBAL_DATA__) {
                        return;
                    }
                    window.__GLOBAL_DATA__.last_active_drawing = {
                        type: "Feature",
                        properties: feicao.properties,
                        click_lat: ponto.lat,
                        click_lng: ponto.lng
                    };
                });
                if (camada.eachLayer) {
                    camada.eachLayer(ligarClique);
                }
            }
            mapa.eachLayer(ligarClique);
        {% endmacro %}
        """
    )


class _TrazerEstadoFrente(MacroElement):
    """Deixa a borda do estado selecionado por cima dos vizinhos."""

    def __init__(self, sigla):
        super().__init__()
        self._name = "TrazerEstadoFrente"
        self.sigla = sigla or ""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
            var mapa = {{ this._parent.get_name() }};
            var sigla = {{ this.sigla|tojson }};
            function trazer(camada) {
                var feicao = camada.feature;
                if (feicao && feicao.properties && feicao.properties.sigla === sigla && camada.bringToFront) {
                    camada.bringToFront();
                }
                if (camada.eachLayer) {
                    camada.eachLayer(trazer);
                }
            }
            if (sigla) {
                mapa.eachLayer(trazer);
            }
        {% endmacro %}
        """
    )


class _EncaixarNoTopo(MacroElement):
    """Sobe o país até a borda de cima e corta a altura no fim da legenda."""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
            var mapa = {{ this._parent.get_name() }};
            var ultimoTamanho = "";
            var encaixando = false;
            var pendente = false;
            function encaixar() {
                if (encaixando) {
                    pendente = true;
                    return;
                }
                encaixando = true;
                try {
                    mapa.invalidateSize({animate: false, pan: false});
                    var tamanho = mapa.getSize();
                    if (!tamanho || tamanho.x < 20 || tamanho.y < 50) {
                        return;
                    }
                    var assinatura = tamanho.x + "x" + tamanho.y;
                    if (assinatura === ultimoTamanho && isFinite(mapa.getZoom())) {
                        return;
                    }
                    var limites = null;
                    mapa.eachLayer(function (camada) {
                        if (!camada.getBounds) {
                            return;
                        }
                        try {
                            var caixa = camada.getBounds();
                            if (caixa.isValid()) {
                                limites = limites ? limites.extend(caixa) : caixa;
                            }
                        } catch (erro) {}
                    });
                    if (!limites) {
                        return;
                    }
                    ultimoTamanho = assinatura;
                    mapa.options.minZoom = 0;
                    mapa.options.maxZoom = 18;
                    mapa.setMinZoom(0);
                    mapa.setMaxZoom(18);
                    if (!isFinite(mapa.getZoom())) {
                        mapa.setView([-15.8, -47.9], 4, {animate: false});
                    }
                    mapa.fitBounds(limites, {padding: [16, 16], animate: false});
                    var topo = mapa.latLngToContainerPoint(limites.getNorthWest()).y;
                    if (topo > 8) {
                        mapa.panBy([0, topo - 8], {animate: false});
                    }
                    var sul = mapa.latLngToContainerPoint(limites.getSouthEast()).y;
                    var legenda = document.getElementById("legenda-mapa");
                    if (legenda && !legenda.offsetHeight) {
                        ultimoTamanho = "";
                        return;
                    }
                    var altura = Math.ceil(sul + 16);
                    if (legenda) {
                        var abaixo = sul + 12;
                        legenda.style.bottom = "auto";
                        legenda.style.top = Math.max(8, abaixo) + "px";
                        altura = Math.ceil(abaixo + legenda.offsetHeight + 16);
                    }
                    var caixa = document.getElementById("map_div") || mapa.getContainer();
                    if (caixa && altura + 8 < tamanho.y) {
                        caixa.style.height = altura + "px";
                        var moldura = document.getElementById("parent");
                        if (moldura) {
                            moldura.style.height = altura + "px";
                        }
                        document.body.style.height = altura + "px";
                        document.documentElement.style.height = altura + "px";
                        mapa.invalidateSize({animate: false, pan: false});
                        if (window.Streamlit && window.Streamlit.setFrameHeight) {
                            window.Streamlit.setFrameHeight(altura);
                        }
                        ultimoTamanho = "";
                        setTimeout(encaixar, 0);
                        return;
                    }
                    var nivel = mapa.getZoom();
                    if (isFinite(nivel)) {
                        mapa.setMinZoom(nivel);
                        mapa.setMaxZoom(nivel);
                    }
                } finally {
                    encaixando = false;
                    if (pendente) {
                        pendente = false;
                        encaixar();
                    }
                }
            }
            mapa.whenReady(function () {
                setTimeout(encaixar, 0);
                setTimeout(encaixar, 200);
                var alvo = mapa.getContainer();
                if (window.ResizeObserver && alvo) {
                    new ResizeObserver(function () { encaixar(); }).observe(alvo);
                }
                if (window.IntersectionObserver && alvo) {
                    new IntersectionObserver(function (entradas) {
                        for (var i = 0; i < entradas.length; i++) {
                            if (entradas[i].isIntersecting && entradas[i].intersectionRect.height > 50) {
                                encaixar();
                                return;
                            }
                        }
                    }).observe(alvo);
                }
                window.addEventListener("resize", encaixar);
            });
        {% endmacro %}
        """
    )


class _TravarZoom(MacroElement):
    """Fixa o zoom calculado pelo enquadramento dos estados."""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
            var mapa = {{ this._parent.get_name() }};
            var nivel = mapa.getZoom();
            if (isFinite(nivel)) {
                mapa.setMinZoom(nivel);
                mapa.setMaxZoom(nivel);
            }
        {% endmacro %}
        """
    )
