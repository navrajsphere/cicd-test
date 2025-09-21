pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = "507508956373.dkr.ecr.ap-southeast-1.amazonaws.com"    // e.g., docker.io / <aws_account_id>.dkr.ecr.<region>.amazonaws.com
        DOCKER_REPO = "test"   // e.g., myuser/myapp
        DOCKER_IMAGE = "myapp"
        BRANCH = "main"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: "${BRANCH}",
                    url: 'https://github.com/navrajsphere/cicd-test.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${DOCKER_REGISTRY}/${DOCKER_REPO}")
                }
            }
        }

        stage('Login to Registry') {
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", "docker-credentials-id") {
                        echo "Logged in to registry"
                    }
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", "docker-credentials-id") {
                        dockerImage.push()
                        dockerImage.push("latest")
                    }
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
