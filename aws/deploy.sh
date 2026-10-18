#!/bin/bash
# Launch the GPU box. Read aws/COSTS.md first: this spends real money.
# Needs: AWS CLI logged in, a key pair, and a security group that opens 5000.
set -e

KEY_NAME="${KEY_NAME:?set KEY_NAME to your EC2 key pair name}"
SG_ID="${SG_ID:?set SG_ID to a security group id with port 5000 open}"
SUBNET_ID="${SUBNET_ID:?set SUBNET_ID to your subnet id}"
INSTANCE_TYPE="${INSTANCE_TYPE:-g5.12xlarge}"  # g5.xlarge if you only need Whisper
REGION="${REGION:-us-east-1}"
# Deep Learning AMI (Ubuntu, NVIDIA drivers pre-installed) - update id per region
AMI="${AMI:-ami-0abcdef1234567890}"

echo "Launching $INSTANCE_TYPE in $REGION ... (on-demand, billed per hour)"
INSTANCE_ID=$(aws ec2 run-instances \
  --region "$REGION" \
  --image-id "$AMI" \
  --instance-type "$INSTANCE_TYPE" \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --subnet-id "$SUBNET_ID" \
  --user-data "file://$(dirname "$0")/user-data.sh" \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=video-summarizer}]' \
  --query 'Instances[0].InstanceId' --output text)

echo "Instance: $INSTANCE_ID"
echo "Watch it boot: aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress'"
echo "STOP it when done or it keeps billing: aws ec2 stop-instances --instance-ids $INSTANCE_ID"
