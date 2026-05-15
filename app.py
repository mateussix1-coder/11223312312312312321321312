import html
import os
import re
import tempfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import streamlit as st

import auditoria_engine as engine
from auditoria_engine import auditar, format_money_br, linhas_para_dataframe

BRAND_NAME = "FRETE VISION"
BRAND_TAGLINE = "Visão que move resultados"
CENTAVOS = Decimal("0.01")


def safe(value):
    return html.escape(str(value))


def icon(name, size=20):
    paths = {
        "home": '<path d="M3 11.5 12 4l9 7.5v8a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1v-8Z"/>',
        "file": '<path d="M7 3h7l4 4v14H7V3Z"/><path d="M14 3v5h5"/>',
        "chart": '<path d="M4 19V5"/><path d="M4 19h16"/><path d="M8 15v-4"/><path d="M12 15V8"/><path d="M16 15v-6"/>',
        "alert": '<path d="M12 3 22 20H2L12 3Z"/><path d="M12 9v5"/><path d="M12 17h.01"/>',
        "money": '<path d="M12 3v18"/><path d="M17 7.5c-.8-1.1-2.2-1.8-4-1.8-2.2 0-4 1.1-4 2.8 0 4.3 8 1.8 8 6.2 0 1.8-1.9 3-4.4 3-2 0-3.7-.8-4.6-2"/>',
        "settings": '<path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"/><path d="M3 12h2m14 0h2M12 3v2m0 14v2M5.6 5.6 7 7m10 10 1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/>',
        "help": '<path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z"/><path d="M9.7 9a2.4 2.4 0 0 1 4.6 1c0 1.7-2.3 1.9-2.3 3.5"/><path d="M12 17h.01"/>',
        "search": '<circle cx="11" cy="11" r="7"/><path d="m16.5 16.5 4 4"/>',
        "bell": '<path d="M18 8a6 6 0 1 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z"/><path d="M10 21h4"/>',
        "chev": '<path d="m9 6 6 6-6 6"/>',
        "spark": '<path d="M4 14l4-4 3 3 6-7 3 4"/><path d="M4 20h16"/>',
        "swap": '<path d="M7 7h10l-3-3"/><path d="M17 17H7l3 3"/>',
        "upload": '<path d="M12 16V4"/><path d="m7 9 5-5 5 5"/><path d="M5 20h14"/>',
    }
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{paths.get(name, paths["file"])}</svg>'


