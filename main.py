
from typing import List
from types import MethodType
from bson import ObjectId
import pymongo,json
from flask import Flask,request,jsonify
from pymongo import results
from twilio.rest import Client
from flask_cors import CORS
from bson.timestamp import Timestamp
import datetime as dt
from models.login import genotp,addNumberPhoneUser
from config.db import db

app = Flask(__name__)
CORS(app) 


@app.route('/')
def home():
    return "Hello World REST API"

#generate OTP 
@app.route('/LoginOTP',methods=['POST'])
def LoginOTP() :    
    numberphone=request.json["numberphone"]  
    otp=genotp()
    account_sid = "AC972c43f1b33f1b1fdf504a65febf75a4"
    auth_token = "d4d0c071f9597cc806ec2265996515bc"
    client = Client(account_sid, auth_token)
    client.api.account.messages.create(
    to="+66"+numberphone,
    from_="+13868537656",
    body="Your OTP : "+str(otp))
    addNumberPhoneUser(numberphone,otp)
    return {"message":"please check OTP SentTo Your mobilephone +66"+numberphone}
   
#verify OTP 
@app.route('/verifyOTP',methods=['POST'])
def VerifyOTP():
    numberphone=request.json["numberphone"]
    OTPconfirm=request.json["confirmOTP"]
    result=db.OTP.find_one({'numberphone':numberphone,'otp':OTPconfirm})
    if(result):
        db.OTP.delete_many({'numberphone':numberphone})             
        return {"status":True,"numberphone":numberphone}
        
    else:
        return {"message":" please verify your OTP agian!!"}


#add user to DB 
@app.route('/Adduser',methods=['POST'])
def Adduser():
    if request.method == 'POST':
        email=request.json["email"]
        password=request.json["password"]
        name=request.json["name"]
        lastname=request.json["lastname"]
        phoneNumber=request.json["numberphone"]
        if(db.Users.find_one({'numberphone':phoneNumber})):
            return {"messages":"phoneNumber has registered"}
        else:        
            result=db.Users.insert_one({"email":email,
            "password":password,
            "name":name,
            "lastname":lastname,
            "numberphone":phoneNumber})
            if(result):
                return {"messages":"Successful registration"}
      
#login 
@app.route('/Login',methods=['POST'])
def Login():
    email=request.json["email"]
    password=request.json["password"]
    result=db.Users.find_one({'email':email,'password':password})
    if(result):
        return {"message":"Login succes","status":True,
            "userinfo":[
            {
                "userid": str(result['_id']),
                "name":result['name'],
                "lastname":result['lastname']}]         
            }
    else: 
        return{ "message":"Login False" }

              

#get user one 
@app.route('/getuser/<string:userid>',methods=['GET'])
def getuser(userid):
    result=db.Users.find_one({"_id":ObjectId(userid)})
    return  {   
                "status":True,
                "userinfo":[{
                "userid": str(result['_id']),
                "name":result['name'],"lastname":result['lastname']}]              
            }


#get product from store url 
@app.route('/GetProducts/<string:store_ID>',methods = ['GET'])
def Getproduct(store_ID):   
    product=[]
    for x in db.product.find({'store_ID':store_ID}):
          product.append({"product_id":str(x["_id"]),
                          "product_name":x["proname"],
                          "product_price":x["price"],
                          "product_img":x["pro_img"],
                          "number":0})   
    return jsonify(product)
     


#add product to db  from store
@app.route('/addproduct',methods = ['POST'])
def Addproduct():
    if request.method == 'POST':
        if db.product.find_one({'proname':request.json["proname"]}):
            print(request.json["proname"])
            return {"messags":"product name is Alerdy"}
        else:
            db.product.insert_one({'proname':request.json["proname"],
                                   'price':request.json["price"],
                                   'pro_img':request.json["pro_img"],
                                   'stock_quantity':request.json["stock_quantity"],
                                   'store_ID':request.json["store_ID"]
                                   })
            return {"messags":"Add product success"}



#update data product from store 
@app.route('/UpdateProduct',methods=['PUT'])
def Updateproduct():
    productID=request.args.get('product_id')
    proname=request.json["proname"]
    price=request.json["price"]
    pro_img=request.json["pro_img"]
    prostock=request.json["stock_quantity"]
    result=db.product.update({"_id":ObjectId(productID)} ,{   
            "$set":{        
                "proname":proname,
                "price":price,
                "pro_img":pro_img,
                "stock_quantity":prostock,              
            }      
    })
    if(result):
        return {"messages":"update prodct success productID is "+productID,"status":True}



#post ordrs from user 
@app.route('/post_order',methods=['POST'])
def postOrder():
    timeNow=dt.datetime.now()
    orderlist={
    "userid":request.json["userid"],
    "bill_id":"GV",
    "store_ID":request.json["store_ID"],
    "date":Timestamp(int(dt.datetime.today().timestamp()), 1),
    "status_order":[
        {"time":"00:00","status":"จัดส่งสำเร็จ","check":False},
        {"time":"00:00","status":"สินค้ากำลังจัดส่ง","check":False},
        {"time":"00:00","status":"ผู้ขายกำลังเตรียมสินค้า","check":False},
        {"time":"00:00","status":"ยืนยันคำสั่งซื้อ","check":False}],
    "order_products":request.json["order_products"],
    "orderTime":timeNow.timestamp(),
    "Pickup_time":request.json["Pickup_time"],
    "note":request.json["note"]
    }
    result=db.orders.insert_one(orderlist)
    if(result):
        return {"message":"post order your success"}


