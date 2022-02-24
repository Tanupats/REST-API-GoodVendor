from config.db import db,users
from bson import ObjectId
def GetuserData(_id):
    userinfo=users.find({'_id':ObjectId(_id)})
    contactuser=db.customer_contract.find({'userid':_id})
    name=''
    email=''
    numberphone=''
    address=''
    lat=''
    lang=''
    
    for x in userinfo:
        name=x['name']+" "+x['lastname']
        numberphone=x['numberphone']
        email=x['email']
    for a in contactuser:
        address=a['adress']
        lat=a['latitude']
        lang=a['longitude']
    
    return {
    'name':name,
    'numberphone':numberphone,
    'adress':address,
    'lat':lat,
    'lang':lang,
    'email':email
            }