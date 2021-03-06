
import boto3
import botocore
import cv2
import hashlib
import json
import logging
import numpy
import os
import time


S3_URL = "https://{bucketName}.s3.ap-northeast-2.amazonaws.com/{keyName}"
DEST_S3_URL = "https://{bucketName}.s3.ap-northeast-2.amazonaws.com/{keyName}?t={timeStamp}"
#
# ''' get the hash value for an image '''
#
def hash_image(img):

    h = hashlib.sha256(img).hexdigest()

    return h

#
# ''' list images from a bucket of s3  '''
#
def listImages(reponse):

    result = {}
    for obj in reponse.get('Contents', []):
        if '/gray.' in obj['Key']:
            result['gray'] = S3_URL.format(bucketName = 'cartoonaf', keyName = obj['Key'])
        elif '/ep.' in obj['Key']:
            result['edgePreserving'] = S3_URL.format(bucketName = 'cartoonaf', keyName = obj['Key'])
        elif '/de.' in obj['Key']:
            result['detailEnhance'] = S3_URL.format(bucketName = 'cartoonaf', keyName = obj['Key'])
        elif '/style.' in obj['Key']:
            result['stylization'] = S3_URL.format(bucketName = 'cartoonaf', keyName = obj['Key'])
        elif '/ps-color.' in obj['Key']:
            result['pencilSketch_gray'] = S3_URL.format(bucketName = 'cartoonaf', keyName = obj['Key'])
        elif '/ps-gray.' in obj['Key']:
            result['pencilSketch_color'] = S3_URL.format(bucketName = 'cartoonaf', keyName = obj['Key'])
        elif '/source.' in obj['Key']:
            result['source'] = S3_URL.format(bucketName = 'cartoonaf', keyName = obj['Key'])

    return result


#
#  Main handler of lambda_function
#
def lambda_handler(event, context):

    print("==== event ===> {}".format(event))

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info('event parameter: {}'.format(event))

    src_filename = event['name']
    filter_name = event['filter']
    param_flags = event.get('flags',0)
    param_sigma_s = event.get('sigma_s',0)
    param_sigma_r = event.get('sigma_r',0.0)
    param_shade_factor = event.get('shade_factor',0.0)

    print("[DEBUG] param_sigma_r ===> {}".format(param_sigma_r))

    filename_set = os.path.splitext(src_filename)
    basename = filename_set[0]
    ext = filename_set[1]
    hashvalue = basename.split("/")[0]


    down_filename='/tmp/my_image{}'.format(ext)
    down_filename_filter='/tmp/my_image_filter{}'.format(ext)
    down_filename_filter_json='/tmp/my_image_filter.json'

    if os.path.exists(down_filename):
        os.remove(down_filename)
    if os.path.exists(down_filename_filter):
        os.remove(down_filename_filter)

    #
    # s3 = boto3.resource('s3')
    #
    s3 = boto3.client('s3')
    BUCKET_NAME = os.environ.get("BUCKET_NAME")
    S3_KEY = "public/{}".format(src_filename)

    try:
        # s3.Bucket(BUCKET_NAME).download_file(S3_KEY, down_filename)
        s3.download_file(BUCKET_NAME, S3_KEY, down_filename)        
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("===error message ===> {}".format(e))
            print("The object does not exist: s3://{}/{}".format(BUCKET_NAME, S3_KEY))
        else:
            raise

    #
    # Load an image from file system.
    #
    image_src = cv2.imread(down_filename)

    filter_filename='public/{basename}/{filtername}{ext}'.format(
        basename = hashvalue,
        filtername = filter_name,
        ext = ext
    )

    filter_jsonfile='public/{basename}/{filtername}.json'.format(
        basename = hashvalue,
        filtername = filter_name
    ) 

    print("[DEBUG] ===> {}".format(filter_filename))

    if filter_name == 'ep':
        image_ep = cv2.edgePreservingFilter(image_src, 
            flags=param_flags, 
            sigma_s=param_sigma_s, 
            sigma_r=param_sigma_r
        )
        cv2.imwrite(down_filename_filter, image_ep)

    elif filter_name == 'de':
        image_de  = cv2.detailEnhance(image_src, 
            sigma_s=param_sigma_s, 
            sigma_r=param_sigma_r
        )
        cv2.imwrite(down_filename_filter, image_de)

    elif filter_name == 'style':
        image_stylization = cv2.stylization(image_src, 
            sigma_s=param_sigma_s, 
            sigma_r=param_sigma_r
        )
        cv2.imwrite(down_filename_filter, image_stylization)

    elif filter_name == 'ps-gray':
        image_ps_gray, image_ps_color = cv2.pencilSketch(image_src, 
            sigma_s=param_sigma_s, 
            sigma_r=param_sigma_r, 
            shade_factor=param_shade_factor
        )
        cv2.imwrite(down_filename_filter, image_ps_gray)

    elif filter_name == 'ps-color':
        image_ps_gray, image_ps_color = cv2.pencilSketch(image_src, 
            sigma_s=param_sigma_s, 
            sigma_r=param_sigma_r, 
            shade_factor=param_shade_factor
        )
        cv2.imwrite(down_filename_filter, image_ps_color)

    # 삭제하신 후 제글도 삭제하세요.
    # Save json text to temp file.
    #
    j = {
        'flags' : param_flags,
        'sigma_s' : param_sigma_s,
        'sigma_r' : param_sigma_r,
        'shade_factor' : param_shade_factor
    }

    with open(down_filename_filter_json,'w') as f:
        f.write(json.dumps(j))

    #
    # s3 = boto3.client('s3')
    #
    s3.upload_file(down_filename_filter, BUCKET_NAME, filter_filename)
    s3.upload_file(down_filename_filter_json, BUCKET_NAME, filter_jsonfile)

    images = {
        "source" : S3_URL.format(
            bucketName = BUCKET_NAME, 
            keyName = src_filename
        ),
        "params" : j,
        "dest" : DEST_S3_URL.format(
            bucketName = BUCKET_NAME, 
            keyName = filter_filename,
            timeStamp = time.time()
        )
    }

        
    return {
        "statusCode": 200,
        "body": { "images": images }
    }

