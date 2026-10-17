
pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    stages {
        stage('Test') {
            steps {
                sh '''
                    python3 -m venv ci-venv
                    ci-venv/bin/pip install -r requirements.txt
                    ci-venv/bin/pip install -r requirements-dev.txt
                    ci-venv/bin/pytest -v
                '''
            }
        }

        stage('Build') {
            steps {
                sh '''
                    docker build -t document-management:${BUILD_NUMBER} .
                    docker tag document-management:${BUILD_NUMBER} document-management:latest
                '''
            }
        }
    }
}
