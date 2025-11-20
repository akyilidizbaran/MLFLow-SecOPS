import json
import os
from pathlib import Path

import joblib
import mlflow
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

# Bu script, DVC pipeline içindeki "train" aşamasıdır.
# Görevi:
# - params.yaml dosyasından hiperparametreleri ve hedef kolonu okumak
# - Kaggle'dan indirilmiş veri setini yüklemek
# - Basit bir sınıflandırma modeli eğitmek
# - Metrikleri hem metrics.json dosyasına hem de MLflow'a loglamak
# - Eğitilen modeli dosyaya kaydetmek ve MLflow'a artefakt olarak yüklemek


def load_params(params_path: Path) -> dict:
    """params.yaml dosyasını okuyup train bölümünü ve diğer ayarları döndürür."""
    with params_path.open("r", encoding="utf-8") as f:
        params = yaml.safe_load(f)
    return params or {}


def main() -> None:
    # Çalışma dizini /app olarak ayarlandığı için yolları göreli kullanıyoruz.
    params_path = Path("params.yaml")
    data_path = Path("data/raw/kaggle_raw.csv")
    model_path = Path("models/model.pkl")
    metrics_path = Path("metrics.json")

    if not params_path.exists():
        raise FileNotFoundError("Hata: 'params.yaml' dosyası bulunamadı.")

    # Hiperparametreleri ve diğer ayarları yüklüyoruz.
    params = load_params(params_path)
    train_params = params.get("train", {})

    test_size = float(train_params.get("test_size", 0.2))
    random_state = int(train_params.get("random_state", 42))
    n_estimators = int(train_params.get("n_estimators", 100))
    max_depth = train_params.get("max_depth", 5)
    max_depth = int(max_depth) if max_depth is not None else None
    target_column = train_params.get("target_column", "target")

    print("Hiperparametreler yüklendi:", train_params)

    # Veri setini yüklüyoruz.
    if not data_path.exists():
        raise FileNotFoundError(
            "Veri dosyası bulunamadı: 'data/raw/kaggle_raw.csv'. "
            "Önce 'download_data.py' çalıştırılmalıdır (DVC download stage)."
        )

    df = pd.read_csv(data_path)
    num_rows, num_cols = df.shape
    print(f"Toplam {num_rows} satır ve {num_cols} kolon içeren veri seti yüklendi.")

    if target_column not in df.columns:
        raise ValueError(
            f"Hata: hedef kolon '{target_column}' veri setinde bulunamadı. "
            "Lütfen params.yaml içindeki 'train.target_column' değerini veri setinize göre güncelleyin."
        )

    print(f"Kullanılan hedef kolon: '{target_column}'")

    X = df.drop(columns=[target_column])
    y = df[target_column]

    # Eğitim ve test kümelerine bölüyoruz.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    # Basit bir RandomForest sınıflandırıcı eğitiyoruz.
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
    )

    print("Model eğitimi başlıyor...")
    model.fit(X_train, y_train)
    print("Model eğitimi tamamlandı.")

    # Test kümesi üzerinde değerlendirme yapıyoruz.
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    metrics = {
        "accuracy": accuracy,
        "f1_score": f1,
    }

    print(f"Test accuracy: {accuracy:.4f}")
    print(f"Test F1-score: {f1:.4f}")

    # Metrikleri JSON dosyasına yazıyoruz.
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)

    print("Metrikler 'metrics.json' dosyasına kaydedildi.")

    # Modeli kaydetmek için klasörü oluşturuyoruz.
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print("Eğitilen model 'models/model.pkl' dosyasına kaydedildi.")

    # MLflow ayarları
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow.set_tracking_uri(tracking_uri)

    # Basit bir deney adı belirliyoruz.
    experiment_name = "demo-mlops-pipeline"
    mlflow.set_experiment(experiment_name)

    # MLflow run başlatıyoruz.
    print(f"MLflow tracking URI: {tracking_uri}")
    print(f"MLflow deney adı: {experiment_name}")

    with mlflow.start_run():
        # Hiperparametreleri logluyoruz.
        mlflow.log_params(train_params)

        # Metrikleri logluyoruz.
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)

        # Model dosyasını artefakt olarak yüklüyoruz.
        mlflow.log_artifact(str(model_path), artifact_path="model")

        print("MLflow run başarıyla loglandı.")


if __name__ == "__main__":
    main()

