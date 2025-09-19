pipeline {
    agent any

    stages {
        stage('Send POST Request') {
            steps {
                sh '''
                    echo "Sending POST request to localhost:8000..."
                    curl -X POST http://localhost:8000 \
                         -H "Content-Type: application/json" \
                         -d '{"message": "Hello from Jenkins!"}'
                '''
            }
        }
    }
}
