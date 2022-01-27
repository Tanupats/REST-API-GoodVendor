import requests
import json
from config.db import db

def sendNotification(storeID):

    deviceToken=""
    result=db.store.find({'store_ID':storeID}) 
    for a in result:
        deviceToken=a['token']
    
    serverToken='AAAAyUVAl84:APA91bESa6gqr04uti79giLDhHOietQrqmMu0PjE_wlQ2qAJu9MQzzT8a1aBUcaQzF_ZijfJmZTwnIpMShxLZotXpkIlH3h06GibuBji-Y62ZBsETs7jmuopSHq2e2iVwCADExt4Rvh1'
   
    
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'key=' + serverToken,
    }
    body={
    'body':
        {
          'notification': { 'title': 'แจ้งเตือนคำสั่งซื้อสินค้าใหม่ตอนนี้',
                            'body': 'สถาน่ะรอผู้ขายยืนยันคำสั่งซื้อ'
                          },
          "data": {"click_action":"FLUTTER_NOTIFICATION_CLICK"},
          'to':deviceToken,
          'priority': 'high',
          
        }
    }
    response = requests.post("https://fcm.googleapis.com/fcm/send",headers = headers, data=json.dumps(body['body']))
    return response.status_code

    