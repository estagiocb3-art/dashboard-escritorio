# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ============================================================
# CONFIGURACAO
# ============================================================
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3OTQ1OTE1MzYsImp0aSI6IjFmMDliYjI0LTI3Y2QtNDVjMC05MmNjLTAwMzI4MjYxZWE0YyIsInN1YiI6MzA3MTY4MzMwLCJ1c2VyIjp7ImlkIjozMDcxNjgzMzAsImVtYWlsIjoiZXN0YWdpby5jYi4zQGdtYWlsLmNvbSJ9LCJ1c2VyX3R5cGUiOiJhdXRoZW50aWNhdGVkIn0.ksKaVjWVzgtx0Nn7pEgpT_Fs-fCt2d0IE-XIf9Ko399GN3swfkV-HmVxBORB33-WaRIX-3XLoJAkTn3SzJKIrA"

HEADERS = {
    "Authorization": f"Bearer {PIPEFY_TOKEN}",
    "Content-Type": "application/json"
}

FUNIL_PIPE_ID = "305786823"
CAPTADORES = ["Ruan Auzier", "Welison Capao", "Samara Barbosa", "Debora"]

CORES = {
    "Ruan Auzier":    "#00BFFF",
    "Welison Capao":  "#FFD700",
    "Samara Barbosa": "#FF69B4",
    "Debora":         "#98FB98",
}

MEDALHAS = ["🥇", "🥈", "🥉", "4️⃣"]

# ============================================================
# BUSCA PIPEFY
# ============================================================
def buscar_contratos(mes_ano: str):
    ano, mes = map(int, mes_ano.split("-"))

    cards_query = """
    query($pipe_id: ID!, $after: String) {
      cards(pipe_id: $pipe_id, first: 50, after: $after) {
        pageInfo { hasNextPage endCursor }
        edges {
          node {
            id
            created_at
            created_by { name }
            fields { name value }
          }
        }
      }
    }
    """

    todos_cards = []
    cursor = None

    for _ in range(20):
        variables = {"pipe_id": FUNIL_PIPE_ID}
        if cursor:
            variables["after"] = cursor

        resp = requests.post(
            "https://api.pipefy.com/graphql",
            json={"query": cards_query, "variables": variables},
            headers=HEADERS,
            timeout=30
        )
        if resp.status_code != 200:
            break

        data = resp.json()
        cards_data = data.get("data", {}).get("cards", {})
        edges = cards_data.get("edges", [])
        todos_cards.extend(edges)

        page_info = cards_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    contagens = {cap: 0 for cap in CAPTADORES}

    for edge in todos_cards:
        node = edge.get("node", {})
        created_at = node.get("created_at", "")
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if dt.year != ano or dt.month != mes:
                continue
        except Exception:
            continue

        cap_encontrado = None
        for field in node.get("fields", []):
            fname = (field.get("name") or "").lower()
            if "captador" in fname or "captado" in fname or "vendedor" in fname:
                val = field.get("value") or ""
                for cap in CAPTADORES:
                    if cap.split()[0].lower() in val.lower():
                        cap_encontrado = cap
                        break

        if not cap_encontrado:
            criador = (node.get("created_by") or {}).get("name") or ""
            for cap in CAPTADORES:
                if cap.split()[0].lower() in criador.lower():
                    cap_encontrado = cap
                    break

        if cap_encontrado:
            contagens[cap_encontrado] += 1

    total = sum(contagens.values())
    return total, contagens


# ============================================================
# PAGINA
# ============================================================
st.set_page_config(
    page_title="Dashboard - Campelo e Bentes",
    page_icon="⚖️",
    layout="wide"
)