def getstoreData(storeid):
    result=db.store.find_one({'store_ID':storeid})
    return result

#get orders for web from user 
@app.route('/getorder/<string:userid>',methods=['GET'])
def getorder(userid):
    orders=[]
    result_orders=db.orders.find({'userid':userid})
    storeid={}
    storedata='' 
    for x in result_orders:
        storeid=x['store_ID']
        storedata=getstoreData(storeid)
        orders.append(
        {
            'bill_id':x['bill_id'],
            'storename': str(storedata['storename']),
            'store_img':storedata['store_img']
         })

    #print(orders)
    #print(storeid) 
    return {"meesage":"getorder success","order":orders}



#getDetails for web 
@app.route('/getorderDetail/<string:bill_id>',methods=['GET'])
def getorderDetail(bill_id):
    orders=[]
    result_order=db.orders.find({'bill_id':bill_id})
    for x in result_order:
        orders.append({'orderList':x['order_products'],"status_order":x['status_order']})
    #print(orders) 
    return {"meesage":"getorder detail success","orders":orders}


#get order tracking for web status order success by user 
@app.route('/getordertracking/<string:userid>',methods=['GET'])
def getorderTcaking(userid):
    ordersTrace=[]
    storeid={}
    storeData=''   
    result=db.orders.find({"userid":userid,"status_order.status":"จัดส่งสำเร็จ","status_order.check":True})
    for x in result:
        storeid=x['store_ID']
        storeData=getstoreData(storeid)
        ordersTrace.append({
            'bill_id':x['bill_id'],
            'storename': str(storeData['storename']),
            'store_img':storeData['store_img'],
            'status_order':'จัดส่งสำเร็จ'
        })     
    return {"meesage":"getorder tracking success","orders":ordersTrace}


#post store 
@app.route('/poststore',methods=['POST'])
def postStore():
    storeID=request.json["store_ID"]
    storename=request.json["storename"]
    coordinates=request.json["coordinates"]
    userid=request.json["userid"]
    lat=request.json["lat"]
    longs=request.json["long"]
    result=db.store.insert_one({
         "store_ID":storeID,
         "storename":storename,
         "coordinates":coordinates,
         "userid":userid,
         "lat":lat,
         "long":longs})
    if(result):
        return {"message":"add store ","status":True}



#get store 
@app.route('/getstore/<string:userid>',methods=['GET'])
def getstore(userid):
    result=db.store.find_one({'userid':userid})
    return {
            'message':'getstore ok',
            "mystore":[{
            "store_ID": str(result["store_ID"]),
            "storename":result["storename"],
            "coordinates":result["coordinates"],
            "userid":result["userid"],
            "lat":result["lat"],
            "long":result["long"]}
            ]}



#create_link_store
@app.route('/createlink',methods=['POST'])
def createLink():
    url_phat="https:localhost:8000"
    produt_ID=request.json["produt_ID"]
    store_ID=request.json["store_ID"]
    Date=request.json["Date"]
    Delivery_time=request.json["Delivery_time"]
    Url_path=request.json["Url_path"]
    link_expired=request.json["link_expired"]
    result=db.LinkStore.insert_one(
    {   
        "productid":produt_ID,
        "store_ID":store_ID,
        "Date":Date,
        "Delivery_time":Delivery_time,
        "Url_path":Url_path,
        "link_expired":link_expired
        
    })
    if(result):
        return {"message":"create_link_store success","status":True,"url":url_phat}


#put status order  for mobile application 
@app.route('/updateStatusOrder/<string:bill_id>',methods=['PUT'])
def updateStatusOrder(bill_id):
    billid=bill_id
    result=db.orders.update({"status_order.status":"ยืนยันคำสั่งซื้อ","bill_id":billid},{   
            "$set":{        
                "check":True,                     
            }      
    })

    if(result):
        return {"message":"update status success"}



#post customer contact
@app.route('/postcustomerContact',methods=['POST'])
def postcustomerContact():
    userid=request.json["userid"]
    latitude=request.json["latitude"]
    longitude=request.json["longitude"]
    adress=request.json["adress"]
    userResult=db.customer_contract.find({'userid':userid})
    if(userResult):
        return {"status":False,"message":"CustomerContact Exit for user id : "+userid}        
    else:
        result=db.customer_contract.insert_one({'userid':userid,'latitude':latitude,'longitude':longitude,'adress':adress})
        if(result):
            return  {"status":True,"message":"postCustomerContact Success for user id : "}


#get customer contract 
@app.route('/getcustomerContact/<string:userid>',methods=['GET'])
def getContactUser(userid):
    output=[]
    result=db.customer_contact.find_one({'userid':userid})
    output.append({'userid':str(result['_id']),
                   'adress':result['adress'],
                   'latitude':result['latitude'],
                   'longitude':result['longitude']
                   })
    
    return {"status":True,"message":"getContactUser Success for user id : "+userid,"usercontact":output}


#get order for mobileApplication by vender 
@app.route('/GetorderStore/<string:store_ID>',methods=['GET'])
def GetorderStore(store_ID):
    orderStore=[]
    results=db.orders.find({'store_ID':store_ID})
    if(results):
        for x in results:
            orderStore.append({
                'bill_id':x['bill_id'],
                'orderTime':str(x['orderTime']),
                'order_products': x['order_products'],
                'Pickup_time':x['Pickup_time'],
                'note':x['note']     
                })
            #print(list(orderStore))
        return {"GetorderStore":"success","ordersStore":orderStore}





if __name__ == '__main__':
    app.run(debug=True,host="localhost",port=5000)
   

