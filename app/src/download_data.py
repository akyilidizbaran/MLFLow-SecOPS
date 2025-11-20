import os
import os.path
import sys
from pathlib import Path
import zipfile

import yaml
from kaggle.api.kaggle_api_extended import KaggleApi


# Bu script, DVC pipeline içindeki "download" aşamasıdır.
# Görevi:
# - params.yaml içinden Kaggle veri seti bilgilerini okumak
# - Kaggle API ile veri setini indirmek
# - İndirilen dosyayı data/raw/kaggle_raw.csv adıyla kaydetmek
#
# Kaggle kimlik doğrulaması iki şekilde çalışabilir:
# - KAGGLE_USERNAME ve KAGGLE_KEY environment değişkenleri
# - Kullanıcının .kaggle/kaggle.json dosyası (bu proje için host'tan konteynere mount edilecek)
#
# Bu script, KaggleApi().authenticate() fonksiyonunun bu mekanizmaları otomatik kullanmasına güvenir.


def load_params(params_path: Path) -> dict:
    """params.yaml dosyasını okuyup tüm parametreleri döndürür."""
    if not params_path.exists():
        print("Hata: 'params.yaml' dosyası bulunamadı. Kaggle ayarlarını önce bu dosyada tanımlamalısınız.")
        sys.exit(1)

    with params_path.open("r", encoding="utf-8") as f:
        params = yaml.safe_load(f) or {}

    return params


def get_kaggle_api() -> KaggleApi:
    """
    Kaggle API nesnesini oluşturur ve kimlik doğrulaması yapmaya çalışır.

    Kaggle API şu kaynakları kullanabilir:
    - KAGGLE_USERNAME ve KAGGLE_KEY environment değişkenleri
    - Kullanıcının ana dizinindeki .kaggle/kaggle.json dosyası

    Kimlik doğrulama başarısız olursa, Türkçe ve açıklayıcı bir hata mesajı basılır ve program sonlandırılır.
    """
    api = KaggleApi()
    try:
        api.authenticate()
        return api
    except Exception as e:  # noqa: BLE001
        print(
            "Hata: Kaggle API kimlik doğrulaması başarısız oldu.\n"
            "Lütfen aşağıdaki iki yöntemden birini doğru şekilde ayarladığınızdan emin olun:\n"
            "  1) KAGGLE_USERNAME ve KAGGLE_KEY environment değişkenlerini tanımlayın\n"
            "  2) Kaggle hesabınızdan aldığınız kaggle.json dosyasını '~/.kaggle/kaggle.json' yoluna koyun\n"
            "     (Bu projede Docker içinde '/root/.kaggle/kaggle.json' yoluna mount edilecektir).\n"
            f"Ayrıntılı hata mesajı: {e}"
        )
        sys.exit(1)


def main() -> None:
    # Parametre dosyasını ve çıktı klasörünü tanımlıyoruz.
    params_path = Path("params.yaml")
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "kaggle_raw.csv"

    # Ayarları yüklüyoruz.
    params = load_params(params_path)
    kaggle_cfg = params.get("kaggle", {})

    dataset_slug = kaggle_cfg.get("dataset")
    file_name = kaggle_cfg.get("file")

    if not dataset_slug or not file_name:
        print(
            "Hata: 'params.yaml' içindeki 'kaggle.dataset' ve 'kaggle.file' alanları doldurulmalıdır.\n"
            "Örneğin:\n"
            "kaggle:\n"
            "  dataset: \"uciml/pima-indians-diabetes-database\"\n"
            "  file: \"diabetes.csv\""
        )
        sys.exit(1)

    print(f"İndirilecek Kaggle veri seti: {dataset_slug}")
    print(f"İndirilecek dosya adı: {file_name}")
    print(f"Hedef çıktı dosyası: {output_path}")

    if output_path.exists():
        print("Bilgi: Mevcut 'data/raw/kaggle_raw.csv' dosyası üzerine yazılacak.")

    # Kaggle API ile kimlik doğrulaması yapıyoruz.
    api = get_kaggle_api()

    # Dosyayı indiriyoruz.
    try:
        print("Kaggle veri seti indiriliyor...")
        api.dataset_download_file(
            dataset=dataset_slug,
            file_name=file_name,
            path=str(output_dir),
            force=True,
        )
    except Exception as e:  # noqa: BLE001
        print(f"Hata: Kaggle veri seti indirilirken bir sorun oluştu: {e}")
        sys.exit(1)

    # Kaggle genellikle iki şekilde dosya bırakır:
    # - Sıkıştırılmamış: data/raw/<file_name>
    # - Sıkıştırılmış: data/raw/<file_name>.zip
    plain_path = output_dir / file_name
    zip_path = output_dir / f"{file_name}.zip"

    try:
        if zip_path.exists():
            print(f"Bilgi: Dosya zip formatında indirildi: {zip_path}")
            # Zip dosyasını açıp içindeki asıl CSV dosyasını kaggle_raw.csv olarak kaydediyoruz.
            with zipfile.ZipFile(zip_path, "r") as zf:
                members = zf.namelist()
                if not members:
                    print("Hata: Zip dosyası boş görünüyor, içinde çıkarılacak dosya yok.")
                    sys.exit(1)

                # Çoğu zaman zip içinde tek bir CSV olur, ilkini alıyoruz.
                inner_name = members[0]
                print(f"Zip içinden çıkarılan dosya: {inner_name}")
                zf.extract(inner_name, path=str(output_dir))

                extracted_path = output_dir / inner_name

            # Çıkarılan dosyayı hedef isimle değiştiriyoruz.
            if extracted_path.exists():
                os.replace(extracted_path, output_path)
                print(f"Veri seti zip'ten açıldı ve '{output_path}' olarak kaydedildi.")
            else:
                print("Hata: Zip içinden çıkarılan dosya bulunamadı, lütfen Kaggle veri setini kontrol edin.")
                sys.exit(1)

            # İsteğe bağlı: zip dosyasını temizleyebiliriz.
            zip_path.unlink(missing_ok=True)

        elif plain_path.exists():
            # Sıkıştırılmamış dosya doğrudan inmişse, adını kaggle_raw.csv yapıyoruz.
            os.replace(plain_path, output_path)
            print(f"Veri seti doğrudan indirildi ve '{output_path}' olarak kaydedildi.")
        else:
            print(
                "Hata: İndirme işleminden sonra beklenen dosyalar bulunamadı.\n"
                f"Beklenen yollar: '{plain_path}' veya '{zip_path}'"
            )
            sys.exit(1)

    except Exception as e:  # noqa: BLE001
        print(f"Hata: İndirilen dosyanın işlenmesi sırasında sorun oluştu: {e}")
        sys.exit(1)

    print("Kaggle veri indirme işlemi başarıyla tamamlandı.")


if __name__ == "__main__":
    main()

