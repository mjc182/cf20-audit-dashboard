CF20 Bridge Infrastructure Website Showcase Pack

Put these files into your repo:

1. build_bridge_infrastructure_summary.py
   Location: repo root

2. pages/9_Bridge_Infrastructure.py
   Location: pages/9_Bridge_Infrastructure.py

3. bridge_home_showcase_component.py
   Optional component you can copy into app.py if you want the homepage itself to render the bridge showcase.

4. patch_app_sidebar.py
   Optional helper to add the new page link to app.py.

Required inputs:
- bridge_cluster_terminal_endpoints.csv
- bridge_cluster_unclassified_wallets.csv
- bridge_cluster_summary.json
- known_wallet_labels.csv
- bridge_market_route_summary.json if available

Run:
python3 build_bridge_infrastructure_summary.py

Then add this to app.py page_links:
("pages/9_Bridge_Infrastructure.py", "Bridge Infrastructure"),

Optional:
python3 patch_app_sidebar.py

Recommended rerun sequence:
python3 trace_bridge_cluster.py --max-hops 5 --min-amount 1000 --max-edges-per-node 75
python3 rank_unclassified_wallets.py
python3 build_bridge_infrastructure_summary.py

Upload these generated outputs to GitHub:
- bridge_infrastructure_summary.json
- bridge_cluster_terminal_endpoints.csv
- bridge_cluster_unclassified_wallets.csv
- bridge_cluster_summary.json
- known_wallet_labels.csv
