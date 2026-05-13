
import json
from pathlib import Path
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st


# ============================================================
# CELLFRAME AUDIT DASHBOARD — VISUAL REDESIGN
# ============================================================

st.set_page_config(
    page_title="CELLFRAME On-Chain Audit",
    page_icon="⬢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(".")


# ------------------------------
# Helpers
# ------------------------------

def load_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        return default
    return default


def load_csv(path: Path):
    try:
        if path.exists():
            return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame()


def D(value, default="0"):
    try:
        if value is None or value == "":
            return Decimal(default)
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def compact(value):
    d = D(value)
    sign = "-" if d < 0 else ""
    d = abs(d)
    if d >= Decimal("1000000000"):
        return f"{sign}{d / Decimal('1000000000'):.2f}B"
    if d >= Decimal("1000000"):
        return f"{sign}{d / Decimal('1000000'):.2f}M"
    if d >= Decimal("1000"):
        return f"{sign}{d / Decimal('1000'):.2f}K"
    return f"{sign}{d:.2f}"


def fmt(value, places=2):
    return f"{D(value):,.{places}f}"


def anchor(name):
    st.markdown(f'<a id="{name}"></a>', unsafe_allow_html=True)


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def safe_df(df, height=None):
    if df is not None and not df.empty:
        if height:
            st.dataframe(df, use_container_width=True, hide_index=True, height=height)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)


def evidence_file_rows(files):
    rows = []
    for f in files:
        p = ROOT / f
        rows.append({
            "Artifact": f,
            "Present": "Yes" if p.exists() else "No",
            "Size KB": round(p.stat().st_size / 1024, 2) if p.exists() else "",
        })
    return pd.DataFrame(rows)


# ------------------------------
# Load generated audit data
# ------------------------------

reserve = load_json(ROOT / "reserve_backing_reconciliation.json")
reserve_totals = reserve.get("totals", {}) if isinstance(reserve, dict) else {}

circ = load_json(ROOT / "circulating_supply_estimate.json")
circ_inputs = circ.get("inputs", {}) if isinstance(circ, dict) else {}
circ_estimates = circ.get("estimates", {}) if isinstance(circ, dict) else {}

trace_8bbf_recipients = load_csv(ROOT / "auto_trace_8bbf_combined_recipient_summary.csv")
old_child = load_csv(ROOT / "oldcell_458b_child_probe_summary.csv")
old_secondary = load_csv(ROOT / "oldcell_secondary_child_probe_summary.csv")
mexc_label = load_csv(ROOT / "mexc_label_check_report.csv")
mexc_pattern = load_csv(ROOT / "mexc_deposit_pattern_check_report.csv")
circ_csv = load_csv(ROOT / "circulating_supply_estimate.csv")

# Current verified values
ETH_SUPPLY = D(reserve_totals.get("eth_total_supply_cell") or circ_inputs.get("eth_total_supply_cell") or "30300000")
BSC_SUPPLY = D(reserve_totals.get("bsc_total_supply_cell") or circ_inputs.get("bsc_total_supply_cell") or "33300000")
RAW_SUPPLY = D(circ_inputs.get("raw_eth_plus_bsc_contract_supply_cell") or (ETH_SUPPLY + BSC_SUPPLY))
BACKING = D(
    circ_estimates.get("conservative_non_circulating_cell")
    or reserve_totals.get("eth_backing_candidate_included_cell")
    or "990044.19498039"
)
CIRC_EST = D(circ_estimates.get("conservative_circulating_supply_estimate_cell") or "62609955.80501961")
BSC_GAP = D(circ_estimates.get("bsc_supply_minus_verified_eth_backing_candidates_cell") or "32309955.80501961")
GATEIO_EXPOSURE = D("2596567.55466338")
OLD_CELL_UNLOCK = D("5207505.2")
OLD_CELL_A9AD_HELD = D("2625551.2")

PUBLIC_MEXC_HITS = 0
if not mexc_label.empty and "status" in mexc_label.columns:
    PUBLIC_MEXC_HITS += int(mexc_label["status"].isin(["known_mexc_label", "bscscan_page_contains_mexc_keyword"]).sum())
if not mexc_pattern.empty and "status" in mexc_pattern.columns:
    PUBLIC_MEXC_HITS += int((mexc_pattern["status"] == "known_mexc_route_detected").sum())


# ============================================================
# CSS — matches the futuristic audit dashboard mockup
# ============================================================

