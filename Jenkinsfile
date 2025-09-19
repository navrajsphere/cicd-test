pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                // Pull code from repo
                checkout scm
            }
        }

        stage('Run Python Script') {
            steps {
                sh '''
                    echo "Running Python script..."
                    python3 script.py
                '''
            }
        }
    }
}
