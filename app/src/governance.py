import json
import os
from pathlib import Path


def main():
    # Yollar
    metrics_path = Path("metrics.json")
    sbom_path = Path("reports/sbom/bom.json")
    fairness_path = Path("reports/fairness/fairness_report.txt")
    giskard_path = Path("reports/quality/giskard_report.html")
    garak_path = Path("reports/security/garak_report.report.html")

    output_path = Path("reports/governance/credo_report.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Performans Kontrolü
    metrics = {}
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)

    acc = metrics.get("accuracy", 0)
    f1 = metrics.get("f1_score", 0)

    # 2. Uyumluluk Kontrolleri
    has_sbom = "✅ MEVCUT" if sbom_path.exists() else "❌ EKSIK"
    has_fairness = "✅ MEVCUT" if fairness_path.exists() else "❌ EKSIK"
    has_giskard = "✅ MEVCUT" if giskard_path.exists() else "❌ EKSIK"
    has_garak = "✅ MEVCUT" if garak_path.exists() else "❌ EKSIK"

    # 3. Karar Mantığı
    decision = "ONAYLANDI" if (acc > 0.6 and has_sbom == "✅ MEVCUT") else "INCELENMELI"
    color = "green" if decision == "ONAYLANDI" else "red"

    # 4. HTML Raporu
    html_content = f"""
    <html>
    <head><title>MLSecOps Yonetisim Raporu</title></head>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1>MLSecOps Yonetisim Raporu (Simulasyon)</h1>
        <hr>
        <h2 style="color: {color};">KARAR: {decision}</h2>

        <h3>1. Model Performansi</h3>
        <ul>
            <li>Accuracy: {acc:.4f}</li>
            <li>F1 Score: {f1:.4f}</li>
        </ul>

        <h3>2. Uyumluluk Kontrol Listesi</h3>
        <table border="1" cellpadding="10" style="border-collapse: collapse;">
            <tr><th>Kontrol</th><th>Durum</th></tr>
            <tr><td>Tedarik Zinciri (SBOM)</td><td>{has_sbom}</td></tr>
            <tr><td>Adillik Testi (Fairness)</td><td>{has_fairness}</td></tr>
            <tr><td>Kalite Testi (Giskard)</td><td>{has_giskard}</td></tr>
            <tr><td>Guvenlik Taramasi (Garak)</td><td>{has_garak}</td></tr>
        </table>

        <p><small>Rapor Olusturma Tarihi: Otomatik</small></p>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Yonetisim raporu olusturuldu: {output_path}")


if __name__ == "__main__":
    main()