html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root{
  --bg0:#020711;
  --bg1:#061321;
  --bg2:#081b2d;
  --card:#071928cc;
  --card2:#0b2035d9;
  --cyan:#20f3e8;
  --cyan2:#0bbbd6;
  --blue:#3b82f6;
  --green:#19d37d;
  --amber:#f7c948;
  --purple:#a970ff;
  --red:#fb7185;
  --text:#f3fbff;
  --muted:#9eb4c9;
  --line:rgba(45,245,232,.18);
}

html, body, [class*="css"]{font-family:'Inter',sans-serif;}
.stApp{
  color:var(--text);
  background:
    radial-gradient(circle at 72% 8%, rgba(32,243,232,.25), transparent 28%),
    radial-gradient(circle at 10% 12%, rgba(32,243,232,.12), transparent 25%),
    radial-gradient(circle at 80% 70%, rgba(59,130,246,.12), transparent 34%),
    linear-gradient(180deg,#020711 0%,#04111f 48%,#020711 100%);
}
.block-container{max-width:1540px;padding-top:1.1rem;padding-bottom:3rem;}
a{text-decoration:none;color:inherit;}
#MainMenu, footer, header{visibility:hidden;}

.audit-shell{
  border:1px solid rgba(32,243,232,.16);
  border-radius:24px;
  background:linear-gradient(180deg,rgba(2,7,17,.72),rgba(3,12,24,.62));
  box-shadow:0 26px 90px rgba(0,0,0,.38), inset 0 0 0 1px rgba(255,255,255,.02);
  overflow:hidden;
}

.topnav{
  position:sticky;top:0;z-index:20;
  display:flex;align-items:center;justify-content:space-between;gap:20px;
  padding:16px 24px;
  border-bottom:1px solid rgba(32,243,232,.16);
  backdrop-filter:blur(18px);
  background:rgba(2,7,17,.78);
}
.logo{
  display:flex;align-items:center;gap:12px;font-weight:950;font-size:1.45rem;letter-spacing:-.04em;
}
.logo-mark{
  width:31px;height:31px;border-radius:9px;
  background:linear-gradient(135deg,rgba(32,243,232,.25),rgba(32,243,232,.05));
  border:2px solid rgba(32,243,232,.85);
  box-shadow:0 0 28px rgba(32,243,232,.45);
  position:relative;
}
.logo-mark:after{
  content:"";position:absolute;inset:7px;border:2px solid rgba(32,243,232,.7);border-radius:6px;transform:rotate(45deg);
}
.logo span{color:var(--cyan);}
.navlinks{display:flex;align-items:center;justify-content:flex-end;gap:22px;flex-wrap:wrap;}
.navlinks a{font-size:.88rem;font-weight:800;color:#c8d7e4;opacity:.9;}
.navlinks a.active{color:white;border-bottom:3px solid var(--cyan);padding-bottom:12px;}
.nav-badge{
  display:flex;align-items:center;gap:8px;color:var(--cyan);font-weight:900;
  padding:9px 14px;border:1px solid rgba(32,243,232,.38);border-radius:11px;background:rgba(32,243,232,.06);
}

.hero{
  display:grid;grid-template-columns:1.05fr .95fr;gap:30px;
  padding:34px 30px 22px;min-height:290px;position:relative;
}
.hero h1{
  font-size:clamp(2.4rem,4.8vw,4.6rem);line-height:.98;margin:0 0 12px;letter-spacing:-.075em;
}
.hero h1 .accent{color:var(--cyan);text-shadow:0 0 30px rgba(32,243,232,.25);}
.hero p{color:#b9c8d7;font-size:1.05rem;line-height:1.65;margin:0;max-width:720px;}
.hero-tags{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px;}
.tag{
  border:1px solid rgba(32,243,232,.18);background:rgba(5,21,35,.72);
  color:#bfeaf0;padding:8px 12px;border-radius:9px;font-size:.82rem;font-weight:700;
}
.hero-visual{
  min-height:245px;border-radius:22px;position:relative;overflow:hidden;
  background:
    radial-gradient(circle at 52% 30%, rgba(32,243,232,.48), transparent 13%),
    radial-gradient(circle at 52% 35%, rgba(32,243,232,.18), transparent 28%),
    linear-gradient(120deg,rgba(4,15,28,.2),rgba(32,243,232,.08));
}
.hero-visual:before{
  content:"";position:absolute;inset:0;
  background-image:
    linear-gradient(rgba(32,243,232,.10) 1px, transparent 1px),
    linear-gradient(90deg,rgba(32,243,232,.10) 1px, transparent 1px);
  background-size:38px 38px;
  transform:perspective(500px) rotateX(60deg) translateY(40px);
  opacity:.7;
}
.orb{
  position:absolute;left:50%;top:48%;transform:translate(-50%,-50%);
  width:132px;height:132px;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#eaffff,#20f3e8 28%,#075a66 65%,#04111f 100%);
  border:7px solid rgba(236,255,255,.38);
  box-shadow:0 0 20px rgba(32,243,232,.55),0 0 80px rgba(32,243,232,.38);
}
.orb:after{
  content:"";position:absolute;inset:32px;border:4px solid rgba(2,7,17,.9);border-radius:16px;transform:rotate(45deg);
}
.node{position:absolute;width:24px;height:24px;border:1px solid rgba(32,243,232,.55);border-radius:6px;background:rgba(32,243,232,.08);}
.n1{left:18%;top:28%}.n2{right:18%;top:34%}.n3{left:28%;bottom:22%}.n4{right:28%;bottom:24%}

.kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;padding:0 24px 12px;}
.kpi{
  border:1px solid rgba(32,243,232,.18);border-radius:14px;padding:18px;min-height:144px;
  background:linear-gradient(145deg,rgba(7,25,40,.9),rgba(5,14,26,.78));
}
.kpi.cyan{border-color:rgba(32,243,232,.34);background:linear-gradient(145deg,rgba(7,44,54,.72),rgba(5,17,28,.8));}
.kpi.blue{border-color:rgba(59,130,246,.36);}
.kpi.green{border-color:rgba(25,211,125,.33);background:linear-gradient(145deg,rgba(7,44,36,.68),rgba(5,17,28,.8));}
.kpi.amber{border-color:rgba(247,201,72,.36);background:linear-gradient(145deg,rgba(48,36,8,.58),rgba(5,17,28,.8));}
.kpi-icon{
  width:54px;height:54px;border-radius:14px;display:flex;align-items:center;justify-content:center;
  font-size:1.55rem;margin-bottom:10px;border:1px solid currentColor;background:rgba(255,255,255,.04);
}
.kpi .label{font-size:.88rem;color:white;font-weight:800;margin-bottom:10px;}
.kpi .value{font-size:2.1rem;font-weight:950;letter-spacing:-.06em;color:var(--cyan);}
.kpi.green .value{color:#35f59c}.kpi.amber .value{color:#ffd35c}.kpi.blue .value{color:#73b7ff}
.kpi .unit{font-size:.78rem;color:var(--cyan);font-weight:900;margin-left:4px;}
.kpi .sub{font-size:.83rem;color:var(--muted);line-height:1.35;margin-top:6px;}

.section{
  margin:12px 16px;border:1px solid rgba(32,243,232,.13);border-radius:18px;
  background:linear-gradient(180deg,rgba(4,15,27,.72),rgba(3,11,21,.60));
  padding:20px;
}
.section-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px;}
.section h2{font-size:1.38rem;margin:0;letter-spacing:-.04em;}
.section p{color:var(--muted);line-height:1.55;margin:.3rem 0 0;}
.badge{border:1px solid rgba(32,243,232,.28);color:var(--cyan);font-weight:900;border-radius:999px;padding:7px 10px;font-size:.76rem;background:rgba(32,243,232,.07);}
.badge.green{color:#72ffb7;border-color:rgba(25,211,125,.35);background:rgba(25,211,125,.08);}
.badge.amber{color:#ffdc69;border-color:rgba(247,201,72,.35);background:rgba(247,201,72,.08);}
.badge.red{color:#ff9aaa;border-color:rgba(251,113,133,.35);background:rgba(251,113,133,.08);}

.card-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.info-card{
  border:1px solid rgba(32,243,232,.14);border-radius:14px;padding:16px;background:rgba(7,25,40,.62);
  min-height:140px;
}
.info-card h3{margin:0 0 8px;font-size:1rem;}
.info-card p{font-size:.86rem;color:#aabed0;line-height:1.45;margin:0 0 10px;}
.status{display:inline-flex;gap:7px;align-items:center;padding:6px 9px;border-radius:999px;font-weight:900;font-size:.75rem;}
.status.ok{color:#6fffb2;background:rgba(25,211,125,.12);border:1px solid rgba(25,211,125,.28);}
.status.open{color:#ffd86b;background:rgba(247,201,72,.12);border:1px solid rgba(247,201,72,.28);}
.status.no{color:#ff9aaa;background:rgba(251,113,133,.12);border:1px solid rgba(251,113,133,.28);}

.flow{display:grid;grid-template-columns:1fr 42px 1fr 42px 1fr 42px 1fr 42px 1fr;align-items:stretch;gap:8px;}
.flow-card{
  border:1px solid rgba(32,243,232,.2);border-radius:14px;padding:14px;background:rgba(7,25,40,.66);min-height:170px;
}
.flow-card.purple{border-color:rgba(169,112,255,.32)}
.flow-card.amber{border-color:rgba(247,201,72,.42)}
.flow-num{width:30px;height:30px;border-radius:10px;display:flex;align-items:center;justify-content:center;color:var(--cyan);border:1px solid currentColor;background:rgba(32,243,232,.08);font-weight:950;margin-bottom:10px;}
.flow-card h3{margin:0 0 6px;font-size:1rem;color:#9ffdf5;}
.flow-card.amber h3{color:#ffdc69}.flow-card.purple h3{color:#d7b9ff}
.flow-card p{font-size:.82rem;margin:0 0 10px;color:#aac0d2;}
.addr-chip{display:inline-flex;margin:4px 4px 0 0;padding:5px 7px;border-radius:7px;background:rgba(32,243,232,.08);border:1px solid rgba(32,243,232,.18);color:#76f7f0;font-size:.72rem;font-weight:800;}
.arrow{display:flex;align-items:center;justify-content:center;color:var(--cyan);font-size:2rem;text-shadow:0 0 20px rgba(32,243,232,.6);}

.split{display:grid;grid-template-columns:1.15fr .85fr;gap:14px;}
.path-strip{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;}
.path-node{border:1px solid rgba(32,243,232,.18);border-radius:13px;padding:12px;background:rgba(7,25,40,.68);min-height:165px;}
.path-node .mini{color:var(--cyan);font-weight:900;font-size:.78rem;margin-bottom:8px;}
.path-node h4{margin:0 0 8px;font-size:.95rem;}
.path-node p{font-size:.76rem;margin:0;color:#9eb4c9;}
.callout{margin-top:12px;border:1px solid rgba(247,201,72,.35);background:rgba(247,201,72,.08);color:#ffdc69;padding:13px;border-radius:13px;font-weight:900;}

.supply-panel{display:grid;grid-template-columns:210px 1fr;gap:18px;align-items:center;}
.donut{
  width:180px;height:180px;border-radius:50%;margin:auto;
  background:conic-gradient(var(--cyan) 0 4.09%, var(--green) 4.09% 5.65%, rgba(59,130,246,.85) 5.65% 100%);
  display:flex;align-items:center;justify-content:center;position:relative;
}
.donut:after{content:"";position:absolute;inset:38px;border-radius:50%;background:#071525;border:1px solid rgba(32,243,232,.16);}
.donut span{position:relative;z-index:2;text-align:center;font-weight:950;font-size:1.1rem;}
.legend-row{display:grid;grid-template-columns:1fr auto;gap:10px;padding:9px 0;border-bottom:1px solid rgba(32,243,232,.10);color:#c9d8e5;font-size:.88rem;}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px;background:var(--cyan);}
.dot.green{background:var(--green)}.dot.blue{background:var(--blue)}

.table-wrap{border:1px solid rgba(32,243,232,.13);border-radius:14px;overflow:hidden;background:rgba(7,25,40,.54);}
[data-testid="stDataFrame"]{border:1px solid rgba(32,243,232,.13);border-radius:14px;overflow:hidden;}
[data-testid="stDataFrame"] *{font-family:'Inter',sans-serif;}

.download-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}
.download-card{border:1px solid rgba(32,243,232,.16);border-radius:14px;padding:16px;background:rgba(7,25,40,.62);}
.download-card h3{margin:0 0 8px;font-size:1rem}.download-card p{font-size:.82rem;margin:0;color:#9eb4c9;}

.footerbar{display:flex;justify-content:space-between;align-items:center;gap:20px;margin:16px 18px 0;padding:18px;color:#91a7b9;font-size:.8rem;border-top:1px solid rgba(32,243,232,.12);}

@media(max-width:1200px){
  .hero{grid-template-columns:1fr}.kpi-row{grid-template-columns:repeat(2,1fr)}
  .card-grid{grid-template-columns:repeat(2,1fr)}
  .flow{grid-template-columns:1fr}.arrow{transform:rotate(90deg)}
  .split{grid-template-columns:1fr}.path-strip{grid-template-columns:repeat(2,1fr)}
  .download-grid{grid-template-columns:1fr}.supply-panel{grid-template-columns:1fr}
}
@media(max-width:720px){
  .topnav{align-items:flex-start;flex-direction:column;border-radius:18px}
  .navlinks{gap:12px}.hero{padding:24px 18px}.kpi-row{grid-template-columns:1fr;padding:0 14px 12px}
  .card-grid{grid-template-columns:1fr}.path-strip{grid-template-columns:1fr}.section{margin:10px 8px;padding:16px}
}
</style>
""")


# ============================================================
# Page
# ============================================================

html('<div class="audit-shell">')

# Header / navigation
html("""
<div class="topnav">
  <div class="logo"><div class="logo-mark"></div><div><span>CELLFRAME</span> Audit</div></div>
  <div class="navlinks">
    <a class="active" href="#overview">Overview</a>
    <a href="#findings">Evidence</a>
    <a href="#supply">Supply</a>
    <a href="#bridge">Bridges</a>
    <a href="#routes">Routes</a>
    <a href="#trust">Trust</a>
    <a href="#downloads">Downloads</a>
    <a href="#about">About</a>
  </div>
  <div class="nav-badge">🛡 On-Chain Only</div>
</div>
""")

anchor("overview")
html("""
<div class="hero">
  <div>
    <h1>CELLFRAME <span class="accent">On-Chain Audit</span></h1>
    <p>
      Independent on-chain evidence of CELL / CELLFRAME: supply tracing,
      bridge analysis, reserve candidates, downstream wallet routing, and market-route verification.
    </p>
    <div class="hero-tags">
      <div class="tag">🛡 Public on-chain evidence only</div>
      <div class="tag">🔒 No private or off-chain data used</div>
      <div class="tag">🔎 Reproducible CSV / JSON evidence</div>
    </div>
  </div>
  <div class="hero-visual">
    <div class="orb"></div>
    <div class="node n1"></div><div class="node n2"></div><div class="node n3"></div><div class="node n4"></div>
  </div>
</div>
""")

# KPI row
html(f"""
<div class="kpi-row">
  <div class="kpi cyan">
    <div class="kpi-icon">⬢</div>
    <div class="label">Total Supply Snapshot</div>
    <div><span class="value">{compact(RAW_SUPPLY)}</span><span class="unit">CELL</span></div>
    <div class="sub">Across Ethereum & BSC</div>
  </div>

  <div class="kpi cyan">
    <div class="kpi-icon">👥</div>
    <div class="label">Evidence-Only Circulating Estimate</div>
    <div><span class="value">{compact(CIRC_EST)}</span><span class="unit">CELL</span></div>
    <div class="sub">On-chain verified estimate</div>
  </div>

  <div class="kpi blue">
    <div class="kpi-icon">↪</div>
    <div class="label">Verified Gate.io Route Exposure</div>
    <div><span class="value">{compact(GATEIO_EXPOSURE)}</span><span class="unit">CELL</span></div>
    <div class="sub">≥ {fmt(GATEIO_EXPOSURE, 2)} CELL Gate.io-bound route</div>
  </div>

  <div class="kpi green">
    <div class="kpi-icon">🛡</div>
    <div class="label">Verified Backing Candidates</div>
    <div><span class="value">{fmt(BACKING, 0)}</span><span class="unit">CELL</span></div>
    <div class="sub">On-chain reserve / backing candidates identified</div>
  </div>

  <div class="kpi amber">
    <div class="kpi-icon">⚠</div>
    <div class="label">Public MEXC Label Hits</div>
    <div><span class="value">{PUBLIC_MEXC_HITS}</span></div>
    <div class="sub">No publicly labelled MEXC endpoint detected so far</div>
  </div>
</div>
""")


# Current bridge model
anchor("bridge")
html("""
<div class="section">
  <div class="section-head">
    <div>
      <h2>Current Bridge Model</h2>
      <p>How the traced ecosystem currently appears from public on-chain evidence.</p>
    </div>
    <div class="badge green">Verified routes + open questions</div>
  </div>
  <div class="flow">
    <div class="flow-card">
      <div class="flow-num">1</div>
      <h3>Bridge-Facing Wallets</h3>
      <p>Initial wallets that interact with bridge / lock infrastructure.</p>
      <span class="addr-chip">0xfd64...c128</span><span class="addr-chip">0x4A83...b93f</span>
    </div>
    <div class="arrow">➜</div>
    <div class="flow-card">
      <div class="flow-num">2</div>
      <h3>Lock / Unlock Contracts</h3>
      <p>Bridge and lock/unlock contracts on BSC & Ethereum.</p>
      <span class="addr-chip">0x35ce...1ac</span><span class="addr-chip">0x7e9d...4b6f</span>
    </div>
    <div class="arrow">➜</div>
    <div class="flow-card purple">
      <div class="flow-num">3</div>
      <h3>Intake / Aggregator Layer</h3>
      <p>Intake wallets and aggregator addresses that consolidate inflows.</p>
      <span class="addr-chip">0x3f8c...8a21</span><span class="addr-chip">0x81c9...e764</span>
    </div>
    <div class="arrow">➜</div>
    <div class="flow-card purple">
      <div class="flow-num">4</div>
      <h3>Consolidation / Routing</h3>
      <p>Consolidation contracts and wallets route funds downstream.</p>
      <span class="addr-chip">0x65def...</span><span class="addr-chip">0xda8a...</span>
    </div>
    <div class="arrow">➜</div>
    <div class="flow-card amber">
      <div class="flow-num">5</div>
      <h3>Market Endpoints</h3>
      <p>Funds reach exchange deposit addresses and market infrastructure.</p>
      <span class="addr-chip">0x0d070... Gate.io</span>
    </div>
  </div>
</div>
""")


# Verified findings and supply glance
anchor("findings")
html(f"""
<div class="split">
  <div class="section">
    <div class="section-head">
      <div><h2>Verified Findings</h2><p>Concise summary of the main evidence-backed conclusions.</p></div>
      <div class="badge green">Evidence-backed</div>
    </div>
    <div class="card-grid">
      <div class="info-card">
        <h3>Gate.io Route Exposure</h3>
        <p>At least {fmt(GATEIO_EXPOSURE, 2)} CELL verified to Gate.io deposit address.</p>
        <span class="status ok">✓ Verified</span>
      </div>
      <div class="info-card">
        <h3>BSC Mint Path Distribution</h3>
        <p>Confirmed via BSC mint events and bridge inflows. Central wallets traced.</p>
        <span class="status ok">✓ Verified</span>
      </div>
      <div class="info-card">
        <h3>Old-CELL Claim Path</h3>
        <p>Old-CELL claim path traced. MEXC dumping remains unverified.</p>
        <span class="status ok">✓ Traced</span>
      </div>
      <div class="info-card">
        <h3>Reserve / Backing Reconciliation</h3>
        <p>Full reserve reconciliation remains in progress and unresolved.</p>
        <span class="status open">⚠ Open</span>
      </div>
    </div>
  </div>
  <div class="section">
    <div class="section-head">
      <div><h2>Supply at a Glance</h2><p>Evidence-only view of total supply, backing candidates, and exposed supply.</p></div>
      <div class="badge">Supply</div>
    </div>
    <div class="supply-panel">
      <div class="donut"><span>{compact(RAW_SUPPLY)}<br><small>TOTAL</small></span></div>
      <div>
        <div class="legend-row"><div><span class="dot"></span>Gate.io Route Exposure</div><b>{compact(GATEIO_EXPOSURE)} ({(GATEIO_EXPOSURE/RAW_SUPPLY*100):.2f}%)</b></div>
        <div class="legend-row"><div><span class="dot green"></span>Backing Candidates</div><b>{compact(BACKING)} ({(BACKING/RAW_SUPPLY*100):.2f}%)</b></div>
        <div class="legend-row"><div><span class="dot blue"></span>Other Circulating / Exposed</div><b>{compact(CIRC_EST)} ({(CIRC_EST/RAW_SUPPLY*100):.2f}%)</b></div>
        <p style="font-size:.78rem;color:#89a1b5;margin-top:10px;">Figures are approximate and on-chain verified only.</p>
      </div>
    </div>
  </div>
</div>
""")


# Route map
anchor("routes")
html(f"""
<div class="split">
  <div class="section">
    <div class="section-head">
      <div><h2>Verified Supply Path — BSC Downstream</h2><p>Primary high-level evidence route.</p></div>
      <div class="badge green">Trace map</div>
    </div>
    <div class="path-strip">
      <div class="path-node"><div class="mini">BSC Mint</div><h4>⬢ Mint</h4><p>CELL minted on BSC.</p><br><b>{compact(BSC_SUPPLY)} CELL</b></div>
      <div class="path-node"><div class="mini">Bridge / Unlock</div><h4>🔒 Unlock</h4><p>Bridge unlock contracts and flows.</p></div>
      <div class="path-node"><div class="mini">Intake / Aggregator</div><h4>⏳ Aggregator</h4><p>0x35ce / 0x7e9d style routes.</p></div>
      <div class="path-node"><div class="mini">Distribution</div><h4>👥 Wallets</h4><p>Distributed to multiple downstream wallets.</p></div>
      <div class="path-node"><div class="mini">Consolidation</div><h4>◎ Routing</h4><p>0x65def / 0xda8a consolidation.</p></div>
      <div class="path-node"><div class="mini" style="color:#ffdc69;">Gate.io Deposit</div><h4>🏦 Endpoint</h4><p>Reached 0x0d070...</p><br><b>≥ {fmt(GATEIO_EXPOSURE,2)} CELL</b></div>
    </div>
    <div class="callout">🛡 At least {fmt(GATEIO_EXPOSURE, 2)} CELL is verified as Gate.io-bound route exposure.</div>
  </div>
  <div class="section">
    <div class="section-head">
      <div><h2>Reserve / Circulating View</h2><p>How much supply can currently be excluded from circulation using verified evidence only.</p></div>
      <div class="badge amber">Estimate</div>
    </div>
    <div class="card-grid" style="grid-template-columns:1fr;">
      <div class="info-card"><h3>Raw ETH+BSC Supply</h3><p>{fmt(RAW_SUPPLY, 2)} CELL</p><span class="status ok">Contract supply</span></div>
      <div class="info-card"><h3>Verified Reserve / Backing Candidates</h3><p>{fmt(BACKING, 2)} CELL</p><span class="status ok">Evidence-backed</span></div>
      <div class="info-card"><h3>Evidence-Only Circulating Estimate</h3><p>{fmt(CIRC_EST, 2)} CELL</p><span class="status open">Estimate, not official</span></div>
    </div>
  </div>
</div>
""")


# Trust and open questions
anchor("trust")
html("""
<div class="split">
  <div class="section">
    <div class="section-head">
      <div><h2>Trust & Evidence Standard</h2><p>Why the site avoids overclaiming.</p></div>
      <div class="badge green">Public proof</div>
    </div>
    <div class="info-card"><h3>🛡 Public On-Chain Proof</h3><p>All findings are based on publicly available data on Ethereum and BSC.</p></div>
    <br>
    <div class="info-card"><h3>🔗 Trace-Based Verification</h3><p>We follow fund flows end-to-end using verifiable transaction and contract histories.</p></div>
    <br>
    <div class="info-card"><h3>👁 Limits of Exchange Visibility</h3><p>Exchange internal wallets and off-chain records are outside the scope of public on-chain audits.</p></div>
  </div>
  <div class="section">
    <div class="section-head">
      <div><h2>Key Open Questions</h2><p>Items that remain open using public data only.</p></div>
      <div class="badge amber">Open</div>
    </div>
    <div class="legend-row"><div>⚠ Full reconciliation of reserves, backing sources & liabilities</div><b>Open</b></div>
    <div class="legend-row"><div>⚠ Public MEXC dumping allegations</div><b>Open</b></div>
    <div class="legend-row"><div>⚠ Additional exchange deposit addresses and routes</div><b>In progress</b></div>
    <div class="legend-row"><div>⚠ Unknown intermediary wallets in consolidation layer</div><b>In progress</b></div>
    <div class="legend-row"><div>⚠ Reachable wallets and off-chain custodial balances</div><b>Open</b></div>
  </div>
</div>
""")


# Old-CELL claim
anchor("oldcell")
html(f"""
<div class="section">
  <div class="section-head">
    <div>
      <h2>Old-CELL / MEXC Claim Check</h2>
      <p>A public claim alleged that 5M+ old CELL was bridged back and dumped on MEXC. The bridge/unlock route is supported; the MEXC dumping part remains unverified.</p>
    </div>
    <div class="badge amber">Claim reviewed</div>
  </div>
  <div class="card-grid">
    <div class="info-card"><h3>Bridge / Unlock</h3><p>{fmt(OLD_CELL_UNLOCK, 1)} old CELL routed into 0xc3b8.</p><span class="status ok">✓ Supported</span></div>
    <div class="info-card"><h3>0xc3b8 Old-CELL Balance</h3><p>0xc3b8 routed old CELL onward and reached zero old-CELL balance.</p><span class="status ok">✓ Verified</span></div>
    <div class="info-card"><h3>Largest Held Branch</h3><p>0xa9ad held {fmt(OLD_CELL_A9AD_HELD,1)} old CELL at scan end.</p><span class="status open">⚠ Open</span></div>
    <div class="info-card"><h3>MEXC Label Check</h3><p>{PUBLIC_MEXC_HITS} publicly labelled MEXC endpoints detected in checked trace addresses.</p><span class="status no">✕ Unverified</span></div>
  </div>
</div>
""")

if not old_child.empty:
    st.markdown("#### Ten 100k Old-CELL Child Wallet Probe")
    safe_df(old_child, height=280)
if not old_secondary.empty:
    st.markdown("#### Secondary Child Wallet Probe")
    safe_df(old_secondary, height=240)
if not mexc_label.empty and {"address","status","bscscan_title"}.issubset(mexc_label.columns):
    st.markdown("#### Public MEXC Label Check")
    safe_df(mexc_label[["address","status","bscscan_title"]].head(30), height=320)


# Methodology
anchor("methodology")
html("""
<div class="section">
  <div class="section-head">
    <div><h2>Methodology</h2><p>How the audit evidence was generated and interpreted.</p></div>
    <div class="badge">Reproducible</div>
  </div>
  <div class="card-grid">
    <div class="info-card"><h3>Supply Verification</h3><p>Contract totalSupply values and mint/burn Transfer events were scanned on Ethereum and BSC.</p></div>
    <div class="info-card"><h3>Wallet Tracing</h3><p>Wallets were traced by probing balance changes and pulling Transfer logs around each change.</p></div>
    <div class="info-card"><h3>Reserve Classification</h3><p>Only verified reserve/backing candidates are excluded from conservative circulating estimates.</p></div>
    <div class="info-card"><h3>Exchange Classification</h3><p>A labelled CEX route is exchange exposure, not proof of completed exchange-side sale.</p></div>
  </div>
</div>
""")


# Evidence summary / downloads
anchor("downloads")
files = [
    "AUDIT_SUMMARY.md",
    "evidence_hashes.txt",
    "circulating_supply_estimate.json",
    "circulating_supply_estimate.csv",
    "reserve_backing_reconciliation.json",
    "reserve_backing_candidates.csv",
    "auto_trace_c3b8_summary.json",
    "auto_trace_65def_summary.json",
    "auto_trace_da8a_summary.json",
    "auto_trace_8bbf_combined_summary.json",
    "auto_trace_35ce_summary.json",
    "auto_trace_oldcell_c3b8_summary.json",
    "auto_trace_oldcell_8929_summary.json",
    "oldcell_458b_child_probe_summary.csv",
    "oldcell_secondary_child_probe_summary.csv",
    "mexc_label_check_report.csv",
    "mexc_deposit_pattern_check_report.csv",
]

html("""
<div class="section">
  <div class="section-head">
    <div><h2>Evidence Downloads / Audit Artifacts</h2><p>Generated CSV, JSON, reports, and hashes supporting the dashboard.</p></div>
    <div class="badge green">Artifacts</div>
  </div>
</div>
""")
safe_df(evidence_file_rows(files), height=400)

# Evidence hashes table
hash_path = ROOT / "evidence_hashes.txt"
if hash_path.exists():
    rows = []
    for line in hash_path.read_text().splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            rows.append({"sha256": parts[0], "file": parts[-1]})
    if rows:
        st.markdown("#### Evidence Hashes")
        safe_df(pd.DataFrame(rows).head(250), height=360)
else:
    st.warning("Missing evidence_hashes.txt. Generate with: shasum -a 256 *.csv *.json *.py > evidence_hashes.txt")


# Footer
anchor("about")
html("""
<div class="footerbar">
  <div>CELLFRAME Audit • Transparent • Verifiable • Reproducible</div>
  <div>Ethereum • BSC • Public on-chain data only</div>
  <div>This audit is for information purposes only and is not financial advice.</div>
</div>
</div>
""")
