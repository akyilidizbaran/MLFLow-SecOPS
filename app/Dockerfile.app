# Bu imaj, eğitim uygulaması için Python 3.11 tabanını sağlar.
FROM python:3.11-slim

# Gerekli sistem bağımlılıklarını kuruyoruz (derleme araçları vb.).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
 && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını bu dosyadan kuracağız.
WORKDIR /app
COPY requirements.txt /app/requirements.txt

# Python paketlerini yüklüyoruz.
RUN pip install --no-cache-dir -r /app/requirements.txt

# Uygulama kaynak kodunu konteynere kopyalıyoruz.
# docker-compose ile ayrıca bind mount yapacağımız için bu sadece temel imaj içindir.
COPY src /app/src

# DVC ve eğitim scripti params.yaml ve dvc.yaml dosyalarını kullanacak.
# Bunlar docker-compose ile volume olarak bağlanacağı için burada kopyalamıyoruz.

# Python çıktılarının buffering yapmaması için bu değişkeni ayarlıyoruz.
ENV PYTHONUNBUFFERED=1

# Çalışma dizinini ayarlıyoruz.
WORKDIR /app

# Varsayılan komut eğitim scriptini çalıştırmak.
CMD ["python", "src/train.py"]

# Not:
# - Bu konteyner veri hazırlama ve model eğitimi için kullanılır.
# - DVC pipeline aşamaları (prepare, train) bu ortamda çalıştırılabilir.
# - MLflow ile bağlantı için MLFLOW_TRACKING_URI ortam değişkeni kullanılır.

