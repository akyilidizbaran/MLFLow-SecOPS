# mlops-mlflow-dvc-jenkins

Bu proje, Docker, MLflow, DVC, Jenkins ve Git kullanarak basit ama gerçekçi bir MLOps pipeline örneği sunar. Amaç, bir üniversite öğrencisinin uçtan uca temel bir MLOps mimarisini deneyerek öğrenmesini sağlamaktır.

## Mimari Özeti

Bu projede üç ana bileşen vardır:

- **MLflow Tracking Server**
  - `mlflow` servisi ile Docker içinde çalışır.
  - SQLite backend ve yerel klasörde artefakt saklama kullanır.
  - Host makineden `http://localhost:5000` adresi üzerinden erişilir.

- **Eğitim Uygulaması (app)**
  - Basit bir Python/Scikit-learn uygulaması.
  - Kaggle API ile bir veri seti indirir (DVC `download` aşaması).
  - DVC ile iki aşamalı pipeline tanımlıdır:
    - `download`: Kaggle'dan veri indirme
    - `train`: model eğitimi ve metrik hesaplama
  - Metrikleri ve modeli hem dosya olarak hem de MLflow'a loglar.

- **Jenkins CI/CD**
  - `jenkins` servisi ile Docker içinde çalışır.
  - Kod değiştiğinde pipeline çalıştırarak:
    - Bağımlılıkları kurar.
    - `dvc repro` ile (Kaggle indirme + eğitim) pipeline'ını çalıştırır.
    - Metrikleri gösterir ve artefaktları arşivler.
    - DVC remote'a artefaktları push eder.
    - Git deposuna otomatik commit + push yapar.
  - Aynı Docker ağı üzerinden `http://mlflow:5000` adresindeki MLflow servisine erişebilir.

## Gereksinimler

- Docker / Docker Desktop
- Git
- (İsteğe bağlı) DVC'nin lokal kurulu olması (`pip install dvc[all]`)
- Kaggle hesabı ve Kaggle API anahtarı

## İlk Kurulum

1. Yeni bir klasör oluşturun ve proje adını verin:

```bash
mkdir mlops-mlflow-dvc-jenkins
cd mlops-mlflow-dvc-jenkins
```

2. Bu repodaki dosyaları buraya kopyalayın.

3. Git deposu oluşturun:

```bash
git init
git add .
git commit -m "İlk MLOps iskeleti"
```

4. DVC'yi başlatın:

```bash
dvc init
git add .dvc .dvcignore
git commit -m "DVC init"
```

> Not: DVC remote (örneğin S3, Azure, GDrive veya lokal bir klasör) eklemek için bir sonraki bölümdeki adımlara bakın.

## Kaggle Entegrasyonu

Bu proje, Kaggle API üzerinden veri indirmek için tasarlanmıştır. İndirme işlemi:

- `app/src/download_data.py` scripti
- DVC `download` stage'i
- Jenkins pipeline içindeki `DVC ile Kaggle İndir + Eğitim` aşaması

tarafından kullanılır.

### Kaggle API Anahtarını Ayarlama

Kaggle API'yi kullanmak için bir Kaggle hesabınız olmalı ve API anahtarı oluşturmalısınız.

