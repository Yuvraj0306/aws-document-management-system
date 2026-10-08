pipeline {
    agent any

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
                echo 'Build stage completed.'
            }
        }
    }
}