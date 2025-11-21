pipeline {
    agent any

    environment {
        // MLflow server zaten docker'da 5000 portunda çalışıyor
        MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"
    }

    stages {
        stage('Kodları Getir') {
            steps {
                checkout scm
            }
        }

        stage('Python ve Bağımlılıkları Kur') {
            steps {
                bat '''
                echo [PY] Sanal ortam oluşturuluyor...
                python -m venv .venv

                echo [PY] Sanal ortam aktif ediliyor...
                call .venv\\Scripts\\activate

                echo [PY] Bağımlılıklar kuruluyor...
                pip install --upgrade pip
                pip install -r app\\requirements.txt
                '''
            }
        }

        stage('DVC ile Kaggle İndir + Eğitim') {
            steps {
                // Kaggle credential'ları Secret Text olarak eklediğini varsayıyorum:
                // ID'ler: kaggle-username-id, kaggle-key-id
                withCredentials([
                    string(credentialsId: 'kaggle-username-id', variable: 'KAGGLE_USERNAME'),
                    string(credentialsId: 'kaggle-key-id', variable: 'KAGGLE_KEY')
                ]) {
                    bat '''
                    echo [DVC] Sanal ortam aktif ediliyor...
                    call .venv\\Scripts\\activate

                    echo [DVC] Kaggle env değişkenleri ayarlanıyor...
                    set KAGGLE_USERNAME=%KAGGLE_USERNAME%
                    set KAGGLE_KEY=%KAGGLE_KEY%

                    echo [DVC] Pipeline (download + train) çalıştırılıyor...
                    dvc repro

                    echo [DVC] Metrikler gösteriliyor...
                    dvc metrics show
                    '''
                }
            }
        }

        stage('MLSecOps Denetimi (Şablon)') {
            steps {
                bat '''
                echo [MLSecOps] Buraya OWASP Top 10 ve MITRE ATLAS kontrollerini ekleyeceksin.
                echo [MLSecOps] Örn: model artifact taraması, dependency taraması, config hardening vb.
                '''
            }
        }

        stage('DVC Snapshot ve Remote Push') {
            steps {
                bat '''
                echo [DVC] Sanal ortam aktif ediliyor...
                call .venv\\Scripts\\activate

                echo [DVC] DVC durumu:
                dvc status || echo "DVC status hata verdi (önemliyse loga bak)."

                echo [DVC] DVC push ile artefaktlar remote'a gönderiliyor...
                dvc push
                '''
            }
        }

        stage('Artefaktları Arşivle') {
            steps {
                archiveArtifacts artifacts: 'metrics.json, dvc.lock, models/model.pkl', onlyIfSuccessful: true
            }
        }

        stage('Git Push (CI Sonrası)') {
            steps {
                // Git için Jenkins credentials: git-credentials-id (Username with password / PAT)
                withCredentials([
                    usernamePassword(credentialsId: 'git-credentials-id', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')
                ]) {
                    bat '''
                    echo [GIT] Kullanıcı bilgisi ayarlanıyor...
                    git config user.email "ci-bot@example.com"
                    git config user.name "jenkins-bot"

                    echo [GIT] Değişiklik var mı?
                    git status

                    echo [GIT] dvc.lock ve .dvc/config commit'e ekleniyor (varsa)...
                    REM -f parametresi (force) gitignore kuralini ezer ve dosyalari zorla ekler
                    git add -f dvc.lock .dvc/config reports/

                    echo [GIT] Commit denemesi...
                    git commit -m "CI: Update DVC lockfile" || echo "Commitlenecek değişiklik yok."

                    echo [GIT] Remote URL PAT ile güncelleniyor...
                    git remote set-url origin https://%GIT_USERNAME%:%GIT_PASSWORD%@github.com/akyilidizbaran/MLFLow-SecOPS.git

                    echo [GIT] main branch push ediliyor...
                    git push origin HEAD:main || echo "Push başarısız oldu, loga bak."
                    '''
                }
            }
        }
    }

    post {
        always {
            bat '''
            echo [POST] Son durum raporu alınıyor...

            if exist .venv\\Scripts\\activate (
                call .venv\\Scripts\\activate
                echo [POST] dvc status:
                dvc status || echo "dvc status post aşamasında hata verdi."
            ) else (
                echo [POST] .venv bulunamadı, dvc status atlanıyor.
            )

            echo [POST] Son commit:
            git log -1 --oneline || echo "Git log okunamadı."
            '''
        }
    }
}
