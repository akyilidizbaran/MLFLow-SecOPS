pipeline {
    agent any

    environment {
        // MLflow server docker ortamında 5000 portunda çalışıyor
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

        stage('MLSecOps Denetimi (Garak & LLM)') {
            steps {
                bat '''
                echo Starting Security Scan...
                call .venv\\Scripts\\activate
                if not exist reports mkdir reports

                echo [GARAK] Yerel GPT-2 modeli ile tarama başlıyor...
                python -m garak --model_type huggingface --model_name gpt2 --probes encoding --report_prefix reports/garak_report || ver > nul

                echo [SUMMARY] Tarih/Saat ve DVC durum raporu hazırlanıyor...
                echo Tarih/Saat: %DATE% %TIME% > reports/pipeline_summary.txt
                echo DVC Status: >> reports/pipeline_summary.txt
                dvc status >> reports/pipeline_summary.txt 2>&1

                echo [DEBUG] reports klasörü içeriği:
                dir reports

                echo Scan complete.
                '''
            }
        }

        stage('DVC Snapshot ve Remote Push') {
            steps {
                bat '''
                echo [DVC] Sanal ortam aktif ediliyor...
                call .venv\\Scripts\\activate

                echo [DVC] DVC durumu:
                dvc status || echo "DVC status hata verdi."

                echo [DVC] DVC push ile artefaktlar remote'a gönderiliyor...
                dvc push
                '''
            }
        }

        stage('Artefaktları Arşivle') {
            steps {
                archiveArtifacts artifacts: 'models/*.pkl, metrics.json, reports/*.*', fingerprint: true
            }
        }

        stage('Git Push (CI Sonrası)') {
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'git-credentials-id', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')
                ]) {
                    bat '''
                    echo [GIT] Kullanıcı bilgisi ayarlanıyor...
                    git config user.email "ci-bot@example.com"
                    git config user.name "jenkins-bot"

                    echo [GIT] reports klasörü kontrol ediliyor...
                    dir reports

                    echo [GIT] dvc.lock, .dvc/config ve reports klasörü commit'e ekleniyor...
                    git add -f dvc.lock .dvc/config
                    git add -f reports/

                    echo [GIT] Git status:
                    git status

                    echo [GIT] Commit denemesi...
                    git commit -m "CI: Add Security Reports and DVC Lock" || echo "Nothing to commit"

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
