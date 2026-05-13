
from __future__ import annotations

import json
from pathlib import Path
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import streamlit as st


# ============================================================
# CELLFRAME AUDIT DASHBOARD — PREMIUM REDESIGN
# ============================================================

st.set_page_config(
    page_title="CELLFRAME Audit",
    page_icon="⬢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(".")


# ============================================================
# DATA HELPERS
# ============================================================

def load_json(path: Path, default: Any | None = None) -> dict:
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        return default
    return default


def load_csv(path: Path) -> pd.DataFrame:
    try:
        if path.exists():
            return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame()


def D(value: Any, default: str = "0") -> Decimal:
    try:
        if value is None or value == "":
            return Decimal(default)
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def compact(value: Any) -> str:
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


def fmt(value: Any, places: int = 2) -> str:
    return f"{D(value):,.{places}f}"


def pct(part: Any, whole: Any) -> str:
    w = D(whole)
    if w == 0:
        return "0.00%"
    return f"{(D(part) / w * Decimal(100)):.2f}%"


def anchor(name: str) -> None:
    st.markdown(f'<span id="{name}" class="anchor-offset"></span>', unsafe_allow_html=True)


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def table(df: pd.DataFrame, height: int | None = None) -> None:
    if df is None or df.empty:
        return
    if height is None:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True, height=height)


def present_file_rows(files: list[str]) -> pd.DataFrame:
    rows = []
    for filename in files:
        path = ROOT / filename
        rows.append(
            {
                "artifact": filename,
                "present": "yes" if path.exists() else "no",
                "size_kb": round(path.stat().st_size / 1024, 2) if path.exists() else "",
            }
        )
    return pd.DataFrame(rows)


# ============================================================
# LOAD AUDIT ARTIFACTS
# ============================================================

reserve = load_json(ROOT / "reserve_backing_reconciliation.json")
reserve_totals = reserve.get("totals", {}) if isinstance(reserve, dict) else {}

circ = load_json(ROOT / "circulating_supply_estimate.json")
circ_inputs = circ.get("inputs", {}) if isinstance(circ, dict) else {}
circ_estimates = circ.get("estimates", {}) if isinstance(circ, dict) else {}

trace_8bbf_recipients = load_csv(ROOT / "auto_trace_8bbf_combined_recipient_summary.csv")
trace_35ce_recipients = load_csv(ROOT / "auto_trace_35ce_recipient_summary.csv")
old_child = load_csv(ROOT / "oldcell_458b_child_probe_summary.csv")
old_secondary = load_csv(ROOT / "oldcell_secondary_child_probe_summary.csv")
mexc_label = load_csv(ROOT / "mexc_label_check_report.csv")
mexc_pattern = load_csv(ROOT / "mexc_deposit_pattern_check_report.csv")
circ_csv = load_csv(ROOT / "circulating_supply_estimate.csv")

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
OLD_CELL_SECONDARY_BACK_TO_E0CA = D("308180")

PUBLIC_MEXC_HITS = 0
if not mexc_label.empty and "status" in mexc_label.columns:
    PUBLIC_MEXC_HITS += int(
        mexc_label["status"].isin(["known_mexc_label", "bscscan_page_contains_mexc_keyword"]).sum()
    )
if not mexc_pattern.empty and "status" in mexc_pattern.columns:
    PUBLIC_MEXC_HITS += int((mexc_pattern["status"] == "known_mexc_route_detected").sum())


# ============================================================
# STYLE
# ============================================================

