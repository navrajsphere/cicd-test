pipeline {
    agent any

    environment {
        BRANCH = "main"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: "${BRANCH}",
                    url: 'https://github.com/navrajsphere/cicd-test.git'
            }
        }

        stage('Python Script') {
            steps {
                script {
                    sh "python3 script.py"
                    echo "Python script ran successfully!!"
                }
            }
        }

  

  
    }

    post {
        always {
            cleanWs()
        }
    }
}
