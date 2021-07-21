import datetime
import requests
import cv2
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import json
import ibmiotf.application
import ibmiotf.device
import random
import time

from cloudant.client import Cloudant
from cloudant.error import CloudantException 
from cloudant.result import Result, ResultByKey
#Provide your IBM Watson Device Credentials
organization = "7x37hm"
deviceType = "facedetect"
deviceId = "1001"
authMethod = "token"
authToken = "1234567890"


url = "https://face-mask-detection.p.rapidapi.com/FaceMaskDetection"

    
# Constants for IBM COS values
COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud" # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
COS_API_KEY_ID = "QgMp-B0GKTnFu3FkdmGeo681oR1UA-RUdTidTkisG5a-" # eg "W00YixxxxxxxxxxMB-odB-2ySfTrFBIQQWanc--P3byk"
COS_AUTH_ENDPOINT = "https://iam.cloud.ibm.com/identity/token"
COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/cfdf24503963447ba9432271b7cbd1df:eec1510a-7347-40be-bdff-746117c6639e::"

client = Cloudant("apikey-v2-1t8pu8xkov65lsjznpkb1mbe1f0mb3v0g1slyih3sd7d", "bdff9d8bf839712fd47c65cb06ce00e1", url="https://apikey-v2-1t8pu8xkov65lsjznpkb1mbe1f0mb3v0g1slyih3sd7d:bdff9d8bf839712fd47c65cb06ce00e1@bd453ab0-a5bd-4358-b64d-83ca7948d553-bluemix.cloudantnosqldb.appdomain.cloud")
client.connect()
database_name = "facedetect"


# Create resource
cos = ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_INSTANCE_CRN,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)

bucket = "mdetect"
def multi_part_upload(bucket_name, item_name, file_path):
    try:
        print("Starting file transfer for {0} to bucket: {1}\n".format(item_name, bucket_name))
        # set 5 MB chunks
        part_size = 1024 * 1024 * 5

        # set threadhold to 15 MB
        file_threshold = 1024 * 1024 * 15

        # set the transfer threshold and chunk size
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )

        # the upload_fileobj method will automatically execute a multi-part upload
        # in 5 MB chunks for all files over 15 MB
        with open(file_path, "rb") as file_data:
            cos.Object(bucket_name, item_name).upload_fileobj(
                Fileobj=file_data,
                Config=transfer_config
            )

        print("Transfer for {0} Complete!\n".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to complete multi-part upload: {0}".format(e))

video_capture = cv2.VideoCapture(0)
while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Display the resulting image
    cv2.imshow('Live', frame)
    picname=datetime.datetime.now().strftime("%y-%m-%d-%H-%M")
    picname=picname+".jpg"
    pic=datetime.datetime.now().strftime("%y-%m-%d-%H-%M")
    cv2.imwrite(picname,frame)
    my_database = client.create_database(database_name)
    multi_part_upload(bucket, picname,pic+".jpg")
    payload="linkfile=https://mdetect.s3.jp-tok.cloud-object-storage.appdomain.cloud/"+picname
    if my_database.exists():
            print("'{database_name}' successfully created.")
            json_document = {
                     "link":"https://mdetect.s3.jp-tok.cloud-object-storage.appdomain.cloud/"+picname
    }
    time.sleep(1)
    #print data
    def myOnPublishCallback():
            print ("Published data to IBM Watson")
    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'x-rapidapi-key': "92bc4dfae7mshf453994a97ab7c0p168e9fjsn8fe751cd72a8",
        'x-rapidapi-host': "face-mask-detection.p.rapidapi.com"
        }
    
    response = requests.request("POST", url, data=payload, headers=headers)
    print(response.text)

    a=json.loads(response.text)
    x0=a["data"][0]["x0"]
    y0=a["data"][0]["y0"]
    x1=a["data"][0]["x1"]
    y1=a["data"][0]["y1"]
    print(type(a))
    if(a["data"][0]["masked"]==0):       
        print("face detected with no mask")
        img=cv2.putText(frame,'No Mask', (x0,(y0-10)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        img=cv2.rectangle(img,(x0,y0),(x1,y1),  (0, 0, 255), 2)
    elif(a["data"][0]["masked"]==1):
        print("face detected with mask")
        img=cv2.putText(frame,'Mask', (x0,(y0-10)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        img=cv2.rectangle(img,(x0,y0),(x1,y1),  (0, 0, 255), 2)

    cv2.imshow('Processed',img)
    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()



