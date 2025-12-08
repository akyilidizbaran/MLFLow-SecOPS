"""
Lightweight governance report generator for Credo AI workflow.

- Loads metrics.json for performance metrics.
- Loads SBOM (if available) from reports/sbom/bom.json.
- Writes an HTML governance report to reports/governance/credo_report.html.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
GOV_DIR = REPORTS_DIR / "governance"
SBOM_PATH = REPORTS_DIR / "sbom" / "bom.json"
METRICS_PATH = BASE_DIR / "metrics.json"
OUTPUT_HTML = GOV_DIR / "credo_report.html"
FAIRNESS_REPORT = REPORTS_DIR / "quality" / "giskard_report.html"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def render_html(metrics: Dict[str, Any], sbom_exists: bool) -> str:
    metrics_rows = ""
    if metrics:
        for k, v in metrics.items():
            metrics_rows += f"<tr><td>{k}</td><td>{v}</td></tr>"
    else:
        metrics_rows = "<tr><td colspan='2'>Metrics not found</td></tr>"

    sbom_status = "SBOM found" if sbom_exists else "SBOM not found"
    fairness_link = FAIRNESS_REPORT.as_posix()

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Credo AI Governance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background: #f4f6f8; }}
        .section {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>Credo AI Governance Report</h1>

    <div class="section">
        <h2>Model Performance Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            {metrics_rows}
        </table>
    </div>

    <div class="section">
        <h2>Supply Chain Status (SBOM)</h2>
        <p>{sbom_status}</p>
    </div>

    <div class="section">
        <h2>Fairness Check Status</h2>
        <p>See fairness report (if generated): <a href="{fairness_link}">{fairness_link}</a></p>
    </div>
</body>
</html>
""".strip()


def main():
    GOV_DIR.mkdir(parents=True, exist_ok=True)

    metrics = load_json(METRICS_PATH)
    sbom_exists = SBOM_PATH.exists()

    html = render_html(metrics, sbom_exists)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Governance report written to {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
