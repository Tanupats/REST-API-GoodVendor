from typing import List
from types import MethodType
from bson import ObjectId
import pymongo,json
from flask import Flask,request,jsonify
from pymongo import results
from pymongo.message import _EMPTY
from twilio.rest import Client
from flask_cors import CORS
from bson.timestamp import Timestamp
import datetime as dt
from models.login import genotp,addNumberPhoneUser,genBill
from models.user import GetuserData
from config.db import db
import uuid
import os
from werkzeug.utils import secure_filename
import urllib.request
from datetime import date

app = Flask(__name__)
CORS(app) 

@app.route('/')
def home():
    return {"message":"Hello World REST API"}


today = date.today()






#generate OTP 
@app.route('/LoginOTP',methods=['POST'])
def LoginOTP() :    
    numberphone=request.json["numberphone"]  
    otp=genotp()
    account_sid = "AC972c43f1b33f1b1fdf504a65febf75a4"
    auth_token = "5e9c5bcb53f4f7189a7f835a5adc9e3d"
    client = Client(account_sid, auth_token)
    client.api.account.messages.create(to="+66"+numberphone,from_="+13868537656",body="GV-OTP : "+str(otp))
    addNumberPhoneUser(numberphone,otp)
    return {"message":"please check OTP SentTo Your mobilephone +66"+numberphone}


#verify OTP 
@app.route('/verifyOTP',methods=['POST'])
def VerifyOTP():
    numberphone=request.json["numberphone"]
    OTPconfirm=request.json["confirmOTP"]
    result=db.OTP.find_one({'numberphone':numberphone,'otp':OTPconfirm})
    if result:
        db.OTP.delete_many({'numberphone':numberphone})             
        return {"status":True,"numberphone":numberphone}      
    else:
        return {"message":" please verify your OTP agian!!"}


#add user or register  
@app.route('/Adduser',methods=['POST'])
def Adduser():
    if request.method == 'POST':
        email=request.json["email"]
        password=request.json["password"]
        name=request.json["name"]
        lastname=request.json["lastname"]
        phoneNumber=request.json["numberphone"]
        if db.Users.find_one({'numberphone':phoneNumber}):
            return {"messages":"phoneNumber has registered","status":False}
        else:        
            result=db.Users.insert_one({"email":email,
            "password":password,
            "name":name,
            "lastname":lastname,
            "numberphone":phoneNumber})
            if result:
                return {"messages":"Successful registration","status":True}
      
#login 
@app.route('/Login',methods=['POST'])
def Login():
    email=request.json["email"]
    password=request.json["password"]
    result=db.Users.find_one({'email':email,'password':password})
    if result:
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


#get products  from store  for mobileApp 
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
     

#add product from store
@app.route('/addproduct',methods = ['POST'])
def Addproduct():
    if request.method == 'POST':
        if db.product.find_one({'proname':request.json["proname"]}):
            return {"messags":"product name is Alerdy"}
        else:
            Price=request.json["price"]
            quantity=request.json["stock_quantity"]
            db.product.insert_one({'proname':request.json["proname"],
                                   'price': Price ,
                                   'pro_img':request.json["pro_img"],
                                   'stock_quantity':quantity,
                                   'store_ID':request.json["store_ID"]
                                   })
            return {"messags":"Add product success"}


#get product from productID 
@app.route('/getProduct/<string:_id>',methods=['GET'])
def getProduct(_id):
    proname=''
    price=''
    stock_quantity=''
    proID=''
    result=db.product.find({'_id':ObjectId(_id)})  
    for x in result:    
        proname=x['proname']
        price=str(x['price'])
        stock_quantity=str(x['stock_quantity'])
        proID=str(x['_id'])      
    return {"messages":"getProduct Success","id":proID,"proname":proname,"price":price,"stock_quantity":stock_quantity}



#update data product from store 
@app.route('/UpdateProduct',methods=['PUT'])
def Updateproduct():
    productID=request.args.get('product_id')
    proname=request.json["proname"]
    price=request.json["price"]
    prostock=request.json["stock_quantity"]
    result=db.product.update({"_id":ObjectId(productID)} ,{   
            "$set":{        
                "proname":proname,
                "price":price,
                "stock_quantity":prostock,              
            }      
    })
    if result:
        return {"messages":"update prodct success "+productID,"status":True}




