from pathlib import Path

APP = Path("app.py")

if not APP.exists():
    raise FileNotFoundError("app.py not found. Run this from the folder containing app.py.")

BACKUP = Path("app.py.bak_live_bridge_model")
if not BACKUP.exists():
    BACKUP.write_text(APP.read_text())

text = APP.read_text()

CSS = r'''
/* ==============================
   POLISHED LIVE CURRENT BRIDGE MODEL
   ============================== */

.live-bridge-model {
    border:1px solid rgba(56,189,248,.20);
    background:
        radial-gradient(circle at 14% 9%, rgba(56,189,248,.12), transparent 28%),
        radial-gradient(circle at 86% 11%, rgba(168,85,247,.10), transparent 24%),
        linear-gradient(180deg, rgba(4,14,28,.98), rgba(3,10,20,.98));
    border-radius:26px;
    padding:22px;
    box-shadow:0 28px 70px rgba(0,0,0,.38), inset 0 0 0 1px rgba(255,255,255,.025);
    overflow:hidden;
    margin-bottom:1.25rem;
}

.live-bridge-head {
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    gap:18px;
    flex-wrap:wrap;
    padding-bottom:16px;
    border-bottom:1px solid rgba(59,130,246,.22);
    margin-bottom:18px;
}

.live-bridge-title {
    margin:0;
    color:#f8fafc;
    font-size:2.05rem;
    line-height:1.05;
    letter-spacing:-.05em;
    font-weight:950;
}

.live-bridge-subtitle {
    margin-top:8px;
    color:#93c5fd;
    font-size:1rem;
    line-height:1.5;
    font-weight:650;
}

.live-bridge-chip {
    display:inline-flex;
    align-items:center;
    gap:8px;
    padding:12px 18px;
    border-radius:999px;
    border:1px solid rgba(34,197,94,.38);
    background:rgba(34,197,94,.11);
    color:#86efac;
    font-size:.93rem;
    font-weight:900;
    white-space:nowrap;
    box-shadow:0 0 26px rgba(34,197,94,.10);
}

.live-bridge-stats {
    display:grid;
    grid-template-columns:repeat(4, minmax(170px, 1fr));
    gap:12px;
    margin-bottom:22px;
}

.live-stat {
    border-radius:16px;
    border:1px solid rgba(148,163,184,.16);
    background:rgba(8,18,34,.72);
    padding:14px 16px;
    min-height:92px;
    box-shadow:inset 0 0 0 1px rgba(255,255,255,.02);
}

.live-stat-label {
    color:#cbd5e1;
    font-size:.84rem;
    font-weight:800;
    margin-bottom:6px;
}

.live-stat-value {
    font-size:2rem;
    line-height:1;
    font-weight:950;
    letter-spacing:-.05em;
}

.live-stat-note {
    margin-top:7px;
    color:#94a3b8;
    font-size:.75rem;
    line-height:1.38;
}

.stat-blue .live-stat-value{ color:#60a5fa; }
.stat-green .live-stat-value{ color:#4ade80; }
.stat-purple .live-stat-value{ color:#c084fc; }
.stat-cyan .live-stat-value{ color:#67e8f9; }

.live-flow {
    display:grid;
    grid-template-columns:minmax(185px,1fr) 96px minmax(185px,1fr) 96px minmax(185px,1fr) 96px minmax(185px,1fr) 96px minmax(185px,1fr);
    gap:12px;
    align-items:stretch;
}

.live-stage {
    position:relative;
    min-height:535px;
    border-radius:22px;
    padding:18px 16px 16px;
    background:linear-gradient(180deg, rgba(14,27,46,.92), rgba(7,17,32,.94));
    overflow:hidden;
}

.live-stage:before {
    content:"";
    position:absolute;
    inset:0;
    pointer-events:none;
    background:
        radial-gradient(circle at 50% 0%, rgba(255,255,255,.055), transparent 40%),
        linear-gradient(180deg, rgba(255,255,255,.015), transparent);
}

.live-stage-inner {
    position:relative;
    z-index:1;
    height:100%;
    display:flex;
    flex-direction:column;
}

.live-stage-blue {
    border:1px solid rgba(56,189,248,.50);
    box-shadow:0 0 28px rgba(56,189,248,.14), inset 0 0 20px rgba(56,189,248,.055);
}
.live-stage-purple {
    border:1px solid rgba(168,85,247,.52);
    box-shadow:0 0 28px rgba(168,85,247,.16), inset 0 0 20px rgba(168,85,247,.055);
}
.live-stage-green {
    border:1px solid rgba(34,197,94,.48);
    box-shadow:0 0 28px rgba(34,197,94,.15), inset 0 0 20px rgba(34,197,94,.055);
}
.live-stage-orange {
    border:1px solid rgba(245,158,11,.50);
    box-shadow:0 0 28px rgba(245,158,11,.16), inset 0 0 20px rgba(245,158,11,.055);
}

.live-stage-num {
    width:52px;
    height:38px;
    border-radius:12px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:1.18rem;
    font-weight:950;
    color:#e0f2fe;
    border:1px solid rgba(125,211,252,.35);
    background:rgba(56,189,248,.10);
    margin-bottom:14px;
}

.live-stage-title {
    color:#f8fafc;
    font-size:1.12rem;
    font-weight:950;
    line-height:1.16;
    min-height:64px;
}

.live-stage-icon {
    width:82px;
    height:82px;
    border-radius:999px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:2rem;
    margin:13px auto 12px;
    border:1px solid rgba(125,211,252,.25);
    background:rgba(3,15,30,.66);
    box-shadow:inset 0 0 18px rgba(255,255,255,.04), 0 0 20px rgba(56,189,248,.10);
}

.live-stage-status {
    display:inline-flex;
    align-self:flex-start;
    padding:8px 16px;
    border-radius:999px;
    font-size:.88rem;
    font-weight:950;
    margin-bottom:14px;
    border:1px solid rgba(56,189,248,.32);
    background:rgba(56,189,248,.10);
    color:#7dd3fc;
}

.live-bullets {
    margin:0;
    padding-left:18px;
    color:#cbd5e1;
    font-size:.88rem;
    line-height:1.52;
}

.live-bullets li { margin-bottom:5px; }

.live-addresses {
    margin-top:auto;
    padding-top:14px;
    display:flex;
    flex-direction:column;
    gap:9px;
}

.live-address {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:10px;
    text-decoration:none !important;
    border:1px solid rgba(59,130,246,.30);
    background:rgba(2,14,28,.74);
    padding:10px 11px;
    border-radius:12px;
    transition:all .15s ease;
}

.live-address:hover {
    transform:translateY(-1px);
    border-color:rgba(125,211,252,.62);
    box-shadow:0 0 16px rgba(56,189,248,.15);
    background:rgba(14,165,233,.10);
}

.live-address-name {
    color:#e2e8f0;
    font-size:.80rem;
    font-weight:900;
    line-height:1.2;
}

.live-address-addr {
    color:#7dd3fc;
    font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size:.74rem;
    margin-top:3px;
}

.live-address-ext {
    color:#67e8f9;
    font-size:1.05rem;
    font-weight:950;
}

.live-arrow-wrap {
    display:flex;
    align-items:center;
    justify-content:center;
}

.live-arrow {
    width:100%;
    min-height:124px;
    clip-path:polygon(0 30%, 62% 30%, 62% 12%, 100% 50%, 62% 88%, 62% 70%, 0 70%);
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    color:white;
    font-size:1.20rem;
    line-height:1.14;
    font-weight:950;
    padding:18px;
    letter-spacing:-.035em;
}

.live-arrow-blue {
    background:linear-gradient(90deg, rgba(56,189,248,.14), rgba(59,130,246,.92));
    box-shadow:0 0 32px rgba(56,189,248,.28);
}
.live-arrow-purple {
    background:linear-gradient(90deg, rgba(168,85,247,.14), rgba(192,132,252,.92));
    box-shadow:0 0 32px rgba(168,85,247,.28);
}
.live-arrow-cyan {
    background:linear-gradient(90deg, rgba(14,165,233,.14), rgba(34,211,238,.92));
    box-shadow:0 0 32px rgba(34,211,238,.28);
}
.live-arrow-green {
    background:linear-gradient(90deg, rgba(34,197,94,.14), rgba(74,222,128,.92));
    box-shadow:0 0 32px rgba(34,197,94,.28);
}

.live-legend {
    margin-top:18px;
    display:grid;
    grid-template-columns:repeat(4, minmax(170px,1fr));
    gap:12px;
}

.live-legend-item {
    border:1px solid rgba(148,163,184,.14);
    background:rgba(8,18,34,.72);
    border-radius:16px;
    padding:14px 16px;
}

.live-legend-title {
    font-size:.90rem;
    font-weight:950;
    margin-bottom:6px;
}

.live-legend-copy {
    color:#cbd5e1;
    font-size:.80rem;
    line-height:1.44;
}

.legend-blue .live-legend-title { color:#7dd3fc; }
.legend-purple .live-legend-title { color:#d8b4fe; }
.legend-orange .live-legend-title { color:#fcd34d; }
.legend-green .live-legend-title { color:#86efac; }

@media (max-width:1500px) {
    .live-flow { grid-template-columns:1fr; }
    .live-stage { min-height:auto; }
    .live-arrow { clip-path:none; border-radius:16px; min-height:74px; }
}
@media (max-width:1100px) {
    .live-bridge-stats, .live-legend { grid-template-columns:1fr 1fr; }
}
@media (max-width:720px) {
    .live-bridge-stats, .live-legend { grid-template-columns:1fr; }
    .live-bridge-title { font-size:1.55rem; }
}
'''