1. Kaggle sitesine gidin (https://www.kaggle.com/) ve giriş yapın.
2. Sağ üstteki profil menüsünden: **Account** sayfasına gidin.
3. Aşağıda **API** bölümünde "Create New API Token" butonuna tıklayın.
4. `kaggle.json` dosyasını bilgisayarınıza indirecektir.

Yerel makinenizde:

```bash
export KAGGLE_USERNAME="kullanici_adiniz"
export KAGGLE_KEY="kaggle_api_anahtariniz"
```

veya `~/.kaggle/kaggle.json` dosyasını uygun şekilde kaydedebilirsiniz.

Jenkins içinde:

- Jenkins web arayüzüne gidin.
- **Manage Jenkins** → **Manage Credentials** → **(Global)** → **Add Credentials**.
- İki adet "Secret text" credential tanımlayın:
  - `kaggle-username-id` → içinde Kaggle kullanıcı adınız
  - `kaggle-key-id` → içinde Kaggle API anahtarınız
- Jenkinsfile içindeki `withCredentials` bloğu bu ID'leri kullanır.

### params.yaml İçinde Kaggle Dataset Tanımı

`params.yaml` dosyasında Kaggle veri setini ve dosya adını şu şekilde tanımlarsınız:

```yaml
kaggle:
  dataset: "owner/dataset-slug"   # Örnek: "zynicide/wine-reviews"
  file: "file.csv"                # Örnek: "winemag-data-130k-v2.csv"

train:
  test_size: 0.2
  random_state: 42
  n_estimators: 100
  max_depth: 5
  target_column: "target"
```

- `kaggle.dataset` ve `kaggle.file` alanlarının Kaggle üzerindeki veri seti ile birebir uyumlu olması gerekir.
  - Örneğin Kaggle sayfasında: `https://www.kaggle.com/datasets/zynicide/wine-reviews` ise
    - `dataset: "zynicide/wine-reviews"`
- `train.target_column` alanı, veri setinizdeki hedef kolonun ismi ile aynı olmalıdır.
  - Örneğin bir sınıflandırma problemi için `quality`, `label`, `target` gibi.

`download` stage, Kaggle'dan veriyi indirip `data/raw/kaggle_raw.csv` dosyasına kaydeder. `train` stage ise bu dosyayı kullanarak modeli eğitir.

## Docker ile Çalıştırma

Önce imajları build edin:

```bash
docker compose build
```

### MLflow Sunucusunu Başlatma

```bash
docker compose up -d mlflow
```

- MLflow arayüzü: `http://localhost:5000`

### Eğitim Uygulamasını Çalıştırma (Kaggle + DVC)

Kaggle environment değişkenlerini terminalinizde ayarladıktan sonra:

```bash
export KAGGLE_USERNAME="kullanici_adiniz"
export KAGGLE_KEY="kaggle_api_anahtariniz"

docker compose run --rm app dvc repro
```

veya daha basit olarak sadece eğitim scriptini çalıştırmak isterseniz:

```bash
docker compose run --rm app python src/train.py
```

> Not: Tam DVC pipeline için önerilen yol `dvc repro` komutunu kullanmaktır; böylece `download` ve `train` aşamaları sırayla çalışır.

Bu adımlar:

- `download_data.py` ile Kaggle veri setini indirir (DVC `download` aşaması).
- `train.py` ile modeli eğitir ve:
  - `models/model.pkl`
  - `metrics.json`
  - MLflow run (MLflow arayüzünde görülebilir)
  üretir.

## DVC Remote ve Otomatik Push

Veri ve model artefaktlarını Git yerine DVC remote üzerinde saklamak daha doğrudur. Örneğin:

- Lokal klasör
- S3 bucket
- Azure Blob Storage
- Google Drive

Örnek DVC remote tanımlama:

```bash
dvc remote add -d origin /path/to/dvc-storage
dvc remote default origin
git add .dvc/config
git commit -m "DVC remote eklendi"
```

Bu ayarları yaptıktan sonra:

```bash
dvc push
```

komutu veri/model artefaktlarını remote'a yükler.

Jenkins pipeline içindeki **"DVC Snapshot ve Remote Push"** stage'i, aynı işlemi CI tarafında yapar:

- `dvc status` ile değişiklikleri kontrol eder.
- `dvc push` ile güncel artefaktları remote'a gönderir.

> Önemli: DVC remote URL'sini ve olası erişim credential'larını kendi ortamınıza göre ayarlamalısınız.

## Otomatik Git Push (CI)

Jenkins pipeline, başarılı bir çalıştırmadan sonra otomatik olarak:

- DVC dosyalarını ve diğer değişen dosyaları `git add .` ile ekler.
- `git commit -m "CI: update DVC snapshot [skip ci]"` ile commit atar.
- `git push origin main` benzeri bir komutla uzak repoya push eder.

Bunun için:

1. Git remote'u ayarlayın:

```bash
git remote add origin <SENIN_GIT_REMOTE_URLIN>
git branch -M main
git push -u origin main
```

2. Jenkins'te Git credential tanımlayın:

- **Manage Jenkins** → **Manage Credentials** → (Global) → **Add Credentials**
- Tür olarak:
  - HTTPS kullanıyorsanız: "Username with password" (kullanıcı adı + token/şifre)
  - SSH kullanıyorsanız: "SSH Username with private key"
- Örneğin `git-credentials-id` adında bir credential oluşturun.

3. Jenkinsfile içindeki `withCredentials` bloğu bu ID'yi kullanır:

- Kullanıcı adı ve token/şifre, `GIT_USERNAME` ve `GIT_PASSWORD` değişkenlerine atanır.
- `git push` komutu bu bilgileri kullanarak uzak repoya push eder.

> Uyarı: Gerçek projelerde erişim yetkilerini dikkatli yönetin, sadece gerekli izinlere sahip token/anahtarları kullanın.

## Jenkins Kurulumu ve CI/CD

1. Jenkins servisini Docker ile başlatın:

```bash
docker compose up -d jenkins
```

2. Tarayıcıdan Jenkins arayüzüne gidin:

- Adres: `http://localhost:8080`

3. Gerekirse ilk kurulum ve kullanıcı oluşturma adımlarını tamamlayın.

4. Yeni bir pipeline job oluşturun:

- **New Item** > bir ad verin (örn. `mlops-demo-pipeline`) > **Pipeline** seçin.
- **Pipeline** sekmesinde:
  - **Definition**: "Pipeline script from SCM"
  - **SCM**: Git
  - Repository URL: Bu repo'nun Git adresi
  - Script Path: `Jenkinsfile`

5. Job'ı kaydedip çalıştırın.

Pipeline aşamaları:

- **Kodları Getir**
  - Git repo'dan kodu çeker.
- **Python ve Bağımlılıkları Kur**
  - `app/requirements.txt` içindeki Python paketlerini kurar.
- **DVC ile Kaggle İndir + Eğitim**
  - `dvc repro` ile `download` ve `train` stage'lerini çalıştırır.
  - `dvc metrics show` ile metrikleri konsola yazar.
- **MLSecOps Denetimi (Şablon)**
  - İleride eklenecek güvenlik kontrolleri için yer tutucu.
- **DVC Snapshot ve Remote Push**
  - `dvc status` ile kontrol, `dvc push` ile DVC remote'a artefakt gönderimi.
- **Artefaktları Arşivle**
  - `metrics.json`, `dvc.lock` ve `models/model.pkl` dosyalarını build artefaktı olarak saklar.
- **Git Push (CI Sonrası)**
  - Değişiklikleri commit ve push eder.

## MLflow ile Deney Takibi

MLflow arayüzü `http://localhost:5000` adresinden açılır. Buradan:

- `demo-mlops-pipeline` deneyini,
- Her çalıştırma (run) için:
  - Hiperparametreler
  - Metrikler (accuracy, f1_score)
  - Model artefaktı

görüntülenebilir.

## Özet

Bu proje, gerçek bir üretim ortamının basitleştirilmiş bir versiyonudur:

- **Docker Compose** ile MLflow, eğitim uygulaması ve Jenkins aynı ağda yönetilir.
- **MLflow** ile deney ve model versiyonları takip edilir.
- **DVC** ile veri ve eğitim pipeline'ı yeniden üretilebilir hale getirilir.
- **Kaggle API** ile dış veri kaynaklarından otomatik veri indirme sağlanır.
- **Jenkins** ile CI/CD süreci (otomatik eğitim, DVC push ve Git push) kurulur.
- **MLSecOps** için bir denetim aşaması şablon olarak eklenmiştir (daha sonra genişletilebilir).

Bu iskeleti, kendi Kaggle veri setiniz, hiperparametreleriniz ve güvenlik kontrollerinizle genişleterek daha ileri seviye MLOps senaryoları deneyebilirsiniz.

