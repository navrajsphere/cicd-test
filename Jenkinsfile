pipeline {
  agent any

  environment {
    REGION = 'ap-south-1'             // change to your region
    AMI = 'ami-xxxxxxxx'              // change to your AMI
    INSTANCE_TYPE = 't3.medium'
    KEY_NAME = 'my-aws-keypair'       // AWS keypair name
    SUBNET_ID = 'subnet-xxxx'
    SG_IDS = 'sg-xxxx'                // space separated if multiple
    REPO_URL = 'https://github.com/yourorg/yourrepo.git'
    REPO_NAME = 'yourrepo'
  }

  triggers {
    // the GitHub plugin + webhook will trigger builds on push
    githubPush()
  }

  stages {
    stage('Prepare') {
      steps {
        // ensure boto3 is present
        sh 'python3 -m pip install --user boto3 || true'
        checkout scm
      }
    }

    stage('Launch Spot') {
      steps {
        // If using aws-creds (username/password) for AWS keys:
        withCredentials([usernamePassword(credentialsId: 'aws-creds', usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
          sh """
            python3 launch_spot.py \
              --region ${env.REGION} \
              --ami ${env.AMI} \
              --instance-type ${env.INSTANCE_TYPE} \
              --key-name ${env.KEY_NAME} \
              --subnet-id ${env.SUBNET_ID} \
              --security-group-ids ${env.SG_IDS} \
              --tag-name jenkins-spot-builder > spot.json
          """
        }
        // If you use instance role for Jenkins, skip withCredentials wrapper
        script {
          def spot = readJSON file: 'spot.json'
          env.SPOT_INSTANCE_ID = spot.InstanceId
          env.SPOT_IP = spot.PublicIp
          echo "Instance ${env.SPOT_INSTANCE_ID} @ ${env.SPOT_IP}"
        }
      }
    }

    stage('SSH & Build on Spot') {
      steps {
        // inject Docker Hub credentials and use SSH agent for key
        withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
          sshagent(['spot-ssh-key']) {
            // pass env variables into remote shell; tag uses build number and commit
            script {
              def tag = env.BUILD_NUMBER
              sh """
                # run deploy.sh on remote host; REPO_NAME used by deploy.sh
                ssh -o StrictHostKeyChecking=no ubuntu@${env.SPOT_IP} 'REPO_NAME=${env.REPO_NAME} REPO_URL=${env.REPO_URL} DOCKER_USER=${DOCKER_USER} DOCKER_PASS=${DOCKER_PASS} TAG=${tag} bash -s' < deploy.sh
              """
            }
          }
        }
      }
    }

    stage('Terminate Spot') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'aws-creds', usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
          sh """
            python3 - <<'PY'
import boto3,sys,os
ec2=boto3.client('ec2', region_name='${env.REGION}')
ec2.terminate_instances(InstanceIds=['${env.SPOT_INSTANCE_ID}'])
print('terminate requested')
PY
          """
        }
      }
    }
  }

  post {
    failure {
      echo "Build failed — check logs. Attempting to terminate spot instance..."
      // attempt to clean up
      withCredentials([usernamePassword(credentialsId: 'aws-creds', usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
        sh "python3 - <<'PY'\nimport boto3\nb=boto3.client('ec2', region_name='${env.REGION}')\ntry: b.terminate_instances(InstanceIds=['${env.SPOT_INSTANCE_ID}']); print('terminate attempted')\nexcept Exception as e: print('terminate failed:', e)\nPY"
      }
    }
  }
}
