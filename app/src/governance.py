"""
MLOps Governance Report (Credo AI Simulation).

- Aggregates key artifacts (metrics, SBOM, fairness, security) and emits a simple HTML report.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
GOV_DIR = REPORTS_DIR / "governance"

METRICS_PATH = BASE_DIR / "metrics.json"
SBOM_PATH = REPORTS_DIR / "sbom" / "bom.json"
FAIRNESS_PATH = REPORTS_DIR / "fairness" / "fairness_report.txt"
GISKARD_PATH = REPORTS_DIR / "quality" / "giskard_report.html"
GARAK_PATH = REPORTS_DIR / "security" / "garak_report.report.html"
OUTPUT_HTML = GOV_DIR / "credo_report.html"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def render_html(metrics: Dict[str, Any], statuses: Dict[str, str], decision: str) -> str:
    acc = metrics.get("accuracy", "N/A")
    f1 = metrics.get("f1", metrics.get("f1_score", "N/A"))

    status_rows = ""
    for k, v in statuses.items():
        status_rows += f"<tr><td>{k}</td><td>{v}</td></tr>"

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MLOps Governance Report (Credo AI Simulation)</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background: #f4f6f8; }}
        .section {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>MLOps Governance Report (Credo AI Simulation)</h1>

    <div class="section">
        <h2>Model Performance</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Accuracy</td><td>{acc}</td></tr>
            <tr><td>F1</td><td>{f1}</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>Compliance Checklist</h2>
        <table>
            <tr><th>Artifact</th><th>Status</th></tr>
            {status_rows}
        </table>
    </div>

    <div class="section">
        <h2>Governance Decision</h2>
        <p>{decision}</p>
    </div>
</body>
</html>
""".strip()


def main() -> None:
    GOV_DIR.mkdir(parents=True, exist_ok=True)

    metrics = load_json(METRICS_PATH)
    accuracy = metrics.get("accuracy")
    sbom_exists = SBOM_PATH.exists()

    statuses = {
        "SBOM": "✅ Found" if sbom_exists else "❌ Missing",
        "Fairness": "✅ Found" if FAIRNESS_PATH.exists() else "❌ Missing",
        "Giskard Quality": "✅ Found" if GISKARD_PATH.exists() else "❌ Missing",
        "Security (Garak)": "✅ Found" if GARAK_PATH.exists() else "❌ Missing",
    }

    decision = "NEEDS REVIEW"
    try:
        if sbom_exists and accuracy is not None and float(accuracy) > 0.6:
            decision = "APPROVED"
    except Exception:
        decision = "NEEDS REVIEW"

    html = render_html(metrics, statuses, decision)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Governance report written to {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
