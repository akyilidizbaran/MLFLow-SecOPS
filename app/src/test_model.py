import json
from pathlib import Path

import joblib
import pandas as pd
from giskard import Dataset, Model, scan


def load_model(model_path: Path):
    if not model_path.exists():
        raise FileNotFoundError(f"Model dosyası bulunamadı: {model_path}")
    return joblib.load(model_path)


def load_data(data_path: Path, target_column: str = "Outcome", sample_size: int = 200):
    if not data_path.exists():
        raise FileNotFoundError(f"Veri dosyası bulunamadı: {data_path}")
    df = pd.read_csv(data_path)
    if target_column not in df.columns:
        raise ValueError(f"Hedef kolon '{target_column}' veri setinde yok.")
    # Hızlı tarama için küçük bir örneklem alıyoruz.
    df_sample = df.sample(n=min(sample_size, len(df)), random_state=42)
    return df_sample


def main():
    model_path = Path("models/model.pkl")
    data_path = Path("data/raw/kaggle_raw.csv")
    reports_dir = Path("reports/quality")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "giskard_report.html"

    print("Model ve veri yükleniyor...")
    model = load_model(model_path)
    df_sample = load_data(data_path, target_column="Outcome")

    feature_cols = [c for c in df_sample.columns if c != "Outcome"]
    X = df_sample[feature_cols]
    y = df_sample["Outcome"]

    print("Giskard Model ve Dataset sarmalayıcıları hazırlanıyor...")

    def predict_fn(input_df):
        # Giskard, DataFrame alıp tahmin dönen bir fonksiyon bekler.
        return model.predict_proba(input_df).tolist() if hasattr(model, "predict_proba") else model.predict(input_df).tolist()

    wrapped_model = Model(
        model=predict_fn,
        model_type="classification",
        name="diabetes-rf",
        feature_names=feature_cols,
        classification_labels=sorted(y.unique().tolist()),
    )

    wrapped_dataset = Dataset(
        df=df_sample,
        target="Outcome",
        feature_names=feature_cols,
        column_types=None,
    )

    print("Giskard taraması başlatılıyor...")
    scan_result = scan(wrapped_model, wrapped_dataset)

    print(f"Rapor kaydediliyor: {report_path}")
    scan_result.to_html(str(report_path))

    # Basit bir özet de JSON olarak saklanabilir (isteğe bağlı).
    summary_path = reports_dir / "giskard_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump({"status": "completed", "report": str(report_path)}, f, indent=2)
    print("Giskard taraması tamamlandı.")


if __name__ == "__main__":
    main()

