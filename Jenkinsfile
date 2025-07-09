pipeline {
    agent any
    tools {
        python 'Python3' // Configured in Jenkins Global Tool Configuration
    }
    environment {
        DOCKER_IMAGE = "hamza27058/myapp:${env.BUILD_ID}" // Adjust to your Docker Hub namespace
        REGISTRY = 'docker.io/hamza27058' // Your Docker Hub registry
    }
    stages {
        stage('Checkout') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                    git branch: 'master', url: 'https://${GIT_USER}:${GIT_TOKEN}@github.com/Hamza27058/devops_boilerplate.git'
                }
            }
        }
        stage('Install Dependencies') {
            steps {
                sh 'python3 -m venv venv'
                sh '. venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt'
            }
        }
        stage('Static Code Analysis') {
            steps {
                sh '. venv/bin/activate && pylint **/*.py' // Adjust for your preferred linter (e.g., flake8)
            }
        }
        stage('Dependency Check') {
            steps {
                sh '. venv/bin/activate && pip install safety'
                sh '. venv/bin/activate && safety check -r requirements.txt --full-report'
            }
        }
        stage('Unit Tests') {
            steps {
                sh '. venv/bin/activate && pytest --junitxml=test-results.xml' // Adjust for your test framework
            }
            post {
                always {
                    junit 'test-results.xml' // Archive test results
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${REGISTRY}/${DOCKER_IMAGE}")
                }
            }
        }
        stage('Container Security Scan') {
            steps {
                sh "trivy image --exit-code 1 --severity HIGH,CRITICAL ${REGISTRY}/${DOCKER_IMAGE}"
            }
        }
        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    script {
                        docker.withRegistry('https://index.docker.io/v1/', 'docker-credentials') {
                            docker.image("${REGISTRY}/${DOCKER_IMAGE}").push()
                        }
                    }
                }
            }
        }
        stage('Deploy to Staging') {
            steps {
                sh 'docker-compose -f docker-compose.staging.yml up -d' // Adjust for your deployment method
            }
        }
        stage('Dynamic Security Testing') {
            steps {
                sh 'zap-cli --quick-scan http://staging.myapp.com' // Adjust for your DAST tool and URL
            }
        }
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Approve deployment to production?', ok: 'Deploy'
                sh 'docker-compose -f docker-compose.prod.yml up -d' // Adjust for your production deployment
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'test-results.xml', allowEmptyArchive: true
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check logs for details.'
        }
    }
}