FUNCTION = r'''
def bridge_short_addr(addr):
    addr = str(addr)
    if len(addr) < 14:
        return addr
    return f"{addr[:8]}...{addr[-6:]}"


def bridge_explorer_url(addr, chain="eth"):
    base = "https://etherscan.io/address/" if chain == "eth" else "https://bscscan.com/address/"
    return f"{base}{addr}"


def bridge_address_pills(addresses):
    parts = []
    for item in addresses:
        label = item.get("label", bridge_short_addr(item["address"]))
        addr = item["address"]
        chain = item.get("chain", "eth")
        url = bridge_explorer_url(addr, chain)
        parts.append(
            f"""
            <a class="live-address" href="{url}" target="_blank">
                <div>
                    <div class="live-address-name">{label}</div>
                    <div class="live-address-addr">{bridge_short_addr(addr)}</div>
                </div>
                <div class="live-address-ext">↗</div>
            </a>
            """
        )
    return "".join(parts)


def render_current_bridge_model_live(bridge, metrics):
    bridge_contracts = int(
        bridge.get("bridge_contracts_identified",
        bridge.get("identified_contract_count", 15)) or 15
    )
    reserve_flows = int(
        bridge.get("reserve_flows_observed",
        bridge.get("supported_reserve_flow_count", 12)) or 12
    )
    market_routes = int(
        bridge.get("market_routes_detected",
        metrics.get("terminal_endpoint_count", 9)) or 9
    )
    reachable = int(metrics.get("reachable_wallets") or 0)

    stages = [
        {
            "num": "01",
            "title": "Bridge-Facing<br>Wallets",
            "icon": "💼",
            "status": "Identified",
            "klass": "live-stage-blue",
            "bullets": [
                "Externally owned / bridge-facing wallets",
                "Bridge entry points",
                "High-value fund receipt",
            ],
            "addresses": [
                {"label": "Bridge Intake", "address": "0x4a831a8ebb160ad025d34a788c99e9320b9ab531", "chain": "eth"},
                {"label": "Lock / Unlock", "address": "0xfd64fa5976687c2048f08f5df89c9a78e31df680", "chain": "eth"},
            ],
        },
        {
            "num": "02",
            "title": "Lock / Unlock<br>Contracts",
            "icon": "🔒",
            "status": "Supported",
            "klass": "live-stage-purple",
            "bullets": [
                "Lock Token method observed",
                "Unlock Token method observed",
                "Bridge Token routing observed",
            ],
            "addresses": [
                {"label": "Lock / Unlock Contract", "address": "0xfd64fa5976687c2048f08f5df89c9a78e31df680", "chain": "eth"},
                {"label": "Bridge Token Target", "address": "0x4a831a8ebb160ad025d34a788c99e9320b9ab531", "chain": "eth"},
            ],
        },
        {
            "num": "03",
            "title": "Intake /<br>Aggregator Layer",
            "icon": "🧱",
            "status": "Observed",
            "klass": "live-stage-blue",
            "bullets": [
                "Intake of released assets",
                "Aggregation and batching",
                "Pre-routing staging layer",
            ],
            "addresses": [
                {"label": "Aggregator", "address": "0x35ce1677d3d6aaaacd96510704d3c8617a12ee60", "chain": "eth"},
                {"label": "Major Distributor", "address": "0x50ebb0827aa80ba1a2a30b38581629996262d481", "chain": "eth"},
                {"label": "Distributor", "address": "0x65def3ea531fd80354ec11c611ae4faa06068f27", "chain": "eth"},
            ],
        },
        {
            "num": "04",
            "title": "Consolidation /<br>Routing",
            "icon": "🔀",
            "status": "Observed",
            "klass": "live-stage-green",
            "bullets": [
                "Consolidation of flows",
                "Routing optimization",
                "Multi-path distribution",
            ],
            "addresses": [
                {"label": "Consolidation", "address": "0xda8a4204de68f959ca2302c4febc4ee5b6cc32f5", "chain": "eth"},
                {"label": "Router Hub", "address": "0x9c4cc862f51b1ba90485de3502aa058ca4331f32", "chain": "eth"},
                {"label": "Distributor", "address": "0xd3ec4a0113091ed2b0a3edbfdf1476efe07c8539", "chain": "eth"},
            ],
        },
        {
            "num": "05",
            "title": "Market<br>Endpoints",
            "icon": "🌐",
            "status": "Observed",
            "klass": "live-stage-orange",
            "bullets": [
                "CEX deposit endpoints",
                "DEX liquidity and router hubs",
                "Swap aggregator routes",
            ],
            "addresses": [
                {"label": "Gate.io 1", "address": "0x0d0707963952f2fba59dd06f2b425ace40b492fe", "chain": "eth"},
                {"label": "MEXC 1", "address": "0x75e89d5979e4f6fba9f97c104c2f0afb3f1dcb88", "chain": "eth"},
                {"label": "Uniswap Router", "address": "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad", "chain": "eth"},
                {"label": "1inch Router", "address": "0x1111111254eeb25477b68fb85ed929f73a960582", "chain": "eth"},
                {"label": "ParaSwap", "address": "0xdef171fe48cf0115b1d80b88dc8eab59176fee57", "chain": "eth"},
            ],
        },
    ]

    arrows = [
        ("Locked /<br>bridged", "live-arrow-blue"),
        ("Released /<br>routed", "live-arrow-purple"),
        ("Consolidated", "live-arrow-cyan"),
        ("Routed to<br>market", "live-arrow-green"),
    ]

    flow_parts = []
    for idx, stage in enumerate(stages):
        bullets = "".join(f"<li>{b}</li>" for b in stage["bullets"])
        addresses = bridge_address_pills(stage["addresses"])

        flow_parts.append(
            f"""
            <div class="live-stage {stage["klass"]}">
                <div class="live-stage-inner">
                    <div class="live-stage-num">{stage["num"]}</div>
                    <div class="live-stage-title">{stage["title"]}</div>
                    <div class="live-stage-icon">{stage["icon"]}</div>
                    <div class="live-stage-status">{stage["status"]}</div>
                    <ul class="live-bullets">{bullets}</ul>
                    <div class="live-addresses">{addresses}</div>
                </div>
            </div>
            """
        )

        if idx < len(arrows):
            label, klass = arrows[idx]
            flow_parts.append(
                f"""
                <div class="live-arrow-wrap">
                    <div class="live-arrow {klass}">{label}</div>
                </div>
                """
            )

    html = f"""
    <div class="live-bridge-model">
        <div class="live-bridge-head">
            <div>
                <h2 class="live-bridge-title">Current Bridge Model</h2>
                <div class="live-bridge-subtitle">Observed bridge infrastructure and downstream routing paths</div>
            </div>
            <div class="live-bridge-chip">● Audit evidence: On-chain verified</div>
        </div>

        <div class="live-bridge-stats">
            <div class="live-stat stat-blue">
                <div class="live-stat-label">Bridge contracts identified</div>
                <div class="live-stat-value">{bridge_contracts}</div>
                <div class="live-stat-note">Lock / unlock and bridge-facing infrastructure identified</div>
            </div>
            <div class="live-stat stat-green">
                <div class="live-stat-label">Reserve flow observed</div>
                <div class="live-stat-value">{reserve_flows}</div>
                <div class="live-stat-note">Supported reserve / release routing observed on-chain</div>
            </div>
            <div class="live-stat stat-purple">
                <div class="live-stat-label">Market routes detected</div>
                <div class="live-stat-value">{market_routes}</div>
                <div class="live-stat-note">CEX / DEX / router / MEV endpoints reached</div>
            </div>
            <div class="live-stat stat-cyan">
                <div class="live-stat-label">Addresses and flows observed</div>
                <div class="live-stat-value">{reachable:,}</div>
                <div class="live-stat-note">Wallets reached by bridge-cluster traversal</div>
            </div>
        </div>

        <div class="live-flow">
            {''.join(flow_parts)}
        </div>

        <div class="live-legend">
            <div class="live-legend-item legend-blue">
                <div class="live-legend-title">Observed on-chain</div>
                <div class="live-legend-copy">Direct on-chain evidence found and verified during audit.</div>
            </div>
            <div class="live-legend-item legend-purple">
                <div class="live-legend-title">Supported classification</div>
                <div class="live-legend-copy">Strong correlation with known bridge infrastructure patterns.</div>
            </div>
            <div class="live-legend-item legend-orange">
                <div class="live-legend-title">Unresolved final sale</div>
                <div class="live-legend-copy">Final market destination does not equal exact realized sale volume.</div>
            </div>
            <div class="live-legend-item legend-green">
                <div class="live-legend-title">Explorer links enabled</div>
                <div class="live-legend-copy">Click any wallet or contract pill to open directly in Etherscan.</div>
            </div>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
'''

