
import boto3
import botocore
import cv2
import hashlib
import json
import logging
import numpy
import os


S3_URL = "https://{bucketName}.s3.ap-northeast-2.amazonaws.com/{keyName}"
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
    filename_set = os.path.splitext(src_filename)
    basename = filename_set[0]
    ext = filename_set[1]

    down_filename='/tmp/my_image{}'.format(ext)
    down_filename_gray='/tmp/my_image_gray{}'.format(ext)
    down_filename_ep='/tmp/my_image_ep{}'.format(ext)
    down_filename_de='/tmp/my_image_de{}'.format(ext)
    down_filename_style='/tmp/my_image_style{}'.format(ext)
    down_filename_ps_gray='/tmp/my_image_ps_gray{}'.format(ext)
    down_filename_ps_color='/tmp/my_image_ps_color{}'.format(ext)


    if os.path.exists(down_filename):
        os.remove(down_filename)
    if os.path.exists(down_filename_gray):
        os.remove(down_filename_gray)
    if os.path.exists(down_filename_ep):
        os.remove(down_filename_ep)
    if os.path.exists(down_filename_de):
        os.remove(down_filename_de)
    if os.path.exists(down_filename_style):
        os.remove(down_filename_style)
    if os.path.exists(down_filename_ps_gray):
        os.remove(down_filename_ps_gray)
    if os.path.exists(down_filename_ps_color):
        os.remove(down_filename_ps_color)

    #
    # s3 = boto3.resource('s3')
    #
    s3 = boto3.client('s3')
    BUCKET_NAME = os.environ.get("BUCKET_NAME")
    S3_KEY = src_filename

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

    #
    # Extract a hash value from an image.
    #
    image_bytes = cv2.imencode(ext, image_src)[1]
    hash_str = hash_image(image_bytes)

    source_filename='public/{}/source{}'.format(hash_str,ext)
    gray_filename='public/{}/gray{}'.format(hash_str,ext)
    ep_filename='public/{}/ep{}'.format(hash_str,ext)
    de_filename='public/{}/de{}'.format(hash_str,ext)
    style_filename='public/{}/style{}'.format(hash_str,ext)
    ps_gray_filename='public/{}/ps-gray{}'.format(hash_str,ext)
    ps_color_filename='public/{}/ps-color{}'.format(hash_str,ext)

    try:

        response =s3.list_objects_v2(
            Bucket = BUCKET_NAME, 
            Prefix = "public/{}".format(hash_str)
        )

        results = listImages(response)
        if len(results) != 0:
            ''' Remove the uploaded file because this file exists on s3 '''
            s3.delete_object(Bucket=BUCKET_NAME, Key=S3_KEY)

            ''' return results '''
            return {
                "statusCode": 200,
                "body": {
                    "hash" : hash_str,
                    "images": results
                },
            }

    except botocore.exceptions.ClientError as e:
        print("[DEBUG] ERROR = {}".format(e))


    print("[DEBUG] no image = {}".format(hash_str))

    image_gray = cv2.cvtColor(image_src, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(down_filename_gray, image_gray)

    image_ep = cv2.edgePreservingFilter(image_src, flags=1, sigma_s=60, sigma_r=0.4)
    cv2.imwrite(down_filename_ep, image_ep)

    image_de  = cv2.detailEnhance(image_src, sigma_s=10, sigma_r=0.15)
    cv2.imwrite(down_filename_de, image_de)

    image_stylization = cv2.stylization(image_src, sigma_s=60, sigma_r=0.45)
    cv2.imwrite(down_filename_style, image_stylization)

    image_ps_gray, image_ps_color = cv2.pencilSketch(image_src, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
    cv2.imwrite(down_filename_ps_gray, image_ps_gray)
    cv2.imwrite(down_filename_ps_color, image_ps_color)

    #
    # s3 = boto3.client('s3')
    #
    s3.upload_file(down_filename, BUCKET_NAME, source_filename)
    s3.upload_file(down_filename_gray, BUCKET_NAME, gray_filename)
    s3.upload_file(down_filename_ep, BUCKET_NAME, ep_filename)
    s3.upload_file(down_filename_de, BUCKET_NAME, de_filename)
    s3.upload_file(down_filename_style, BUCKET_NAME, style_filename)
    s3.upload_file(down_filename_ps_gray, BUCKET_NAME, ps_gray_filename)
    s3.upload_file(down_filename_ps_color, BUCKET_NAME, ps_color_filename)


    images = {
        "source" : S3_URL.format(bucketName = BUCKET_NAME, keyName = source_filename),
        "gray" : S3_URL.format(bucketName = BUCKET_NAME, keyName = gray_filename),
        "edgePreserving" : S3_URL.format(bucketName = BUCKET_NAME, keyName = ep_filename),
        "detailEnhance" : S3_URL.format(bucketName = BUCKET_NAME, keyName = de_filename),
        "stylization" : S3_URL.format(bucketName = BUCKET_NAME, keyName = style_filename),
        "pencilSketch_gray" : S3_URL.format(bucketName = BUCKET_NAME, keyName = ps_gray_filename),
        "pencilSketch_color" : S3_URL.format(bucketName = BUCKET_NAME, keyName = ps_color_filename)
    }

    s3.delete_object(Bucket=BUCKET_NAME, Key=S3_KEY)
    return {
        "statusCode": 200,
        "body": {
            "hash" : hash_str,
            "images": images
        },
    }