#post ordrs from user 
@app.route('/post_order',methods=['POST'])
def postOrder():
    timeNow=dt.datetime.now()
    orderlist={
    "userid":request.json["userid"],
    "bill_id":"GV"+genBill(),
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
    if result:
        return {"message":"post order your success"}


def getstoreData(storeid):
    output={}
    result=db.store.find({'store_ID':storeid})
    for x in result:
        output={'name':x['storename'],'store_img':x['store_img']}
    return output


#get orders for web from user 
@app.route('/getorder/<string:userid>',methods=['GET'])
def getorder(userid):
    orders=[]
    result_orders=db.orders.find({'userid':userid})
    storeid=""
    for x in result_orders:
        storeid=x['store_ID']
        storename=getstoreData(storeid)['name']
        storeimg=getstoreData(storeid)['store_img']
        orders.append(
        {
            'bill_id':x['bill_id'],
            'storename':storename,
            'store_img':storeimg,
            'status_order':'ยืนยันคำสั่งซื้อ'
         })
    return {"meesage":"getorder success","order":orders}



#getDetails for web 
@app.route('/getorderDetail/<string:bill_id>',methods=['GET'])
def getorderDetail(bill_id):
    orders=[]
    result_order=db.orders.find({'bill_id':bill_id})
    for x in result_order:
        orders.append({'orderList':x['order_products'],"status_order":x['status_order']})
    #print(orders) 
    return {"meesage":"getorder detail success","orders":orders,'bill_id':bill_id}



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
            'storename': str(storeData['name']),
            'store_img':storeData['store_img'],
            'status_order':'จัดส่งสำเร็จ'
        })     
    return {"meesage":"getorder tracking success","orders":ordersTrace}


#post store  register for vendor 
@app.route('/Createstore',methods=['POST'])
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
        return {"message":"add store your success","status":True}


#get Mystore  for mobile Application 
@app.route('/getstore/<string:userid>',methods=['GET'])
def getstore(userid):
    mystore={}
    result=db.store.find({'userid':userid})
    for x in result:
        mystore={"storeID":x['store_ID'],
                        "id":str(x['_id']),
                        "storename":x['storename'],
                        "store_img":x['store_img']
                        }
    return {"message":"getdata mystore success","mystore":mystore}

 
#create_link_store for mobile Application 
@app.route('/createlink',methods=['POST'])
def createLink():  
    d1 = today.strftime("%d/%m/%Y")
    products=request.json["products"]
    store_ID=request.json["store_ID"]
    Date=d1
    Delivery_time=request.json["Delivery_time"]
    Url_path=store_ID+str(uuid.uuid4()) 
    link_expired=request.json["link_expired"]
    result=db.LinkStore.insert_one(
    {   
        "products":products,
        "store_ID":store_ID,
        "Date":Date,
        "Delivery_time":Delivery_time,
        "Url_path":Url_path,
        "link_expired":link_expired
    })
    if(result):
        return {"message":"create_link_store success","status":True,"link_store":Url_path}



#getDataLinkStores for MobileApp
@app.route('/getDataLinkStores/<string:storeID>',methods=['GET'])
def getDataLinkStores(storeID):
    results=db.LinkStore.find({'store_ID':storeID})
    print(list(results))
    return {"message":"GetDataLinkStore success"}



#getproduct from link store sale for WebApp
@app.route('/GetProductShop/<string:linkStoreID>',methods=['GET'])
def GetProductShop(linkStoreID):
    products=[]
    output=[]
    storeID=""
    result = db.LinkStore.find({'Url_path':linkStoreID})
    if result:
        for x in result:
            products=x['products']
            storeID=x['store_ID']
        for product in products:
            output.append({ 
                            "product_id":product["product_id"],
                            "product_name":product["proname"],
                            "product_price":product["price"],
                            "product_img":product["pro_img"],
                            "number":0})                          
    return {"products":output,"storeID":storeID}

   