if ".live-bridge-model" not in text:
    if "</style>" not in text:
        raise RuntimeError("Could not find </style> in app.py.")
    text = text.replace("</style>", CSS + "\n</style>")

if "def render_current_bridge_model_live(" not in text:
    marker = "def sidebar():"
    if marker not in text:
        raise RuntimeError("Could not find def sidebar(): in app.py.")
    text = text.replace(marker, FUNCTION + "\n\n" + marker)

text = text.replace("render_current_bridge_model_image()", "render_current_bridge_model_live(bridge, metrics)")
text = text.replace("render_interactive_bridge_model()", "render_current_bridge_model_live(bridge, metrics)")

start = text.find('st.markdown("## Current Bridge Model")')
if start == -1:
    start = text.find('st.markdown("## 🌉 Current Bridge Model")')

if start != -1:
    next_section = text.find('st.markdown("## Route Exposure Summary")', start)
    if next_section != -1:
        replacement = (
            'st.markdown("## 🌉 Current Bridge Model")\n'
            'render_current_bridge_model_live(bridge, metrics)\n'
            'st.caption("Tip: click any address pill inside the model to open that wallet or contract in Etherscan.")\n\n'
        )
        text = text[:start] + replacement + text[next_section:]

APP.write_text(text)

print("Updated app.py with polished live Current Bridge Model.")
print("Backup saved as app.py.bak_live_bridge_model")