html(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root{
  --bg:#02070f;
  --bg2:#04111d;
  --panel:#071929;
  --panel-2:#0a2034;
  --panel-3:#0a1624;
  --cyan:#20f4e8;
  --cyan-2:#08b6d2;
  --cyan-soft:rgba(32,244,232,.12);
  --blue:#3b82f6;
  --green:#19d37d;
  --amber:#f7c948;
  --orange:#fb923c;
  --purple:#a970ff;
  --red:#fb7185;
  --text:#f5fbff;
  --muted:#9fb3c8;
  --faint:#6f8398;
  --line:rgba(32,244,232,.16);
}

html{scroll-behavior:smooth;}
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
body{background:var(--bg);}
#MainMenu, header, footer{visibility:hidden;}
.block-container{
  max-width:1720px;
  padding-top:0.85rem;
  padding-bottom:3.5rem;
}
.stApp{
  color:var(--text);
  background:
    radial-gradient(circle at 72% 8%, rgba(32,244,232,.24), transparent 24%),
    radial-gradient(circle at 8% 4%, rgba(32,244,232,.12), transparent 26%),
    radial-gradient(circle at 88% 72%, rgba(59,130,246,.13), transparent 32%),
    linear-gradient(180deg,#02070f 0%,#061423 48%,#02070f 100%);
}
a{text-decoration:none;color:inherit;}
.anchor-offset{display:block;position:relative;top:-90px;visibility:hidden;}

.audit-frame{
  border:1px solid rgba(32,244,232,.18);
  border-radius:28px;
  background:linear-gradient(180deg,rgba(2,7,15,.82),rgba(3,10,20,.72));
  box-shadow:0 30px 120px rgba(0,0,0,.45), inset 0 0 0 1px rgba(255,255,255,.025);
  overflow:hidden;
}

/* NAV */
.navbar{
  position:sticky;
  top:0;
  z-index:50;
  min-height:66px;
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:18px;
  padding:0 24px;
  background:rgba(2,7,15,.82);
  backdrop-filter:blur(20px);
  border-bottom:1px solid rgba(32,244,232,.14);
}
.logo-lockup{
  display:flex;align-items:center;gap:12px;white-space:nowrap;
  font-size:1.38rem;font-weight:950;letter-spacing:-.05em;
}
.logo-cube{
  width:34px;height:34px;border-radius:10px;position:relative;
  border:2px solid rgba(32,244,232,.85);
  box-shadow:0 0 30px rgba(32,244,232,.42);
  background:linear-gradient(135deg,rgba(32,244,232,.22),rgba(32,244,232,.02));
}
.logo-cube:before{
  content:"";position:absolute;inset:7px;border:2px solid rgba(32,244,232,.76);
  transform:rotate(45deg);border-radius:6px;background:rgba(32,244,232,.08);
}
.logo-lockup .brand{color:var(--cyan);}
.logo-lockup .light{color:#fff;font-weight:850;margin-left:4px;}
.navlinks{display:flex;gap:22px;align-items:center;justify-content:center;flex-wrap:wrap;}
.navlinks a{
  color:#cad8e4;font-size:.86rem;font-weight:800;letter-spacing:-.01em;
  padding:23px 0 18px;border-bottom:3px solid transparent;
}
.navlinks a:hover,.navlinks a.active{color:#fff;border-color:var(--cyan);}
.nav-pill{
  display:flex;align-items:center;gap:8px;
  padding:9px 14px;border-radius:12px;
  color:var(--cyan);font-weight:900;font-size:.82rem;
  border:1px solid rgba(32,244,232,.36);
  background:rgba(32,244,232,.07);
}

/* HERO */
.hero{
  display:grid;
  grid-template-columns:1.02fr .98fr;
  min-height:360px;
  gap:24px;
  padding:42px 34px 20px;
  position:relative;
}
.hero-copy{z-index:2;padding-top:10px;}
.hero h1{
  font-size:clamp(3rem,5vw,5.7rem);
  line-height:.94;
  letter-spacing:-.083em;
  margin:0 0 14px;
}
.hero h1 span{color:var(--cyan);text-shadow:0 0 34px rgba(32,244,232,.26);}
.hero p{
  color:#c3d1de;
  max-width:720px;
  font-size:1.08rem;
  line-height:1.62;
  margin:0 0 18px;
}
.hero-micro{
  display:flex;gap:9px;flex-wrap:wrap;
}
.micro-pill{
  display:inline-flex;align-items:center;gap:8px;
  color:#bfeef2;background:rgba(7,25,41,.78);
  border:1px solid rgba(32,244,232,.17);
  border-radius:10px;padding:8px 11px;font-size:.8rem;font-weight:800;
}
.hero-art{
  position:relative;
  min-height:300px;
  border-radius:26px;
  overflow:hidden;
  background:
    radial-gradient(circle at 52% 31%, rgba(32,244,232,.43), transparent 13%),
    radial-gradient(circle at 52% 37%, rgba(32,244,232,.18), transparent 31%),
    linear-gradient(120deg,rgba(3,12,23,.12),rgba(32,244,232,.06));
}
.hero-art:before{
  content:"";position:absolute;inset:-40px 0 0 0;
  background-image:
    linear-gradient(rgba(32,244,232,.11) 1px,transparent 1px),
    linear-gradient(90deg,rgba(32,244,232,.11) 1px,transparent 1px);
  background-size:42px 42px;
  transform:perspective(520px) rotateX(62deg) translateY(70px);
  opacity:.8;
}
.hero-art:after{
  content:"";position:absolute;left:50%;top:58%;transform:translate(-50%,-50%);
  width:520px;height:130px;border-radius:50%;
  border:1px solid rgba(32,244,232,.16);
  box-shadow:0 0 70px rgba(32,244,232,.12);
}
.holo-coin{
  position:absolute;left:52%;top:42%;transform:translate(-50%,-50%);
  width:156px;height:156px;border-radius:50%;
  background:radial-gradient(circle at 34% 28%,#f7ffff 0,#86fff8 13%,#20f4e8 32%,#067583 66%,#04111d 100%);
  border:8px solid rgba(240,255,255,.38);
  box-shadow:0 0 22px rgba(32,244,232,.7),0 0 96px rgba(32,244,232,.46);
  animation:floaty 4.5s ease-in-out infinite;
}
.holo-coin:before{
  content:"";position:absolute;inset:34px;border:5px solid rgba(2,7,15,.88);border-radius:18px;transform:rotate(45deg);
}
.holo-coin:after{
  content:"";position:absolute;left:50%;top:50%;width:220px;height:220px;border-radius:50%;
  transform:translate(-50%,-50%);
  border:1px solid rgba(32,244,232,.18);
}
@keyframes floaty{0%,100%{transform:translate(-50%,-52%)}50%{transform:translate(-50%,-46%)}}
.art-node{
  position:absolute;width:25px;height:25px;border:1px solid rgba(32,244,232,.55);
  border-radius:7px;background:rgba(32,244,232,.08);box-shadow:0 0 20px rgba(32,244,232,.2);
}
.art-node.n1{left:17%;top:30%}.art-node.n2{right:17%;top:35%}.art-node.n3{left:28%;bottom:22%}.art-node.n4{right:28%;bottom:24%}

/* KPI */
.kpi-grid{
  display:grid;grid-template-columns:repeat(5,1fr);
  gap:14px;padding:0 24px 10px;
}
.kpi{
  min-height:152px;
  padding:18px;
  border-radius:16px;
  border:1px solid rgba(32,244,232,.18);
  background:linear-gradient(145deg,rgba(7,25,41,.92),rgba(4,14,26,.80));
  box-shadow:0 18px 70px rgba(0,0,0,.22);
}
.kpi.teal{border-color:rgba(32,244,232,.36);background:linear-gradient(145deg,rgba(5,50,58,.65),rgba(4,14,26,.82));}
.kpi.blue{border-color:rgba(59,130,246,.36);}
.kpi.green{border-color:rgba(25,211,125,.34);background:linear-gradient(145deg,rgba(6,48,37,.62),rgba(4,14,26,.82));}
.kpi.gold{border-color:rgba(247,201,72,.38);background:linear-gradient(145deg,rgba(52,39,8,.58),rgba(4,14,26,.82));}
.kpi-icon{
  width:56px;height:56px;border-radius:16px;
  display:flex;align-items:center;justify-content:center;
  border:1px solid currentColor;
  color:var(--cyan);background:rgba(32,244,232,.08);
  font-size:1.55rem;margin-bottom:10px;
}
.kpi.gold .kpi-icon{color:var(--amber);background:rgba(247,201,72,.08);}
.kpi.green .kpi-icon{color:var(--green);background:rgba(25,211,125,.08);}
.kpi.blue .kpi-icon{color:#79b7ff;background:rgba(59,130,246,.08);}
.kpi-label{font-size:.86rem;line-height:1.25;font-weight:850;color:#f4fbff;min-height:34px;}
.kpi-value{font-size:2.05rem;font-weight:950;letter-spacing:-.06em;color:var(--cyan);margin-top:4px;}
.kpi.green .kpi-value{color:#54faaa}.kpi.blue .kpi-value{color:#84bdff}.kpi.gold .kpi-value{color:#ffdb64;}
.kpi-unit{font-size:.74rem;margin-left:5px;font-weight:950;color:var(--cyan);}
.kpi-sub{margin-top:6px;font-size:.8rem;color:var(--muted);line-height:1.35;}

/* Generic sections */
.panel{
  margin:12px 16px;
  border:1px solid rgba(32,244,232,.13);
  border-radius:18px;
  background:linear-gradient(180deg,rgba(4,15,27,.74),rgba(3,11,21,.62));
  padding:20px;
  box-shadow:0 20px 80px rgba(0,0,0,.17);
}
.panel-head{
  display:flex;justify-content:space-between;align-items:flex-start;gap:18px;margin-bottom:16px;
}
.panel h2{font-size:1.38rem;margin:0;letter-spacing:-.04em;}
.panel p{color:var(--muted);line-height:1.52;margin:.3rem 0 0;}
.badge{
  display:inline-flex;align-items:center;gap:7px;
  border:1px solid rgba(32,244,232,.29);color:var(--cyan);
  background:rgba(32,244,232,.07);
  font-weight:900;border-radius:999px;padding:7px 10px;font-size:.75rem;white-space:nowrap;
}
.badge.green{color:#7dffbd;border-color:rgba(25,211,125,.35);background:rgba(25,211,125,.08);}
.badge.gold{color:#ffe17a;border-color:rgba(247,201,72,.36);background:rgba(247,201,72,.08);}
.badge.red{color:#ffa5b3;border-color:rgba(251,113,133,.36);background:rgba(251,113,133,.08);}
.card-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.card{
  border:1px solid rgba(32,244,232,.14);
  border-radius:15px;
  background:rgba(7,25,41,.64);
  padding:16px;
  min-height:142px;
}
.card h3{margin:0 0 8px;font-size:1rem;letter-spacing:-.025em;}
.card p{font-size:.84rem;color:#a9bdce;line-height:1.45;margin:0 0 10px;}
.status{
  display:inline-flex;align-items:center;gap:7px;
  border-radius:999px;padding:6px 9px;font-weight:900;font-size:.73rem;
}
.status.ok{color:#69ffaf;background:rgba(25,211,125,.12);border:1px solid rgba(25,211,125,.28);}
.status.open{color:#ffe17a;background:rgba(247,201,72,.12);border:1px solid rgba(247,201,72,.28);}
.status.no{color:#ffa5b3;background:rgba(251,113,133,.12);border:1px solid rgba(251,113,133,.28);}
.status.info{color:#a8d3ff;background:rgba(59,130,246,.12);border:1px solid rgba(59,130,246,.28);}

/* Flow */
.flow{
  display:grid;
  grid-template-columns:1fr 44px 1fr 44px 1fr 44px 1fr 44px 1fr;
  align-items:stretch;
  gap:8px;
}
.flow-card{
  border:1px solid rgba(32,244,232,.22);
  border-radius:15px;
  padding:15px;
  background:rgba(7,25,41,.68);
  min-height:176px;
}
.flow-card.purple{border-color:rgba(169,112,255,.34);}
.flow-card.gold{border-color:rgba(247,201,72,.43);}
.flow-num{
  width:32px;height:32px;border-radius:11px;
  display:flex;align-items:center;justify-content:center;
  color:var(--cyan);border:1px solid currentColor;background:rgba(32,244,232,.08);
  font-weight:950;margin-bottom:10px;
}
.flow-card.purple .flow-num{color:#d7b9ff;background:rgba(169,112,255,.1);}
.flow-card.gold .flow-num{color:#ffdd68;background:rgba(247,201,72,.1);}
.flow-card h3{margin:0 0 6px;color:#9ffdf5;font-size:1rem;}
.flow-card.purple h3{color:#d7b9ff}.flow-card.gold h3{color:#ffe17a}
.flow-card p{font-size:.81rem;color:#aac0d2;margin:0 0 8px;}
.chip{
  display:inline-flex;margin:4px 4px 0 0;padding:5px 7px;
  border-radius:7px;background:rgba(32,244,232,.08);border:1px solid rgba(32,244,232,.18);
  color:#76f7f0;font-size:.71rem;font-weight:850;
}
.arrow{
  display:flex;align-items:center;justify-content:center;
  color:var(--cyan);font-size:2.05rem;text-shadow:0 0 24px rgba(32,244,232,.75);
}

/* Split modules */
.split{display:grid;grid-template-columns:1.06fr .94fr;gap:14px;}
.route-strip{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;}
.route-node{
  min-height:164px;border:1px solid rgba(32,244,232,.18);border-radius:14px;
  padding:12px;background:rgba(7,25,41,.68);
}
.route-node .mini{font-size:.75rem;color:var(--cyan);font-weight:950;margin-bottom:8px;}
.route-node h4{margin:0 0 7px;font-size:.93rem;}
.route-node p{font-size:.76rem;color:#9eb4c9;margin:0 0 8px;}
.callout{
  margin-top:12px;border:1px solid rgba(247,201,72,.36);
  background:linear-gradient(90deg,rgba(247,201,72,.10),rgba(32,244,232,.04));
  color:#ffe17a;
  padding:13px 15px;border-radius:14px;font-weight:950;
}
.supply-card{display:grid;grid-template-columns:220px 1fr;gap:18px;align-items:center;}
.donut{
  width:184px;height:184px;margin:auto;border-radius:50%;
  background:conic-gradient(var(--cyan) 0 4.09%, var(--green) 4.09% 5.65%, rgba(59,130,246,.88) 5.65% 100%);
  display:flex;align-items:center;justify-content:center;position:relative;
  box-shadow:0 0 60px rgba(32,244,232,.13);
}
.donut:after{
  content:"";position:absolute;inset:39px;border-radius:50%;
  background:#071929;border:1px solid rgba(32,244,232,.18);
}
.donut span{position:relative;z-index:2;text-align:center;font-weight:950;font-size:1.1rem;}
.legend-row{
  display:grid;grid-template-columns:1fr auto;gap:12px;
  padding:10px 0;border-bottom:1px solid rgba(32,244,232,.10);
  color:#d4e2ec;font-size:.86rem;
}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px;background:var(--cyan);}
.dot.green{background:var(--green)}.dot.blue{background:var(--blue)}

.download-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.download-card{
  border:1px solid rgba(32,244,232,.15);border-radius:15px;background:rgba(7,25,41,.64);
  padding:16px;min-height:112px;
}
.download-card h3{font-size:1rem;margin:0 0 8px;}
.download-card p{font-size:.82rem;color:#9fb3c8;margin:0;}

[data-testid="stDataFrame"]{
  border:1px solid rgba(32,244,232,.13)!important;
  border-radius:14px!important;
  overflow:hidden!important;
}
[data-testid="stDataFrame"] *{font-family:'Inter',sans-serif!important;}

.footer{
  margin:16px 18px 0;
  padding:18px;
  display:flex;justify-content:space-between;align-items:center;gap:20px;
  border-top:1px solid rgba(32,244,232,.12);
  color:#8fa4b6;font-size:.8rem;
}

@media(max-width:1300px){
  .hero{grid-template-columns:1fr;}
  .kpi-grid{grid-template-columns:repeat(2,1fr);}
  .card-grid{grid-template-columns:repeat(2,1fr);}
  .flow{grid-template-columns:1fr;}
  .arrow{transform:rotate(90deg);height:26px;}
  .split{grid-template-columns:1fr;}
  .route-strip{grid-template-columns:repeat(2,1fr);}
}
@media(max-width:760px){
  .navbar{align-items:flex-start;flex-direction:column;border-radius:0;padding:15px;}
  .navlinks{gap:13px;justify-content:flex-start;}
  .navlinks a{padding:2px 0;border-bottom:0;}
  .hero{padding:25px 16px;}
  .kpi-grid{grid-template-columns:1fr;padding:0 14px 10px;}
  .card-grid,.route-strip,.download-grid{grid-template-columns:1fr;}
  .panel{margin:10px 8px;padding:16px;}
  .supply-card{grid-template-columns:1fr;}
  .footer{flex-direction:column;align-items:flex-start;}
}
</style>
"""
)


# ============================================================
# RENDER
# ============================================================

html('<div class="audit-frame">')

# NAV
html(
    """
<div class="navbar">
  <div class="logo-lockup">
    <div class="logo-cube"></div>
    <div><span class="brand">CELLFRAME</span><span class="light">Audit</span></div>
  </div>
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
  <div class="nav-pill">🛡 On-Chain Only</div>
</div>
"""
)

# HERO
anchor("overview")
html(
    """
<section class="hero">
  <div class="hero-copy">
    <h1>CELLFRAME <span>On-Chain Audit</span></h1>
    <p>
      Independent on-chain evidence of CELL / CELLFRAME: supply tracing,
      bridge analysis, reserve candidates, downstream wallet routing, and market-route verification.
    </p>
    <div class="hero-micro">
      <div class="micro-pill">🛡 Public on-chain evidence only</div>
      <div class="micro-pill">🔒 No private or off-chain data used</div>
      <div class="micro-pill">🔎 Reproducible CSV / JSON evidence</div>
    </div>
  </div>
  <div class="hero-art">
    <div class="holo-coin"></div>
    <div class="art-node n1"></div>
    <div class="art-node n2"></div>
    <div class="art-node n3"></div>
    <div class="art-node n4"></div>
  </div>
</section>
"""
)

# KPIS
html(
    f"""
<section class="kpi-grid">
  <div class="kpi teal">
    <div class="kpi-icon">⬢</div>
    <div class="kpi-label">Total Supply Snapshot</div>
    <div class="kpi-value">{compact(RAW_SUPPLY)}<span class="kpi-unit">CELL</span></div>
    <div class="kpi-sub">Across Ethereum & BSC</div>
  </div>
  <div class="kpi teal">
    <div class="kpi-icon">👥</div>
    <div class="kpi-label">Evidence-Only Circulating Estimate</div>
    <div class="kpi-value">{compact(CIRC_EST)}<span class="kpi-unit">CELL</span></div>
    <div class="kpi-sub">On-chain verified estimate</div>
  </div>
  <div class="kpi blue">
    <div class="kpi-icon">↪</div>
    <div class="kpi-label">Verified Gate.io Route Exposure</div>
    <div class="kpi-value">{compact(GATEIO_EXPOSURE)}<span class="kpi-unit">CELL</span></div>
    <div class="kpi-sub">≥ {fmt(GATEIO_EXPOSURE, 2)} CELL Gate.io-bound route</div>
  </div>
  <div class="kpi green">
    <div class="kpi-icon">🛡</div>
    <div class="kpi-label">Verified Backing Candidates</div>
    <div class="kpi-value">{fmt(BACKING, 0)}<span class="kpi-unit">CELL</span></div>
    <div class="kpi-sub">On-chain reserve / backing candidates identified</div>
  </div>
  <div class="kpi gold">
    <div class="kpi-icon">⚠</div>
    <div class="kpi-label">Public MEXC Label Hits</div>
    <div class="kpi-value">{PUBLIC_MEXC_HITS}</div>
    <div class="kpi-sub">No publicly labelled MEXC endpoint detected so far</div>
  </div>
</section>
"""
)

# BRIDGE MODEL
anchor("bridge")
html(
    """
<section class="panel">
  <div class="panel-head">
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
      <p>Initial wallets that interact with bridge / lock contracts.</p>
      <span class="chip">0xfd64...c128</span><span class="chip">0x4A83...b93f</span><span class="chip">+6 more</span>
    </div>
    <div class="arrow">➜</div>
    <div class="flow-card">
      <div class="flow-num">2</div>
      <h3>Lock / Unlock Contracts</h3>
      <p>Bridge and lock/unlock contracts on BSC & Ethereum.</p>
      <span class="chip">0x35ce...1ac</span><span class="chip">0x7e9d...4b6f</span><span class="chip">+6 more</span>
    </div>
    <div class="arrow">➜</div>
    <div class="flow-card purple">
      <div class="flow-num">3</div>
      <h3>Intake / Aggregator Layer</h3>
      <p>Aggregator wallets receive and consolidate flows.</p>
      <span class="chip">0x3f8c...8a21</span><span class="chip">0x81c9...e764</span><span class="chip">+7 more</span>
    </div>
    <div class="arrow">➜</div>
    <div class="flow-card purple">
      <div class="flow-num">4</div>
      <h3>Consolidation / Routing</h3>
      <p>Consolidation contracts route funds to downstream destinations.</p>
      <span class="chip">0x65def...</span><span class="chip">0xda8a...</span>
    </div>
    <div class="arrow">➜</div>
    <div class="flow-card gold">
      <div class="flow-num">5</div>
      <h3>Market Endpoints</h3>
      <p>Funds reach exchange deposit addresses and market infrastructure.</p>
      <span class="chip">0x0d070... Gate.io</span>
    </div>
  </div>
</section>
"""
)

# FINDINGS + SUPPLY
anchor("findings")
html(
    f"""
<section class="split">
  <div class="panel">
    <div class="panel-head">
      <div><h2>Verified Findings</h2><p>Concise summary of the main evidence-backed conclusions.</p></div>
      <div class="badge green">Evidence-backed</div>
    </div>
    <div class="card-grid">
      <div class="card">
        <h3>Gate.io Route Exposure</h3>
        <p>At least {fmt(GATEIO_EXPOSURE, 2)} CELL verified to Gate.io deposit address.</p>
        <span class="status ok">✓ Verified</span>
      </div>
      <div class="card">
        <h3>BSC Mint Path Distribution</h3>
        <p>Confirmed via BSC mint events and bridge inflows. Central wallets traced.</p>
        <span class="status ok">✓ Verified</span>
      </div>
      <div class="card">
        <h3>Old-CELL Claim Path</h3>
        <p>Old-CELL path traced. MEXC dumping remains unverified.</p>
        <span class="status info">Traced</span>
      </div>
      <div class="card">
        <h3>Reserve / Backing Reconciliation</h3>
        <p>Full reserve reconciliation remains in progress and unresolved.</p>
        <span class="status open">⚠ Open</span>
      </div>
    </div>
  </div>

  <div class="panel">
    <div class="panel-head">
      <div><h2>Supply at a Glance</h2><p>Total supply, backing candidates, and evidence-only exposed supply.</p></div>
      <div class="badge">Supply</div>
    </div>
    <div class="supply-card">
      <div class="donut"><span>{compact(RAW_SUPPLY)}<br><small>TOTAL</small></span></div>
      <div>
        <div class="legend-row"><div><span class="dot"></span>Gate.io Route Exposure</div><b>{compact(GATEIO_EXPOSURE)} ({pct(GATEIO_EXPOSURE, RAW_SUPPLY)})</b></div>
        <div class="legend-row"><div><span class="dot green"></span>Backing Candidates</div><b>{compact(BACKING)} ({pct(BACKING, RAW_SUPPLY)})</b></div>
        <div class="legend-row"><div><span class="dot blue"></span>Other Circulating / Exposed</div><b>{compact(CIRC_EST)} ({pct(CIRC_EST, RAW_SUPPLY)})</b></div>
        <p style="font-size:.78rem;color:#89a1b5;margin-top:10px;">Figures are approximate and on-chain verified only.</p>
      </div>
    </div>
  </div>
</section>
"""
)

# ROUTES
anchor("routes")
html(
    f"""
<section class="split">
  <div class="panel">
    <div class="panel-head">
      <div><h2>Verified Supply Path — BSC Downstream</h2><p>Primary high-level evidence route.</p></div>
      <div class="badge green">Trace map</div>
    </div>
    <div class="route-strip">
      <div class="route-node"><div class="mini">BSC Mint</div><h4>⬢ Mint</h4><p>CELL minted on BSC.</p><br><b>{compact(BSC_SUPPLY)} CELL</b></div>
      <div class="route-node"><div class="mini">Bridge / Unlock</div><h4>🔒 Unlock</h4><p>Bridge unlock contracts and flows.</p></div>
      <div class="route-node"><div class="mini">Intake / Aggregator</div><h4>⏳ Aggregator</h4><p>0x35ce / 0x7e9d style routes.</p></div>
      <div class="route-node"><div class="mini">Distribution</div><h4>👥 Wallets</h4><p>Distributed to multiple downstream wallets.</p></div>
      <div class="route-node"><div class="mini">Consolidation</div><h4>◎ Routing</h4><p>0x65def / 0xda8a consolidation.</p></div>
      <div class="route-node"><div class="mini" style="color:#ffdc69;">Gate.io Deposit</div><h4>🏦 Endpoint</h4><p>Reached 0x0d070...</p><br><b>≥ {fmt(GATEIO_EXPOSURE,2)} CELL</b></div>
    </div>
    <div class="callout">🛡 At least {fmt(GATEIO_EXPOSURE, 2)} CELL is verified as Gate.io-bound route exposure.</div>
  </div>

  <div class="panel">
    <div class="panel-head">
      <div><h2>Reserve / Circulating View</h2><p>Verified exclusions from circulation using evidence only.</p></div>
      <div class="badge gold">Estimate</div>
    </div>
    <div class="card-grid" style="grid-template-columns:1fr;">
      <div class="card"><h3>Raw ETH+BSC Supply</h3><p>{fmt(RAW_SUPPLY, 2)} CELL</p><span class="status ok">Contract supply</span></div>
      <div class="card"><h3>Verified Reserve / Backing Candidates</h3><p>{fmt(BACKING, 2)} CELL</p><span class="status ok">Evidence-backed</span></div>
      <div class="card"><h3>Evidence-Only Circulating Estimate</h3><p>{fmt(CIRC_EST, 2)} CELL</p><span class="status open">Estimate, not official</span></div>
    </div>
  </div>
</section>
"""
)

# CLAIM CHECK / TRUST
anchor("trust")
html(
    f"""
<section class="split">
  <div class="panel">
    <div class="panel-head">
      <div><h2>Trust & Evidence Standard</h2><p>Why the site avoids overclaiming.</p></div>
      <div class="badge green">Public proof</div>
    </div>
    <div class="card"><h3>🛡 Public On-Chain Proof</h3><p>All findings are based on publicly available data on Ethereum and BSC.</p></div>
    <br>
    <div class="card"><h3>🔗 Trace-Based Verification</h3><p>We follow fund flows end-to-end using verifiable transaction and contract histories.</p></div>
    <br>
    <div class="card"><h3>👁 Limits of Exchange Visibility</h3><p>Exchange internal wallets and off-chain records are outside the scope of public on-chain audits.</p></div>
  </div>

  <div class="panel">
    <div class="panel-head">
      <div><h2>Key Open Questions</h2><p>Items that remain open using public data only.</p></div>
      <div class="badge gold">Open</div>
    </div>
    <div class="legend-row"><div>⚠ Full reconciliation of reserves, backing sources & liabilities</div><b>Open</b></div>
    <div class="legend-row"><div>⚠ Public MEXC dumping allegations — verification pending</div><b>Open</b></div>
    <div class="legend-row"><div>⚠ Additional exchange deposit addresses and routes</div><b>In progress</b></div>
    <div class="legend-row"><div>⚠ Unknown intermediary wallets in consolidation layer</div><b>In progress</b></div>
    <div class="legend-row"><div>⚠ Reachable wallets and off-chain custodial balances</div><b>Open</b></div>
  </div>
</section>
"""
)

anchor("oldcell")
html(
    f"""
<section class="panel">
  <div class="panel-head">
    <div>
      <h2>Old-CELL / MEXC Claim Check</h2>
      <p>A public claim alleged that 5M+ old CELL was bridged back and dumped on MEXC. The bridge/unlock route is supported; the MEXC dumping part remains unverified.</p>
    </div>
    <div class="badge gold">Claim reviewed</div>
  </div>
  <div class="card-grid">
    <div class="card"><h3>Bridge / Unlock</h3><p>{fmt(OLD_CELL_UNLOCK, 1)} old CELL routed into 0xc3b8.</p><span class="status ok">✓ Supported</span></div>
    <div class="card"><h3>0xc3b8 Old-CELL Balance</h3><p>0xc3b8 routed old CELL onward and reached zero old-CELL balance.</p><span class="status ok">✓ Verified</span></div>
    <div class="card"><h3>Largest Held Branch</h3><p>0xa9ad held {fmt(OLD_CELL_A9AD_HELD,1)} old CELL at scan end.</p><span class="status open">⚠ Open</span></div>
    <div class="card"><h3>MEXC Label Check</h3><p>{PUBLIC_MEXC_HITS} publicly labelled MEXC endpoints detected in checked trace addresses.</p><span class="status no">✕ Unverified</span></div>
  </div>
</section>
"""
)

if not old_child.empty:
    st.markdown("#### Ten 100k Old-CELL Child Wallet Probe")
    table(old_child, 280)
if not old_secondary.empty:
    st.markdown("#### Secondary Child Wallet Probe")
    table(old_secondary, 240)
if not mexc_label.empty and {"address", "status", "bscscan_title"}.issubset(mexc_label.columns):
    st.markdown("#### Public MEXC Label Check")
    table(mexc_label[["address", "status", "bscscan_title"]].head(30), 320)
if not mexc_pattern.empty:
    visible = [c for c in ["address", "status", "oldcell_out_total", "oldcell_out_txs", "exchange_deposit_like_heuristic"] if c in mexc_pattern.columns]
    if visible:
        st.markdown("#### MEXC Deposit-Pattern Check")
        table(mexc_pattern[visible].head(40), 320)

# Detailed branches
html(
    """
<section class="panel">
  <div class="panel-head">
    <div><h2>Key Evidence Claims</h2><p>Condensed route-specific evidence cards.</p></div>
    <div class="badge">Evidence summary</div>
  </div>
  <div class="card-grid" style="grid-template-columns:repeat(3,1fr);">
    <div class="card">
      <h3>Gate.io Route Exposure</h3>
      <p>Consolidation via 0x65def / 0xda8a to Gate.io deposit endpoint 0x0d070...</p>
      <div class="callout">At least 2,596,567.55 CELL verified</div>
    </div>
    <div class="card">
      <h3>Old-CELL Claim Path</h3>
      <p>Bridge/unlock → 0xc3b8 → 0x8929 → 0xa9ad / 0x458b branches.</p>
      <div class="callout">MEXC claim remains unverified</div>
    </div>
    <div class="card">
      <h3>Reserve / Circulating View</h3>
      <p>Evidence-only circulating estimate is approximately 62.61M CELL.</p>
      <div class="callout">Not official supply guidance</div>
    </div>
  </div>
</section>
"""
)

# Methodology
anchor("methodology")
html(
    """
<section class="panel">
  <div class="panel-head">
    <div><h2>Methodology</h2><p>How the audit evidence was generated and interpreted.</p></div>
    <div class="badge">Reproducible</div>
  </div>
  <div class="card-grid">
    <div class="card"><h3>Supply Verification</h3><p>Contract totalSupply values and mint/burn Transfer events were scanned on Ethereum and BSC.</p></div>
    <div class="card"><h3>Wallet Tracing</h3><p>Wallets were traced by probing balance changes and pulling Transfer logs around each change.</p></div>
    <div class="card"><h3>Reserve Classification</h3><p>Only verified reserve/backing candidates are excluded from conservative circulating estimates.</p></div>
    <div class="card"><h3>Exchange Classification</h3><p>A labelled CEX route is exchange exposure, not proof of completed exchange-side sale.</p></div>
  </div>
</section>
"""
)

# Evidence downloads
anchor("downloads")
artifact_files = [
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

html(
    """
<section class="panel">
  <div class="panel-head">
    <div><h2>Evidence Downloads / Audit Artifacts</h2><p>Generated CSV, JSON, reports, and hashes supporting the dashboard.</p></div>
    <div class="badge green">Artifacts</div>
  </div>
</section>
"""
)
table(present_file_rows(artifact_files), 400)

hash_path = ROOT / "evidence_hashes.txt"
if hash_path.exists():
    rows = []
    for line in hash_path.read_text().splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            rows.append({"sha256": parts[0], "file": parts[-1]})
    if rows:
        st.markdown("#### Evidence Hashes")
        table(pd.DataFrame(rows).head(250), 360)
else:
    st.warning("Missing evidence_hashes.txt. Generate with: shasum -a 256 *.csv *.json *.py > evidence_hashes.txt")

# Footer
anchor("about")
html(
    """
<div class="footer">
  <div>CELLFRAME Audit • Transparent • Verifiable • Reproducible</div>
  <div>Ethereum • BSC • Public on-chain data only</div>
  <div>This audit is for information purposes only and is not financial advice.</div>
</div>
</div>
"""
)