def logo(size=48):
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg"><text x="20" y="72" fill="#10233A" font-family="serif" font-size="72" font-weight="700">F</text><text x="57" y="88" fill="#C28A34" font-family="serif" font-size="68" font-weight="700">V</text><path d="M18 86C41 62 67 51 104 48" stroke="#10233A" stroke-width="11" stroke-linecap="round"/><path d="M34 95C57 72 76 61 103 55" stroke="#C28A34" stroke-width="3" stroke-linecap="round"/></svg>'''


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800;900&display=swap');
:root{--bg:#f7f9fd;--text:#17213f;--muted:#687592;--line:#e8edf7;--blue:#3158ff;--shadow:0 18px 52px rgba(31,45,78,.08)}
html,body,.stApp{background:var(--bg)!important;color:var(--text)!important;font-family:Manrope,"Segoe UI",sans-serif!important}header,[data-testid="stSidebar"],[data-testid="collapsedControl"],#MainMenu,footer{display:none!important}.block-container{max-width:none!important;padding:16px 24px 14px 272px!important}
.fv-sidebar{position:fixed;z-index:90;left:0;top:0;width:250px;height:100vh;background:#fff;border-right:1px solid #edf1f8;padding:25px 14px 20px;box-shadow:12px 0 42px rgba(47,66,104,.04)}.fv-logo-row{display:flex;align-items:center;gap:13px;padding:0 20px 27px}.fv-logo-title{font-size:21px;line-height:1;font-weight:900;letter-spacing:.08em;color:#152242}.fv-logo-title span{color:#3158ff}.fv-logo-sub{margin-top:7px;color:#596783;font-size:12px;font-weight:700}.fv-nav{display:grid;gap:9px}.fv-nav a{height:46px;border-radius:14px;display:flex;align-items:center;gap:15px;padding:0 18px;text-decoration:none!important;color:#52617f;font-weight:800;font-size:14px}.fv-nav a.active{background:linear-gradient(135deg,#f1f4ff,#f7f8ff);color:#2347ff;box-shadow:inset 0 0 0 1px #edf1ff}.fv-nav svg{width:19px;height:19px}.fv-plan{position:absolute;left:36px;right:28px;bottom:78px;border:1px solid #e3e9f7;border-radius:22px;padding:16px;background:linear-gradient(180deg,#fff,#f8faff)}.fv-plan b{display:block;margin-bottom:16px;color:#4d45d8;font-size:14px}.fv-plan span{display:block;min-height:42px;color:#53617e;font-size:12px;line-height:1.55}.plan-btn{margin-top:16px;height:40px;border-radius:12px;display:grid;place-items:center;border:1px solid #dbe3ff;color:#3158ff;font-weight:900;background:#f7f8ff}.fv-side-footer{position:absolute;left:0;right:0;bottom:24px;text-align:center;color:#9aa5ba;font-size:11px;line-height:1.55;font-weight:700}
.fv-topbar{height:52px;display:grid;grid-template-columns:minmax(360px,560px) 1fr auto auto auto;gap:20px;align-items:center;margin-bottom:14px}.fv-search{height:52px;border-radius:15px;border:1px solid #e6ebf5;background:#fff;box-shadow:var(--shadow);display:flex;align-items:center;gap:13px;padding:0 20px;color:#8b96ad;font-size:15px;font-weight:700}.fv-kbd{margin-left:auto;min-width:38px;height:30px;border-radius:9px;background:#f7f8fc;border:1px solid #e5ebf6;display:grid;place-items:center;color:#66738d;font-size:12px}.fv-bell{position:relative;width:42px;height:42px;display:grid;place-items:center;color:#263a6d}.fv-badge{position:absolute;right:5px;top:2px;width:18px;height:18px;border-radius:99px;background:#3158ff;color:#fff;display:grid;place-items:center;font-size:10px;font-weight:900}.fv-online{height:44px;padding:0 18px;border-radius:13px;border:1px solid #e7edf6;background:#fff;display:inline-flex;align-items:center;gap:10px;color:#14213d;font-weight:900;box-shadow:0 12px 34px rgba(31,45,78,.05)}.fv-online i{width:10px;height:10px;border-radius:99px;background:#18b877}.fv-user{display:grid;grid-template-columns:48px auto 18px;align-items:center;gap:12px;min-width:210px}.fv-avatar{width:48px;height:48px;border-radius:99px;background:linear-gradient(135deg,#ffe0bc,#b87b4e);color:#fff;display:grid;place-items:center;font-weight:900}.fv-user b{display:block;color:#17213f;font-size:14px}.fv-user span{display:block;color:#7b879f;font-size:12px;margin-top:3px}
.fv-kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:14px}.fv-kpi{height:92px;border:1px solid var(--line);border-radius:16px;background:#fff;box-shadow:var(--shadow);padding:12px 14px;display:grid;grid-template-columns:50px 1fr 72px;gap:12px;align-items:center;overflow:hidden}.fv-kpi-icon{width:50px;height:50px;border-radius:13px;display:grid;place-items:center}.fv-kpi small{display:block;color:#65718b;font-weight:800;font-size:11px;margin-bottom:6px}.fv-kpi b{color:#17213f;font-size:18px;line-height:1.1}.fv-kpi span{display:block;margin-top:7px;color:#1daa68;font-size:11px;font-weight:900}.fv-kpi.red span{color:#ff5161}.spark{width:72px;height:34px;overflow:visible}
.fv-workgrid{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:18px;align-items:start}.fv-card{border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.96);box-shadow:var(--shadow)}div[data-testid="stVerticalBlockBorderWrapper"]{border:1px solid var(--line)!important;border-radius:16px!important;background:#fff!important;box-shadow:var(--shadow)!important}.fv-panel-head{display:grid;grid-template-columns:1fr 152px;gap:18px;align-items:start;margin-bottom:18px}.fv-title-line{display:flex;align-items:flex-start;gap:15px}.fv-title-icon{width:40px;height:40px;border-radius:11px;display:grid;place-items:center;color:#fff;background:linear-gradient(135deg,#4163ff,#7446ef);box-shadow:0 14px 32px rgba(82,80,244,.28)}.fv-title{margin:0;color:#17213f;font-size:22px;font-weight:900}.fv-sub{margin-top:8px;color:#66728d;font-size:13px;font-weight:700}.fv-label{margin:0 0 12px;color:#46536f;font-size:12px;font-weight:900}.stButton>button,.stDownloadButton>button{border-radius:13px!important;border:1px solid #e2e8f5!important;background:#fff!important;color:#25314f!important;font-weight:900!important}.stButton>button[kind="primary"]{height:60px!important;max-width:380px!important;margin:10px auto 0!important;border-radius:16px!important;background:linear-gradient(135deg,#304dff,#693cf4)!important;color:#fff!important;box-shadow:0 18px 42px rgba(68,73,244,.28)!important;font-size:16px!important}
[data-testid="stRadio"] [role="radiogroup"]{display:flex!important;gap:8px!important;flex-wrap:nowrap!important}[data-testid="stRadio"] [role="radiogroup"] label{min-height:44px!important;border-radius:13px!important;border:1px solid #e6ebf7!important;background:#fff!important;color:#17213f!important;box-shadow:none!important;padding:0 10px!important;font-size:13px!important;font-weight:900!important;white-space:nowrap!important}[data-testid="stRadio"] [role="radiogroup"] label[data-checked="true"]{background:#f7f8ff!important;border-color:#a9b5ff!important;color:#3158ff!important;box-shadow:0 0 0 1px rgba(49,88,255,.15)!important}[data-testid="stRadio"] input{accent-color:#3158ff!important}.upload-head{border:1px solid #e8edf7;border-radius:16px;background:#fff;padding:14px 14px 10px;text-align:center}.upload-ico{width:34px;height:34px;margin:0 auto 6px;border-radius:11px;display:grid;place-items:center;color:#3158ff;background:linear-gradient(180deg,#e9efff,#dbe5ff)}.upload-title{color:#17213f;font-size:14px;font-weight:900}.upload-sub{color:#66728d;font-size:11px;font-weight:700;margin:3px 0 6px}.fv-swap{width:44px;height:44px;border-radius:99px;background:#fff;border:1px solid #e6ebf5;box-shadow:0 12px 30px rgba(31,45,78,.08);display:grid;place-items:center;color:#66728d;margin:auto}[data-testid="stFileUploaderDropzone"]{min-height:42px!important;border-radius:14px!important;border:1px dashed #cfd8eb!important;background:#fff!important;padding:6px 10px!important}[data-testid="stFileUploaderDropzone"] small{display:none!important}[data-testid="stFileUploaderDropzone"] button{border:0!important;background:transparent!important;color:#3158ff!important;box-shadow:none!important;padding:0!important}.secure{text-align:center;color:#8a95ad;font-size:12px;font-weight:800;margin-top:6px}
.fv-insights{min-height:430px;padding:18px}.fv-insight-title{display:flex;justify-content:space-between;align-items:center;color:#17213f;font-weight:900;margin-bottom:20px}.fv-ai-list{display:grid;gap:12px;margin:13px 0 18px;color:#66728d;font-size:12px;font-weight:800}.fv-ai-list div{display:flex;align-items:center;gap:12px}.fv-check{width:23px;height:23px;border-radius:99px;display:grid;place-items:center;color:#3158ff;background:#edf2ff;border:1px solid #cad6ff;flex:0 0 auto}.fv-last{border-top:1px solid var(--line);padding-top:16px}.fv-last-head{display:flex;justify-content:space-between;color:#17213f;font-size:13px;font-weight:900;margin-bottom:12px}.fv-last-head a{color:#3158ff;text-decoration:none}.fv-audit-row{display:grid;grid-template-columns:1fr 64px 68px 12px;gap:7px;align-items:center;min-height:41px;font-size:12px}.fv-audit-row b{display:block;font-size:12px;color:#17213f}.fv-audit-row small{display:block;color:#8c97ad;margin-top:2px}.fv-status{height:24px;border-radius:8px;display:grid;place-items:center;font-size:10px;font-weight:900}.fv-status.done{background:#eafaf2;color:#18a66b}.fv-status.wait{background:#fff4dc;color:#e59618}.fv-tip{margin-top:14px;border:1px solid #dfe7f6;border-radius:15px;padding:14px;display:grid;grid-template-columns:34px 1fr;gap:12px;color:#53617e;font-size:12px;line-height:1.55}.fv-tip-icon{width:34px;height:34px;border-radius:99px;display:grid;place-items:center;color:#f0a11d;background:#fff7e8}.results-card{margin-top:16px;padding:16px}.metric-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}.metric{border:1px solid var(--line);border-radius:14px;background:#fff;padding:13px}.metric small{display:block;color:#66728d;font-size:11px;font-weight:900}.metric b{display:block;color:#17213f;font-size:20px;margin-top:7px}.metric.red b{color:#ff5161}.metric.green b{color:#18a66b}.metric.blue b{color:#3158ff}
@media(max-width:1500px){.block-container{padding-left:262px!important;padding-right:18px!important}.fv-sidebar{width:242px}.fv-workgrid{grid-template-columns:minmax(0,1fr) 300px}.fv-kpi{grid-template-columns:48px 1fr 64px;padding:11px}.fv-kpi b{font-size:17px}.fv-audit-row{grid-template-columns:1fr 58px 54px 10px}}@media(max-width:1180px){.fv-sidebar{position:static;width:auto;height:auto;padding:16px;margin-bottom:14px}.fv-plan,.fv-side-footer{display:none}.block-container{padding:16px!important}.fv-nav{grid-template-columns:repeat(3,minmax(0,1fr))}.fv-topbar{grid-template-columns:1fr auto}.fv-online,.fv-user{display:none}.fv-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.fv-workgrid{grid-template-columns:1fr}.fv-swap{display:none}}@media(max-width:760px){.fv-nav,.fv-topbar,.fv-kpi-grid,.metric-grid{grid-template-columns:1fr}.fv-search{min-width:0}}
</style>
"""


def set_page():
    st.set_page_config(page_title=BRAND_NAME, layout="wide", initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)


def page_key():
    try:
        value = st.query_params.get("page", "nova")
    except Exception:
        value = "nova"
    return value[0] if isinstance(value, list) else value


def sidebar(active):
    items = [("nova", "Nova Auditoria", "home"), ("visao", "Visão geral", "file"), ("auditorias", "Auditorias", "file"), ("relatorios", "Relatórios", "chart"), ("divergencias", "Divergências", "alert"), ("economia", "Economia", "money"), ("integracoes", "Integrações", "settings"), ("configuracoes", "Configurações", "settings"), ("suporte", "Suporte", "help")]
    links = "".join(f'<a class="{"active" if key == active else ""}" href="?page={key}">{icon(ic)}<span>{safe(label)}</span></a>' for key, label, ic in items)
    st.markdown(f'''<aside class="fv-sidebar"><div class="fv-logo-row">{logo(48)}<div><div class="fv-logo-title">FRETE<span>VISION</span></div><div class="fv-logo-sub">{safe(BRAND_TAGLINE)}</div></div></div><nav class="fv-nav">{links}</nav><div class="fv-plan"><b>Plano Empresarial</b><span>Aproveite todos os recursos avançados da plataforma.</span><div class="plan-btn">Ver plano</div></div><div class="fv-side-footer">© 2026 FreteVision Logística<br>Desenvolvido por Mateus</div></aside>''', unsafe_allow_html=True)


def topbar():
    st.markdown(f'''<div class="fv-topbar"><div class="fv-search">{icon("search",19)}<span>Buscar auditorias, relatórios, clientes...</span><span class="fv-kbd">⌘ K</span></div><div></div><div class="fv-bell">{icon("bell",24)}<span class="fv-badge">3</span></div><div class="fv-online"><i></i>Online</div><div class="fv-user"><div class="fv-avatar">MS</div><div><b>Mateus Santos</b><span>Administrador</span></div>{icon("chev",18)}</div></div>''', unsafe_allow_html=True)


def spark(color, points):
    return f'<svg class="spark" viewBox="0 0 92 44" fill="none"><path d="{points} L90 44 L6 44 Z" fill="{color}" opacity=".10"/><path d="{points}" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def kpis():
    data = [("Auditorias hoje", "12", "+20% vs ontem", "#4e5bff", "#eef0ff", "file", "M6 35 L16 30 L25 34 L34 16 L43 37 L54 32 L65 35 L76 22 L88 20", ""), ("Divergências", "8", "+12% vs ontem", "#ff5161", "#fff0f2", "alert", "M6 34 L17 36 L28 13 L39 20 L50 31 L61 31 L72 37 L84 28 L90 28", "red"), ("Economia recuperada", "R$ 24.560,75", "+18% vs ontem", "#25b47b", "#e9faf2", "money", "M6 36 L15 29 L25 31 L35 22 L45 23 L55 13 L65 21 L75 14 L84 25 L90 10", ""), ("Tempo médio", "18m 42s", "-8% vs ontem", "#2f7dde", "#eef6ff", "chart", "M6 13 L16 7 L27 19 L37 36 L48 18 L58 6 L69 22 L80 20 L88 27", "")]
    cards = "".join(f'<div class="fv-kpi {extra}"><div class="fv-kpi-icon" style="color:{color};background:{bg};">{icon(ic,26)}</div><div><small>{safe(t)}</small><b>{safe(v)}</b><span>{safe(d)}</span></div>{spark(color, pts)}</div>' for t, v, d, color, bg, ic, pts, extra in data)
    st.markdown(f'<div class="fv-kpi-grid">{cards}</div>', unsafe_allow_html=True)


def normalize(resumo):
    return {"total": int(resumo.get("total_analisado", 0) or 0), "ok": int(resumo.get("ok", 0) or 0), "ok_arredondamento": int(resumo.get("ok_arredondamento", 0) or 0), "divergentes": int(resumo.get("divergentes", 0) or 0), "faltantes_a": int(resumo.get("faltante_a", 0) or 0), "faltantes_b": int(resumo.get("faltante_b", 0) or 0), "impacto_absoluto": resumo.get("impacto_absoluto", Decimal("0.00"))}


def save_upload(uploaded, prefix):
    if uploaded is None:
        return None
    if Path(uploaded.name).suffix.lower() != ".pdf":
        raise ValueError("Envie apenas arquivos PDF.")
    temp_dir = Path(tempfile.gettempdir()) / "fretescan_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix=f"{re.sub(r'[^A-Za-z0-9_-]+', '_', prefix)}_", dir=temp_dir) as tmp:
        tmp.write(bytes(uploaded.getbuffer()))
        return tmp.name


def upload_card(title, desc, key):
    st.markdown(f'''<div class="upload-head"><div class="upload-ico">{icon("upload",22)}</div><div class="upload-title">{safe(title)}</div><div class="upload-sub">{safe(desc)}</div></div>''', unsafe_allow_html=True)
    return st.file_uploader(title, type=["pdf"], key=key, label_visibility="collapsed")


def insights():
    rows = [("AUD-2026-00012", "Hoje, 09:32", "Concluída", "R$ 2.450,75", "done"), ("AUD-2026-00011", "Hoje, 08:11", "Em análise", "-", "wait"), ("AUD-2026-00010", "Ontem, 17:45", "Concluída", "R$ 1.128,40", "done"), ("AUD-2026-00009", "Ontem, 15:20", "Concluída", "R$ 890,10", "done")]
    audit_rows = "".join(f'<div class="fv-audit-row"><div><b>{safe(c)}</b><small>{safe(w)}</small></div><span class="fv-status {k}">{safe(s)}</span><span style="color:#53617e;font-weight:800;">{safe(a)}</span>{icon("chev",13)}</div>' for c, w, s, a, k in rows)
    st.markdown(f'''<aside class="fv-card fv-insights"><div class="fv-insight-title"><span>{icon("spark",18)} Insights automáticos</span><span>⌃</span></div><div style="color:#66728d;font-size:13px;font-weight:700;">Ao enviar os relatórios, nossa IA irá:</div><div class="fv-ai-list"><div><span class="fv-check">✓</span> Comparar valores e identificar divergências</div><div><span class="fv-check">⊙</span> Detectar cobranças indevidas</div><div><span class="fv-check">✓</span> Validar regras e políticas aplicadas</div><div><span class="fv-check">✓</span> Gerar relatório detalhado</div><div><span class="fv-check">$</span> Calcular economia potencial</div></div><div class="fv-last"><div class="fv-last-head"><span>Últimas auditorias</span><a href="?page=auditorias">Ver todas</a></div>{audit_rows}</div><div class="fv-tip"><div class="fv-tip-icon">!</div><div><b style="display:block;color:#17213f;margin-bottom:4px;">Dica</b>Mantenha os relatórios do mesmo período para análises mais precisas.</div></div></aside>''', unsafe_allow_html=True)


def setup_panel():
    head_left, head_right = st.columns([5.6, 1.45], gap="small")
    with head_left:
        st.markdown(f'''<div class="fv-panel-head"><div class="fv-title-line"><div class="fv-title-icon">{icon("spark",21)}</div><div><h3 class="fv-title">Nova Auditoria</h3><div class="fv-sub">Configure a tolerância e envie os dois relatórios do mesmo período para iniciar a análise.</div></div></div></div>''', unsafe_allow_html=True)
    with head_right:
        if st.button("Limpar formulário", use_container_width=True):
            for key in ["up_a", "up_b", "resultado", "erro"]:
                st.session_state.pop(key, None)
            st.rerun()
    st.markdown('<div class="fv-label">Tolerância de diferença</div>', unsafe_allow_html=True)
    opts = {"R$ 0,00": 0.0, "R$ 0,30": 0.30, "R$ 0,50": 0.50, "R$ 1,00": 1.0, "Personalizado": -1}
    selected = st.radio("Tolerância", list(opts.keys()), index=2, horizontal=True, label_visibility="collapsed")
    tolerance = opts[selected]
    if tolerance == -1:
        tolerance = st.number_input("Valor personalizado (R$)", 0.0, 999.0, 0.50, 0.10, format="%.2f")
    col_a, col_mid, col_b = st.columns([1, 0.16, 1], gap="small")
    with col_a:
        file_a = upload_card("Sistema A (Relatório DL)", "Upload do relatório principal da empresa.", "up_a")
    with col_mid:
        st.markdown(f'<div class="fv-swap">{icon("swap",22)}</div>', unsafe_allow_html=True)
    with col_b:
        file_b = upload_card("Sistema B (Relatório Carreteiro)", "Upload do relatório de conferência.", "up_b")
    clicked = st.button("Iniciar Auditoria", type="primary", use_container_width=True)
    st.markdown('<div class="secure">Seus dados estão seguros e criptografados.</div>', unsafe_allow_html=True)
    return tolerance, file_a, file_b, clicked


def run_audit(tolerance, file_a, file_b):
    if not file_a or not file_b:
        raise ValueError("Faça upload dos dois relatórios antes de iniciar a auditoria.")
    path_a = save_upload(file_a, "ATUA")
    path_b = save_upload(file_b, "GW")
    result = auditar(path_a, path_b, Decimal(str(tolerance)).quantize(CENTAVOS, rounding=ROUND_HALF_UP))
    df = linhas_para_dataframe(result["linhas"])
    summary = normalize(result["resumo"])
    engine.salvar_historico(file_a.name, file_b.name, float(tolerance), summary)
    st.session_state.resultado = {"df": df, "summary": summary, "raw": result, "name_a": file_a.name, "name_b": file_b.name, "tolerance": float(tolerance)}
    for path in [path_a, path_b]:
        try:
            os.unlink(path)
        except OSError:
            pass


def render_results():
    data = st.session_state.get("resultado")
    if not data:
        return
    resumo = data["summary"]
    faltantes = resumo["faltantes_a"] + resumo["faltantes_b"]
    metrics = [("Total analisado", resumo["total"], ""), ("OK", resumo["ok"], "green"), ("OK Arred.", resumo["ok_arredondamento"], "blue"), ("Divergentes", resumo["divergentes"], "red"), ("Faltantes", faltantes, "red"), ("Impacto crítico", format_money_br(resumo["impacto_absoluto"]), "red")]
    metric_html = "".join(f'<div class="metric {kind}"><small>{safe(label)}</small><b>{safe(value)}</b></div>' for label, value, kind in metrics)
    st.markdown(f'<section class="fv-card results-card"><div class="metric-grid">{metric_html}</div></section>', unsafe_allow_html=True)
    with st.expander("Debug da leitura", expanded=False):
        st.json(data["raw"].get("debug", {}), expanded=False)
    st.dataframe(data["df"], use_container_width=True, height=360)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("Baixar CSV", engine.exportar_csv(data["df"]), "auditoria.csv", "text/csv", use_container_width=True)
    with c2:
        st.download_button("Baixar Excel", engine.exportar_excel(data["df"], resumo, data["name_a"], data["name_b"], data["tolerance"]), "auditoria.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with c3:
        st.download_button("Baixar PDF", engine.exportar_pdf(data["df"], resumo, data["name_a"], data["name_b"], data["tolerance"]), "auditoria.pdf", "application/pdf", use_container_width=True)


def placeholder(title):
    st.markdown(f'<section class="fv-card results-card"><h2>{safe(title)}</h2><p style="color:#66728d;font-weight:700;">Área visual mantida para navegação. A auditoria principal fica em Nova Auditoria.</p></section>', unsafe_allow_html=True)


def main():
    st.set_page_config(page_title=BRAND_NAME, layout="wide", initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)
    active = page_key()
    sidebar(active)
    topbar()
    kpis()
    if active == "nova":
        left, right = st.columns([2.75, 1], gap="medium")
        with left:
            with st.container(border=True):
                tolerance, file_a, file_b, clicked = setup_panel()
        with right:
            insights()
        if clicked:
            try:
                with st.spinner("Processando auditoria..."):
                    run_audit(tolerance, file_a, file_b)
                st.rerun()
            except Exception as exc:
                st.session_state.erro = str(exc)
        if st.session_state.get("erro"):
            st.error(st.session_state.erro)
        render_results()
    else:
        placeholder("Visão geral")


main()
