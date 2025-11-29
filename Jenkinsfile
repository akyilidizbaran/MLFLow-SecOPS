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
                echo [PY] Sanal ortam olusturuluyor...
                python -m venv .venv

                echo [PY] Sanal ortam aktif ediliyor...
                call .venv\\Scripts\\activate

                echo [PY] Bagimliliklar kuruluyor...
                pip install --upgrade pip
                pip install -r app\\requirements.txt
                '''
            }
        }

        stage('DVC ile Kaggle Indir + Egitim') {
            steps {
                withCredentials([
                    string(credentialsId: 'kaggle-username-id', variable: 'KAGGLE_USERNAME'),
                    string(credentialsId: 'kaggle-key-id', variable: 'KAGGLE_KEY')
                ]) {
                    bat '''
                    echo [DVC] Sanal ortam aktif ediliyor...
                    call .venv\\Scripts\\activate

                    echo [DVC] Kaggle env degiskenleri ayarlaniyor...
                    set KAGGLE_USERNAME=%KAGGLE_USERNAME%
                    set KAGGLE_KEY=%KAGGLE_KEY%

                    echo [DVC] Pipeline (download + train) calistiriliyor...
                    dvc repro

                    echo [DVC] Metrikler gosteriliyor...
                    dvc metrics show
                    '''
                }
            }
        }

        stage('MLSecOps Denetimi (Garak & LLM)') {
            steps {
                bat '''
                echo Starting Security Scan...

                echo [ENV] Kullanici profili calisma alanina yonlendiriliyor...
                set USERPROFILE=%WORKSPACE%
                set HF_HOME=%WORKSPACE%\\.cache\\huggingface
                set TORCH_HOME=%WORKSPACE%\\.cache\\torch

                call .venv\\Scripts\\activate
                if not exist .local\\share\\garak\\garak_runs\\reports mkdir .local\\share\\garak\\garak_runs\\reports
                if not exist reports mkdir reports

                echo [GARAK] Yerel distilgpt2 modeli ile hizli tarama basliyor...
                python -m garak --model_type huggingface --model_name distilgpt2 --probes encoding.InjectBase64 --generations 10 --report_prefix reports/garak_report || echo "Garak found vulnerabilities..."

                echo [COPY] Garak raporlari workspace altina kopyalaniyor...
                xcopy /s /y %USERPROFILE%\\.local\\share\\garak\\garak_runs\\reports\\*.* reports\\

                echo [SUMMARY] Tarih/Saat ve DVC durum raporu hazirlaniyor...
                echo Tarih/Saat: %DATE% %TIME% > reports/pipeline_summary.txt
                echo DVC Status: >> reports/pipeline_summary.txt
                dvc status >> reports/pipeline_summary.txt 2>&1

                echo [DEBUG] reports klasoru icerigi:
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

                echo [DVC] DVC push ile artefaktlar remote'a gonderiliyor...
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
                    echo [GIT] Kullanici bilgisi ayarlaniyor...
                    git config user.email "ci-bot@example.com"
                    git config user.name "jenkins-bot"

                    echo [GIT] reports klasoru kontrol ediliyor...
                    dir reports

                    echo [GIT] dvc.lock, .dvc/config ve reports klasoru commit'e ekleniyor...
                    git add -f dvc.lock .dvc/config
                    git add -f reports/

                    echo [GIT] Git status:
                    git status

                    echo [GIT] Commit denemesi...
                    git commit -m "CI: Add Security Reports and DVC Lock" || echo "Nothing to commit"

                    echo [GIT] Remote URL PAT ile guncelleniyor...
                    git remote set-url origin https://%GIT_USERNAME%:%GIT_PASSWORD%@github.com/akyilidizbaran/MLFLow-SecOPS.git

                    echo [GIT] main branch push ediliyor...
                    git push origin HEAD:main || echo "Push basarisiz oldu, loga bak."
                    '''
                }
            }
        }
    }

    post {
        always {
            bat '''
            echo [POST] Son durum raporu aliniliyor...

            if exist .venv\\Scripts\\activate (
                call .venv\\Scripts\\activate
                echo [POST] dvc status:
                dvc status || echo "dvc status post asamasinda hata verdi."
            ) else (
                echo [POST] .venv bulunamadi, dvc status atlanıyor.
            )

            echo [POST] Son commit:
            git log -1 --oneline || echo "Git log okunamadi."
            '''
        }
    }
}
