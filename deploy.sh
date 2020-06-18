#!/bin/bash
# Create the Lambda function:
./compress.sh
ROLE_NAME=lambda-opencv_study
ZIPFILE=allinone.zip
FUNCTION_NAME=opencv_allinone
ACCOUNT_ID=$(aws sts get-caller-identity | jq -r ".Account")
BUCKET_NAME=cartoonaf
#aws s3 mb s3://$BUCKET_NAME
S3_KEY=images/my_image.jpg
aws s3 cp $ZIPFILE s3://$BUCKET_NAME
#aws lambda create-function --function-name $FUNCTION_NAME --timeout 10 --role arn:aws:iam::${ACCOUNT_ID}:role/$ROLE_NAME --handler app.lambda_handler --region ap-northeast-2 --runtime python3.7 --environment "Variables={BUCKET_NAME=$BUCKET_NAME,S3_KEY=$S3_KEY}" --code S3Bucket="$BUCKET_NAME",S3Key="$ZIPFILE"
#aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://$ZIPFILE
aws lambda update-function-code --function-name $FUNCTION_NAME --region ap-northeast-2 --s3-bucket $BUCKET_NAME --s3-key $ZIPFILE
