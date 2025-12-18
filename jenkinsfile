
pipeline {
    agent any

    tools {
        python 'python3'  // Use Python tool configured in Jenkins (or remove this if none)
    }

    environment {
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt || true' // skip if not present
            }
        }

        stage('Run Tests') {
            steps {
                sh 'pytest tests/'
            }
        }
    }

    post {
        always {
            echo 'CI pipeline finished.'
        }
    }
}
