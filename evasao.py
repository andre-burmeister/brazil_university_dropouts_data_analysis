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

    esquerda = esquerda.rename(
        columns={"QT_MAT": "QT_MAT_2023", "QT_CONC": "QT_CONC_2023"}
    )
    direita = direita.rename(
        columns={"QT_MAT": "QT_MAT_2024", "QT_ING": "QT_ING_2024"}
    )
    pares = esquerda.merge(
        direita[CHAVES_OFERTA + ["QT_MAT_2024", "QT_ING_2024"]],
        on=CHAVES_OFERTA,
        how="inner",
    )
    pares["CO_MUNICIPIO"] = pares["CO_MUNICIPIO"].replace(-1, pd.NA)
    quantidades = ["QT_MAT_2023", "QT_CONC_2023", "QT_MAT_2024", "QT_ING_2024"]
    pares[quantidades] = pares[quantidades].fillna(0)
    pares["QT_EVAS"] = (
        pares["QT_MAT_2023"]
        - pares["QT_CONC_2023"]
        - pares["QT_MAT_2024"]
        + pares["QT_ING_2024"]
    )
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


def _legenda_taxa(vmin, vmax):
    paradas = ", ".join(CORES_TAXA)
    meio = (vmin + vmax) / 2
    return f"""
    <div style="
        position: fixed; z-index: 9999; left: 16px; bottom: 16px;
        background: #ffffff; color: {COR_TEXTO};
        border: 1px solid rgba(20, 34, 43, 0.08); border-radius: 12px;
        padding: 10px 12px 8px; font-family: sans-serif; font-size: 12px;
        box-shadow: 0 1px 2px rgba(20, 34, 43, 0.06);
    ">
        <div style="font-weight: 650; margin-bottom: 6px;">Taxa de evasão (%)</div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div>
                <div style="
                    width: 168px; height: 10px; border-radius: 999px;
                    background: linear-gradient(to right, {paradas});
                "></div>
                <div style="display: flex; justify-content: space-between; margin-top: 3px; font-size: 11px;">
                    <span>{_decimal(vmin)}</span>
                    <span>{_decimal(meio)}</span>
                    <span>{_decimal(vmax)}</span>
                </div>
            </div>
            <div style="width: 1px; align-self: stretch; background: rgba(20, 34, 43, 0.08);"></div>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 11px;">
                <span style="
                    width: 12px; height: 12px; border-radius: 3px; display: inline-block;
                    background: {COR_SEM_DADOS}; border: 1px solid {COR_CONTORNO};
                "></span>
                sem dados
            </div>
        </div>
    </div>
    """


def mapa_estados(estados, geojson, uf_selecionada=None):
    limites = copy.deepcopy(geojson)
    siglas = pd.DataFrame(
        {
            "SG_UF": [feicao["properties"]["sigla"] for feicao in limites["features"]],
            "nome_estado": [feicao["properties"]["name"] for feicao in limites["features"]],
        }
    )
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
    if escala is not None:
        mapa.get_root().html.add_child(folium.Element(_legenda_taxa(escala.vmin, escala.vmax)))

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
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "sigla", "taxa", "matriculas"],
            aliases=["Estado:", "UF:", "Taxa de evasão:", "Matrículas em 2023:"],
            sticky=True,
        ),
    ).add_to(mapa)
    mapa.fit_bounds(_caixa_geojson(limites), padding=(16, 16))
    mapa.add_child(_LigarCliqueEstado())
    mapa.add_child(_TrazerEstadoFrente(uf_selecionada))
    mapa.add_child(_TravarZoom())
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