#update status order  for mobile application 
@app.route('/updateStatusOrder/<string:bill_id>/<string:statusnum>',methods=['PUT'])
def updateStatusOrder(bill_id,statusnum):

    if statusnum == '1':
        db.orders.update_one(
                {
                "bill_id":bill_id,"status_order.status":"ยืนยันคำสั่งซื้อ"},
                {"$set":{"status_order.$.check":True,"status_order.$.time":request.json["Time"]} }
                )
    elif statusnum =='2':
         db.orders.update_one(
                {
                "bill_id":bill_id,"status_order.status":"ผู้ขายกำลังเตรียมสินค้า"},
                {"$set":{"status_order.$.check":True,"status_order.$.time":request.json["Time"]} }
                )
    elif statusnum =='3':
         db.orders.update_one(
                {
                "bill_id":bill_id,"status_order.status":"สินค้ากำลังจัดส่ง"},
                {"$set":{"status_order.$.check":True,"status_order.$.time":request.json["Time"]} }
                )
    elif statusnum =='4':
         db.orders.update_one(
                {
                "bill_id":bill_id,"status_order.status":"จัดส่งสำเร็จ"},
                {"$set":{"status_order.$.check":True,"status_order.$.time":request.json["Time"]} }
                )

    return {"message":"update status success"}



#post customer contract
@app.route('/customerContract',methods=['POST'])
def postcustomerContact():
    userid=request.json["userid"]
    latitude=request.json["latitude"]
    longitude=request.json["longitude"]
    adress=request.json["adress"] 
    result=db.customer_contract.insert_one({'userid':userid,'latitude':latitude,'longitude':longitude,'adress':adress})
    if(result):
        return  {"status":True,"message":"postCustomerContract Success"}


#get customer  one contract 
@app.route('/getcustomerContact/<string:userid>',methods=['GET'])
def getContactUser(userid):
    output=[]
    result=db.customer_contract.find({'userid':userid})
    if result :
        for x in result:
            output.append({
                        'adress':x['adress'],
                        'latitude':x['latitude'],
                        'longitude':x['longitude']
                        })
        return {"status":True,"message":"getContactUser Success","usercontact": output }

     





#function get data products 
def getProductList(productList):
    finalpro=''
    for n in productList:
            finalpro+='\n'+n['product_name']+" "+str(n['number'])+ " กิโลกรัม"
    return(finalpro)


#get order for mobileApplication by vender 
@app.route('/GetorderStore/<string:store_ID>',methods=['GET'])
def GetorderStore(store_ID):
    orderStore=[]
    results=db.orders.find({'store_ID':store_ID})
    productList=''

    if(results):
        for x in results:      
            productList=x['order_products']
            orderStore.append({
                'bill_id':x['bill_id'],
                'Pickup_time':x['Pickup_time'],
                'note':x['note'],               
                'name':GetuserData(x['userid'])['name'],
                'numberphone':GetuserData(x['userid'])['numberphone'],
                'adress':GetuserData(x['userid'])['adress'],
                'products':getProductList(productList)       
                }) 
        #print(productList)
        #print(getProductList(productList))         
        return {"GetorderStore":"success","ordersStore":orderStore}


UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        resp = jsonify({
            'status' : False,
            'message' : 'Image is not defined'})
        resp.status_code = 400
        return resp

    files = request.files.getlist('image')

    errors = {}
    success = False

    for photo in files:

        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            success = True
        else:
            errors[photo.filename] = 'Image type is not allowed'

    if success and errors:
        errors['message'] = jsonify({
            'data' : photo.filename,
            'status' : True,
            'message' : 'Image(s) successfully uploaded'})
        resp = jsonify(errors)
        resp.status_code = 500
        return resp

    if success:
        resp = jsonify({
            'data' : photo.filename,
            'status' : True,
            'message' : 'Images successfully uploaded'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify(errors)
        resp.status_code = 500
        return resp

if __name__ == '__main__':
    app.run(debug=True,host="localhost",port=5000)
   

