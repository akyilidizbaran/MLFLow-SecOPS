import pandas as pd
from pathlib import Path
from sklearn.datasets import make_classification

# Bu script, DVC pipeline içindeki "prepare" aşamasıdır.
# Gerçek veri seti indirmek yerine, eğitim amaçlı sentetik bir veri seti üretiyoruz.
# Böylece internet bağlantısına veya dış sistemlere ihtiyaç duymadan örnek çalıştırabiliriz.


def main() -> None:
    # Çıktı dosyasının yolu (konteyner içindeki /app altında)
    data_path = Path("data/raw/data.csv")

    # Klasör yoksa oluşturuyoruz.
    data_path.parent.mkdir(parents=True, exist_ok=True)

    # Sentetik sınıflandırma veri seti üretiyoruz.
    # 1000 örnek, 20 özellik, ikili sınıflandırma.
    X, y = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=10,
        n_redundant=5,
        n_classes=2,
        random_state=42,
    )

    # Özellikleri ve hedef değişkeni bir pandas DataFrame'e koyuyoruz.
    feature_columns = [f"feature_{i}" for i in range(X.shape[1])]
    df = pd.DataFrame(X, columns=feature_columns)
    df["target"] = y

    # CSV dosyasına yazıyoruz.
    df.to_csv(data_path, index=False)

    print("Sentetik veri seti oluşturuldu ve 'data/raw/data.csv' dosyasına kaydedildi.")


if __name__ == "__main__":
    main()