st.markdown("""
<style>
  body, .stApp { background:#0d0d0d !important; color:#f0e6c8; }
  .block-container { padding-top: 1.5rem; }
  .titulo-principal {
    font-size: 2rem; font-weight: 900; color: #FFD700;
    text-align: center; letter-spacing: 2px; margin-bottom: 0.2rem;
  }
  .subtitulo { text-align:center; color:#aaa; font-size:1rem; margin-bottom:1.5rem; }
  .card-m {
    background: linear-gradient(135deg,#1a1a2e,#16213e);
    border: 1px solid #FFD70044;
    border-radius: 12px; padding: 18px 24px; text-align: center;
  }
  .card-m .lbl { color:#aaa; font-size:.85rem; margin-bottom:4px; }
  .card-m .val { color:#FFD700; font-size:2rem; font-weight:900; }
  .card-m .val.verde { color:#00ff99; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="titulo-principal">⚖️ Dashboard — Campelo e Bentes Advogados</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Sistema Comercial · Contratos & Captadores</div>', unsafe_allow_html=True)
st.markdown("---")

# Controles
col_mes, col_meta = st.columns(2)
meses = [f"{y}-{m:02d}" for y in range(2024, 2028) for m in range(1, 13)]
mes_atual = datetime.now().strftime("%Y-%m")
idx = meses.index(mes_atual) if mes_atual in meses else 0

with col_mes:
    mes_selecionado = st.selectbox("📅 Mês:", meses, index=idx)
with col_meta:
    meta = st.number_input("🎯 Meta mensal de contratos:", min_value=1, max_value=500, value=50)

with st.spinner("Buscando dados no Pipefy..."):
    total, contagens = buscar_contratos(mes_selecionado)

if total is None:
    st.error("❌ Não foi possível carregar os dados. Verifique o token Pipefy.")
    st.stop()

pct = round((total / meta) * 100, 1) if meta > 0 else 0
faltam = max(0, meta - total)

# Métricas
c1, c2, c3, c4 = st.columns(4)
for col, lbl, val, verde in [
    (c1, "📋 Total de Contratos", str(total), False),
    (c2, "🎯 Meta", str(meta), False),
    (c3, "📊 Cumprimento", f"{pct}%", pct >= 100),
    (c4, "🏁 Faltam", str(faltam), False),
]:
    cls = "verde" if verde else ""
    col.markdown(f'<div class="card-m"><div class="lbl">{lbl}</div><div class="val {cls}">{val}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Gauge
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=pct,
    delta={"reference": 100},
    title={"text": "% da Meta", "font": {"color": "#FFD700", "size": 18}},
    number={"suffix": "%", "font": {"color": "#FFD700", "size": 34}},
    gauge={
        "axis": {"range": [0, 100], "tickcolor": "#aaa"},
        "bar": {"color": "#FFD700"},
        "bgcolor": "#1a1a2e",
        "steps": [
            {"range": [0, 50],  "color": "#1a1a2e"},
            {"range": [50, 80], "color": "#16213e"},
            {"range": [80, 100],"color": "#0f3460"},
        ],
        "threshold": {"line": {"color": "#00ff99", "width": 3}, "value": 100}
    }
))
fig_gauge.update_layout(
    paper_bgcolor="#0d0d0d", font_color="#f0e6c8",
    height=260, margin=dict(t=40, b=10, l=20, r=20)
)
st.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("---")

# ============================================================
# CORRIDA DOS CAPTADORES
# ============================================================
st.markdown("### 🏁 Corrida dos Captadores")

ranking = sorted(contagens.items(), key=lambda x: x[1], reverse=True)

# Monta dados para o HTML
dados_js = []
for i, (nome, qtd) in enumerate(ranking):
    cor = CORES.get(nome, "#ffffff")
    medalha = MEDALHAS[i] if i < len(MEDALHAS) else ""
    pct_barra = min(98, round((qtd / meta) * 100)) if meta > 0 else 2
    pct_barra = max(2, pct_barra)  # minimo 2% pra aparecer o corredor
    pct_label = round((qtd / meta) * 100, 1) if meta > 0 else 0
    dados_js.append({
        "nome": nome,
        "qtd": qtd,
        "cor": cor,
        "medalha": medalha,
        "pct_barra": pct_barra,
        "pct_label": pct_label,
    })

# Gera blocos de CSS e HTML separadamente (sem f-string aninhada problemática)
css_keyframes = ""
blocos_html = ""

for i, d in enumerate(dados_js):
    pb = d["pct_barra"]
    css_keyframes += f"""
    @keyframes crescer{i} {{
        0%   {{ width: 0%; }}
        100% {{ width: {pb}%; }}
    }}
    @keyframes pular{i} {{
        0%   {{ transform: translateY(0px) scaleX(-1); }}
        50%  {{ transform: translateY(-10px) scaleX(-1); }}
        100% {{ transform: translateY(0px) scaleX(-1); }}
    }}
    """

    delay = i * 0.2
    blocos_html += f"""
    <div class="corredor-row">
        <div class="corredor-info">
            <span class="corredor-nome" style="color:{d['cor']};">{d['medalha']} {d['nome']}</span>
            <span class="corredor-pts" style="color:{d['cor']};"><b>{d['qtd']}</b> contratos &nbsp; {d['pct_label']}%</span>
        </div>
        <div class="pista">
            <div class="barra-progresso" style="
                width: {d['pct_barra']}%;
                background: linear-gradient(90deg, {d['cor']}55, {d['cor']});
                animation: crescer{i} 1.6s {delay}s cubic-bezier(.4,0,.2,1) both;
            "></div>
            <span class="corredor-emoji" style="
                left: calc({d['pct_barra']}% - 32px);
                animation: crescer{i} 1.6s {delay}s cubic-bezier(.4,0,.2,1) both,
                           pular{i} 0.5s {delay}s ease-in-out infinite;
            ">🏃</span>
        </div>
    </div>
    """

html_corrida = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: #0d0d0d;
    color: #f0e6c8;
    font-family: 'Segoe UI', Arial, sans-serif;
    padding: 16px 20px;
}}
.titulo-corrida {{
    text-align: center;
    color: #FFD700;
    font-size: 1.3rem;
    font-weight: 900;
    letter-spacing: 3px;
    margin-bottom: 4px;
    text-shadow: 0 0 24px #FFD70099;
}}
.meta-label {{
    text-align: center;
    color: #888;
    font-size: 0.85rem;
    margin-bottom: 18px;
}}
.corredor-row {{
    margin-bottom: 18px;
}}
.corredor-info {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}}
.corredor-nome {{
    font-weight: bold;
    font-size: 1rem;
}}
.corredor-pts {{
    font-size: 0.95rem;
    color: #ccc;
}}
.pista {{
    background: #1a1a2e;
    border-radius: 40px;
    height: 48px;
    position: relative;
    overflow: visible;
    border: 1px solid #333;
}}
.barra-progresso {{
    position: absolute;
    top: 0; left: 0;
    height: 100%;
    border-radius: 40px;
    min-width: 0;
}}
.corredor-emoji {{
    position: absolute;
    top: 50%;
    transform: translateY(-50%) scaleX(-1);
    font-size: 1.8rem;
    line-height: 1;
    margin-top: -2px;
    z-index: 10;
    /* posicao inicial: 0, animado pelo JS */
}}
.chegada {{
    text-align: center;
    color: #FFD700;
    font-size: 0.8rem;
    margin-top: 14px;
    letter-spacing: 2px;
    opacity: 0.7;
}}
{css_keyframes}
</style>
</head>
<body>
  <div class="titulo-corrida">🏁 CORRIDA DOS CAPTADORES 🏁</div>
  <div class="meta-label">Meta: {meta} contratos</div>
  {blocos_html}
  <div class="chegada">🏁 — LINHA DE CHEGADA: {meta} CONTRATOS — 🏁</div>
</body>
</html>"""

components.html(html_corrida, height=440, scrolling=False)

st.markdown("---")

# Barras
nomes_r   = [r[0] for r in ranking]
valores_r = [r[1] for r in ranking]
cores_r   = [CORES.get(n, "#FFD700") for n in nomes_r]

fig_bar = go.Figure(go.Bar(
    x=nomes_r, y=valores_r,
    marker_color=cores_r,
    text=valores_r, textposition="outside",
    textfont=dict(color="#FFD700", size=16)
))
fig_bar.update_layout(
    title=dict(text="Contratos por Captador", font=dict(color="#FFD700", size=18)),
    paper_bgcolor="#0d0d0d", plot_bgcolor="#1a1a2e",
    font_color="#f0e6c8",
    yaxis=dict(gridcolor="#333"),
    height=300, margin=dict(t=50, b=20)
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown(
    '<div style="text-align:center;color:#444;font-size:.8rem;margin-top:2rem;">'
    'Campelo e Bentes Advogados · Dashboard Comercial</div>',
    unsafe_allow_html=True
)
