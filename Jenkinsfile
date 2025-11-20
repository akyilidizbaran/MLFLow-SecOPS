pipeline {
    agent any

    environment {
        // MLflow sunucusunun adresi. Jenkins konteyneri aynı docker ağı üzerinde olduğu için
        // mlflow servisine "mlflow" hostname'i ile ulaşabilir.
        MLFLOW_TRACKING_URI = "http://mlflow:5000"
        // İsteğe bağlı: Eğer Kaggle bilgilerini doğrudan ortam değişkeni olarak vermek isterseniz
        // bunları Jenkins "Global properties" veya credentials ile ayarlayabilirsiniz.
        // KAGGLE_USERNAME = credentials('kaggle-username-id')
        // KAGGLE_KEY = credentials('kaggle-key-id')
    }

    stages {
        stage('Kodları Getir') {
            steps {
                // Kaynak kodu git repository'den çekiyoruz.
                checkout scm
            }
        }

        stage('Python ve Bağımlılıkları Kur') {
            steps {
                // CI ortamında ihtiyaç duyulan Python paketlerini kuruyoruz.
                // Varsayım: Jenkins ajanında python3 ve pip3 komutları hazır.
                sh '''
                    python3 -m pip install --upgrade pip
                    pip3 install --no-cache-dir -r app/requirements.txt
                '''
            }
        }

        stage('DVC ile Kaggle İndir + Eğitim') {
            steps {
                // Bu aşamada:
                // - DVC "download" stage Kaggle'dan veri setini indirir.
                // - DVC "train" stage modeli eğitir ve metrikleri üretir.
                //
                // NOT: Kaggle kullanıcı adı ve anahtarını güvenli şekilde saklamak için
                // Jenkins Credentials kullanılmalıdır. Aşağıdaki withCredentials bloğu
                // bir şablondur; kendi credentialsId değerlerinizi tanımlamalısınız.
                withCredentials([
                    string(credentialsId: 'kaggle-username-id', variable: 'KAGGLE_USERNAME'),
                    string(credentialsId: 'kaggle-key-id', variable: 'KAGGLE_KEY')
                ]) {
                    sh '''
                        echo "DVC pipeline (download + train) çalıştırılıyor..."
                        dvc repro
                        echo "DVC metrikleri:"
                        dvc metrics show || echo "DVC metrikleri gösterilemedi."
                    '''
                }
            }
        }

        stage('MLSecOps Denetimi (Şablon)') {
            steps {
                // Bu aşama, ileride MLSecOps kontrolleri için kullanılacaktır.
                // Örneğin: OWASP Top 10, MITRE ATLAS gibi güvenlik kontrol listeleri buraya entegre edilebilir.
                echo "MLSecOps denetimi burada çalıştırılacak (OWASP Top 10, MITRE ATLAS kontrolleri için şablon)."
            }
        }

        stage('DVC Snapshot ve Remote Push') {
            steps {
                // Bu aşamada DVC durumunu kontrol ediyor ve güncel veri/model artefaktlarını
                // önceden tanımlanmış bir DVC remote'a push ediyoruz.
                //
                // Ön Koşul:
                // - Lokal veya uzak bir DVC remote eklenmiş olmalıdır. Örneğin:
                //   dvc remote add -d origin <remote-url>
                //   dvc remote default origin
                sh '''
                    echo "DVC durum kontroli:"
                    dvc status || echo "DVC status komutu hata verdi."
                    echo "DVC remote'a artefaktlar push ediliyor..."
                    dvc push || echo "DVC push başarısız oldu, remote ayarlarını kontrol edin."
                '''
            }
        }

        stage('Artefaktları Arşivle') {
            steps {
                // Eğitim sonucu üretilen önemli dosyaları (metrikler ve model) arşivliyoruz.
                // Böylece Jenkins arayüzünden indirilebilir ve geçmiş build'lerle karşılaştırılabilir.
                archiveArtifacts artifacts: 'metrics.json,dvc.lock,models/model.pkl', fingerprint: true
            }
        }

        stage('Git Push (CI Sonrası)') {
            steps {
                // Bu aşamada DVC dosyalarındaki değişiklikler ve diğer güncellemeler
                // otomatik olarak commit ve push edilir.
                //
                // NOT: Git erişimi için Jenkins'te uygun bir credential (SSH key veya Access Token)
                // tanımlanmalıdır. Aşağıdaki withCredentials bloğu bir örnektir.

                withCredentials([
                    usernamePassword(
                        credentialsId: 'git-credentials-id',
                        usernameVariable: 'GIT_USERNAME',
                        passwordVariable: 'GIT_PASSWORD'
                    )
                ]) {
                    sh '''
                        git config user.email "ci@example.com"
                        git config user.name "jenkins-ci"

                        echo "Git durumu:"
                        git status

                        git add .
                        git commit -m "CI: update DVC snapshot [skip ci]" || echo "Commit yapılacak değişiklik yok."

                        # HTTPS remote kullanıldığını varsayıyoruz.
                        # Eğer SSH kullanacaksanız, bunun yerine SSH key ve uygun remote URL kullanmalısınız.
                        git push https://${GIT_USERNAME}:${GIT_PASSWORD}@$(git remote get-url origin | sed -e 's~https://~~') main || \
                          echo "Git push başarısız, uzak depo veya credential ayarlarını kontrol edin."
                    '''
                }
            }
        }
    }

    post {
        always {
            // Her build sonunda çalışma alanındaki DVC durumunu ve son commit mesajını gösteriyoruz.
            sh '''
                echo "Build sonrası özet:"
                dvc status || echo "DVC durumu okunamadı."
                git log -1 --oneline || echo "Git log alınamadı."
            '''
        }
    }
}

