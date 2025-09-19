import logging
import time
import boto3
import paramiko
from config import *

def build_and_push_image():
    """
    The main background task. This function will:
    1. Create a spot EC2 instance.
    2. SSH into it and run the build process.
    3. Terminate the instance.
    """
    ec2_client = boto3.client(
        'ec2',
        region_name=AWS_REGION
    )
    
    instance_id = None
    try:
        # 1. Request a Spot Instance
        logging.info("Requesting Spot EC2 instance...")
        spot_request = ec2_client.request_spot_instances(
            InstanceCount=1,
            LaunchSpecification={
                'ImageId': AMI_ID,
                'InstanceType': INSTANCE_TYPE,
                'KeyName': KEY_NAME,
                'SecurityGroupIds': [SECURITY_GROUP_ID],
            },
            SpotPrice='0.01' # Max price you are willing to pay
        )
        request_id = spot_request['SpotInstanceRequests'][0]['SpotInstanceRequestId']
        
        # Wait for the request to be fulfilled
        waiter = ec2_client.get_waiter('spot_instance_request_fulfilled')
        waiter.wait(SpotInstanceRequestIds=[request_id])
        
        # Get the instance ID
        result = ec2_client.describe_spot_instance_requests(SpotInstanceRequestIds=[request_id])
        instance_id = result['SpotInstanceRequests'][0]['InstanceId']
        logging.info(f"Spot request fulfilled. Instance ID: {instance_id}")

        # Wait until the instance is running
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        # Get the public IP address of the instance
        instance_details = ec2_client.describe_instances(InstanceIds=[instance_id])
        public_ip = instance_details['Reservations'][0]['Instances'][0]['PublicIpAddress']
        logging.info(f"Instance is running at IP: {public_ip}")

        # Give the instance a moment to initialize
        time.sleep(30)

        # 2. SSH into the new instance and run commands
        logging.info("Connecting to instance via SSH...")
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=public_ip, username='ubuntu', key_filename=SSH_KEY_PATH)

        # The full script to run on the remote machine
        # We chain commands with '&&' to stop if one fails.
        commands = [
            'sudo apt-get update -y',
            'sudo apt-get install -y docker.io git',
            'sudo usermod -aG docker ubuntu', # Add ubuntu user to docker group
            f'git clone {REPO_URL} app_repo',
            'cd app_repo',
            # Note: Using sudo for docker commands as group change requires new login
            f'echo {DOCKER_HUB_PASSWORD} | sudo docker login --username {DOCKER_HUB_USERNAME} --password-stdin',
            f'sudo docker build -t {DOCKER_IMAGE_NAME}:latest .',
            f'sudo docker push {DOCKER_IMAGE_NAME}:latest'
        ]
        full_command = " && ".join(commands)

        logging.info("Executing remote commands...")
        stdin, stdout, stderr = ssh_client.exec_command(full_command)
        
        # Log output for debugging
        stdout_output = stdout.read().decode()
        stderr_output = stderr.read().decode()
        logging.info(f"STDOUT:\n{stdout_output}")
        if stderr_output:
            logging.error(f"STDERR:\n{stderr_output}")

        ssh_client.close()
        
        # 7. Status report (logging)
        logging.info("Successfully built and pushed Docker image to Docker Hub.")

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)

    finally:
        # 8. Terminate the spot instance
        if instance_id:
            logging.info(f"Terminating instance {instance_id}...")
            ec2_client.terminate_instances(InstanceIds=[instance_id])
            logging.info(f"Instance {instance_id} termination initiated.")


if __name__ == "__main__":
    build_and_push_image()
