"""Taxa de evasão entre os censos de 2023 e 2024 e os gráficos do painel."""

from pathlib import Path
import copy
import json

import altair as alt
import branca.colormap as cm
import folium
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


def _grupo(identificador, rotulo, cor):
    return {"id": identificador, "rotulo": rotulo, "cor": cor}


COMPARACOES = {
    "sexo": {
        "rotulo": "Mulheres e homens",
        "modo": "diferenca",
        "texto_diferenca": "mulheres − homens",
        "legenda": "Mulheres − homens (p.p.)",
        "grupos": [
            _grupo("FEM", "Mulheres", "#9d3c66"),
            _grupo("MASC", "Homens", "#1d4e89"),
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
            _grupo("DEFICIENTE", "Com deficiência", "#7e22ce"),
            _grupo("SEM_DEFICIENTE", "Sem deficiência", "#0f766e"),
        ],
        "diferenca": ("DEFICIENTE", "SEM_DEFICIENTE"),
    },
    "cotas": {
        "rotulo": "Alunos cotistas ou não cotistas",
        "modo": "diferenca",
        "texto_diferenca": "cotistas − não cotistas",
        "legenda": "Cotistas − não cotistas (p.p.)",
        "grupos": [
            _grupo("RESERVA_VAGA", "Cotistas", "#0e7490"),
            _grupo("SEM_RESERVA", "Não cotistas", "#a16207"),
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
            _grupo("PROCESCPUBLICA", "Escola pública", "#1d4e89"),
            _grupo("PROCESCPRIVADA", "Escola particular", "#c2410c"),
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


def preparar_recorte(ofertas, modalidades, matriculas_minimas, excluir_sem_concluintes, organizacao, categoria):
    filtradas = filtrar_ofertas(ofertas, modalidades, organizacao, categoria)
    por_codigo = agregar_taxa(filtradas, ["CO_CINE_ROTULO"])
    mascara = por_codigo["QT_MAT_2023"] >= matriculas_minimas
    if excluir_sem_concluintes:
        mascara = mascara & (por_codigo["QT_CONC_2023"] > 0)
    codigos = set(por_codigo.loc[mascara, "CO_CINE_ROTULO"])
    elegiveis = filtradas[filtradas["CO_CINE_ROTULO"].isin(codigos)]
    estados = agregar_taxa(elegiveis[elegiveis["SG_UF"].notna()], ["SG_UF", "NO_UF"])
    return {
        **resumir_ofertas(elegiveis),
        "elegiveis": elegiveis,
        "estados": estados,
    }


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


def grafico_barras(dados, coluna_nome, titulo):
    plot = dados.dropna(subset=["TX_EVAS"]).copy()
    plot["NO_CINE_AREA_GERAL"] = plot["NO_CINE_AREA_GERAL"].fillna("Sem área")
    plot["taxa_pct"] = plot["TX_EVAS"] * 100
    plot["rotulo"] = plot["taxa_pct"].map(lambda valor: _decimal(valor) + "%")
    plot["x_nome"] = plot["taxa_pct"].where(plot["taxa_pct"] < 0, 0.0)
    plot["matriculas_txt"] = plot["QT_MAT_2023"].map(inteiro)
    plot["evadidos_txt"] = plot["QT_EVAS"].map(inteiro)
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

    barras = alt.Chart(plot).mark_bar(cornerRadiusEnd=4, height=22, fillOpacity=1).encode(
        y=eixo_y,
        x=alt.X(
            "taxa_pct:Q",
            title="Taxa de evasão (%)",
            scale=alt.Scale(domain=dominio_x, nice=False),
            axis=alt.Axis(format=".0f", titleColor=COR_TEXTO, labelColor=COR_TEXTO),
        ),
        color=alt.Color(
            "NO_CINE_AREA_GERAL:N",
            title="Área do conhecimento",
            scale=_escala_areas(),
            legend=None,
        ),
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
        text=f"{coluna_nome}:N",
        tooltip=dicas,
    )
    taxas = alt.Chart(plot).mark_text(align="left", dx=6, fontSize=12, color=COR_TEXTO).encode(
        y=eixo_y,
        x=alt.X("taxa_pct:Q", scale=alt.Scale(domain=dominio_x, nice=False), axis=None),
        text="rotulo:N",
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
            title=alt.Title(titulo, anchor="start", color=COR_TEXTO, fontSize=16, fontWeight=600),
            width="container",
            height=alt.Step(34),
            padding={"right": 64, "left": 8, "top": 8, "bottom": 4},
            autosize=alt.AutoSizeParams(type="fit-x", contains="padding", resize=True),
        )
        .configure_view(strokeWidth=0)
        .configure_axis(gridColor="#efeae3", domainColor="#ddd6cc", tickColor="#ddd6cc", labelFontSize=12, titleFontSize=13)
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
            axis=alt.Axis(format=".0f", titleColor=COR_TEXTO, labelColor=COR_TEXTO),
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
            title=alt.Title(titulo, anchor="start", color=COR_TEXTO, fontSize=16, fontWeight=600),
            width="container",
            height=alt.Step(34),
            padding={"right": 64, "left": 8, "top": 8, "bottom": 4},
            autosize=alt.AutoSizeParams(type="fit-x", contains="padding", resize=True),
        )
        .configure_view(strokeWidth=0)
        .configure_axis(gridColor="#efeae3", domainColor="#ddd6cc", tickColor="#ddd6cc", labelFontSize=12, titleFontSize=13)
    )


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
    <div style="
        position: fixed; z-index: 9999; left: 16px; bottom: 16px;
        background: #ffffff; color: {COR_TEXTO};
        border: 1px solid rgba(20, 34, 43, 0.08); border-radius: 12px;
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


def _legenda_taxa(vmin, vmax, titulo="Taxa de evasão (%)", cores=None, com_sinal=False):
    paleta = list(cores or CORES_TAXA)
    paradas = ", ".join(paleta)
    meio = (vmin + vmax) / 2

    def marca(valor):
        texto = _decimal(valor)
        if com_sinal and valor > 0:
            return "+" + texto
        return texto

    return _caixa_legenda(
        f"""
        <div style="font-weight: 650; margin-bottom: 6px;">{titulo}</div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div>
                <div style="
                    width: 168px; height: 10px; border-radius: 999px;
                    background: linear-gradient(to right, {paradas});
                "></div>
                <div style="display: flex; justify-content: space-between; margin-top: 3px; font-size: 11px;">
                    <span>{marca(vmin)}</span>
                    <span>{marca(meio)}</span>
                    <span>{marca(vmax)}</span>
                </div>
            </div>
            <div style="width: 1px; align-self: stretch; background: rgba(20, 34, 43, 0.08);"></div>
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
        scrollWheelZoom=False,
        doubleClickZoom=False,
        touchZoom=False,
        boxZoom=False,
        keyboard=False,
    )
    mapa.get_root().html.add_child(
        folium.Element(
            "<style>"
            f".leaflet-container {{ background: {COR_FUNDO_MAPA}; }}"
            ".leaflet-interactive { cursor: pointer; }"
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
    mapa.add_child(_TravarZoom())
    return mapa


def mapa_estados(estados, geojson, uf_selecionada=None):
    limites, siglas = _malha_estados(geojson)
    dados = siglas.merge(estados, on="SG_UF", how="left")
    dados["taxa_pct"] = dados["TX_EVAS"] * 100

    taxa_por_sigla = dados.set_index("SG_UF")["taxa_pct"].to_dict()
    matriculas_por_sigla = dados.set_index("SG_UF")["QT_MAT_2023"].to_dict()
    coloridos = dados.dropna(subset=["taxa_pct"])
    escala = None
    if not coloridos.empty:
        valores = coloridos["taxa_pct"].astype(float)
        vmin = float(valores.min())
        vmax = float(valores.max())
        if vmin == vmax:
            vmin -= 0.5
            vmax += 0.5
        escala = cm.LinearColormap(CORES_TAXA, vmin=vmin, vmax=vmax)

    for feicao in limites["features"]:
        sigla = feicao["properties"]["sigla"]
        taxa = taxa_por_sigla.get(sigla)
        matriculas = matriculas_por_sigla.get(sigla)
        if escala is not None and pd.notna(taxa):
            feicao["properties"]["cor"] = escala.rgb_hex_str(float(taxa))
            feicao["properties"]["taxa"] = _decimal(taxa) + "%"
        else:
            feicao["properties"]["cor"] = COR_SEM_DADOS
            feicao["properties"]["taxa"] = "sem dados"
        feicao["properties"]["matriculas"] = inteiro(matriculas) if pd.notna(matriculas) else "—"

    legenda = _legenda_taxa(escala.vmin, escala.vmax) if escala is not None else None
    mapa = _montar_mapa(
        limites,
        uf_selecionada,
        legenda,
        ["name", "sigla", "taxa", "matriculas"],
        ["Estado:", "UF:", "Taxa de evasão:", "Matrículas em 2023:"],
    )
    return mapa, dados.dropna(subset=["TX_EVAS"])


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


class _TravarZoom(MacroElement):
    """Fixa o zoom calculado pelo enquadramento dos estados."""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
            var mapa = {{ this._parent.get_name() }};
            var nivel = mapa.getZoom();
            mapa.setMinZoom(nivel);
            mapa.setMaxZoom(nivel);
        {% endmacro %}
        """
    )
