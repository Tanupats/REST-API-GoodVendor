

from bson import ObjectId
from flask.helpers import send_file
import pymongo,json
from flask import Flask,request,jsonify
from pymongo import results
from pymongo import response
from twilio.rest import Client
from flask_cors import CORS
from bson.timestamp import Timestamp
from models.login import genotp,addNumberPhoneUser,genBill
from models.user import GetuserData
from models.sendEmail import senEmail
from config.db import db
import uuid
import os
from werkzeug.utils import secure_filename
import urllib.request
from datetime import date
from datetime import datetime

import os, time
app = Flask(__name__)
CORS(app) 


#set API send SMS to Device 
app.config['ACCOUNT_SID']="AC972c43f1b33f1b1fdf504a65febf75a4"
app.config['AUTH_TOKEN']="b570a83b6dc958bdf37bbb21569dadac"

#set phat for upload File 
UPLOAD_FOLDER = 'uploads/reviews'
UPLOAD_FOLDER_PRODUCT='uploads/products'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_PRODUCT']=UPLOAD_FOLDER_PRODUCT
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


today = date.today()
d1 = today.strftime("%d/%m/%Y")
now = datetime.now()


@app.route('/')
def home():
    return {"message":"Hello World REST API"}

#Login OTP for users 
@app.route('/LoginOTP',methods=['POST'])
def LoginOTP() :    
    numberphone=request.json["numberphone"]  
    otp=genotp()
    account_sid = app.config['ACCOUNT_SID']
    auth_token = app.config['AUTH_TOKEN']
    PHONE_NUMBER="+13868537656"
    client = Client(account_sid, auth_token)
    client.api.account.messages.create(to="+66"+numberphone,from_=PHONE_NUMBER,body="GV-OTP : "+str(otp))
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
            result=db.Users.insert_one(
            {"email":email,
            "password":password,
            "name":name,
            "lastname":lastname,
            "numberphone":phoneNumber})
            if result:
                return {"messages":"Successful registration","status":True,"userid":str(result.inserted_id)}



#login for users  get email or numberphone 
@app.route('/Login',methods=['POST'])
def Login():
    username=request.json["email"]
    password=request.json["password"]
    result=db.Users.find_one({'email':username,'password':password})
    results=db.Users.find_one({'numberphone':username,'password':password})
    if result:
        return {"message":"Login succes","status":True,
            "userinfo":
                {
                    "userid": str(result['_id']),
                    "name":result['name'],
                    "lastname":result['lastname'],
                    "User_Type":result['User_Type']
                 }                  
            } 

    if results:
        return {"message":"Login succes","status":True,
            "userinfo":[
            {
                "userid": str(results['_id']),
                "name":results['name'],
                "lastname":results['lastname']}]         
            } 
    else:
        return { "message":"เข้าสู่ระบบไม่สำเร็จ","status":False }

              

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
                          "number":x["stock_quantity"]})   
    return jsonify(product)
     

#add product from store
@app.route('/addproduct',methods = ['GET','POST'])
def Addproduct():
    Price=request.form.get("price")
    quantity=request.form.get("stock_quantity")
    proname=request.form.get("proname")
    storeId=request.form.get("store_ID")
    if db.product.find_one({'proname':proname}):
        return {"messags":"product name is Alerdy"}
    else:
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
            photo.save(os.path.join(app.config['UPLOAD_FOLDER_PRODUCT'], filename))
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
            'pro_img' : photo.filename,
            'status' : True,
            'message' : 'Images successfully uploaded and save dataProduct'})
        resp.status_code = 200
        datapro = {    'proname':proname,
                                   'price':Price,
                                   'pro_img':photo.filename,
                                   'stock_quantity':quantity,
                                   'store_ID':storeId
                    }
        result =  db.product.insert_one(datapro)
        if result:
            return resp
    else:
        resp = jsonify(errors) 
        
        resp.status_code = 500
        return resp
        


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
@app.route('/UpdateProduct/<string:proID>',methods=['PUT'])
def Updateproduct(proID):
    proname=request.json["proname"]
    price=request.json["price"]
    prostock=request.json["stock_quantity"]
    query={"_id":ObjectId(proID)} 
    newvalue={   
            "$set":{        
                "proname":proname,
                "price":int(price),
                "stock_quantity":int(prostock),              
            }      
    }
    result=db.product.update_one(query,newvalue)
    if(result):
        return {"messages":"update prodct success ","status":True}





@app.route('/Notification',methods=['POST'])
def sendNotification():
    storeID="GV5389" 
    response=fcm.sendNotification(storeID)
    if(response==200):
        return {"massage":"sendNotification success"}

#send notification 
import fcmManager as fcm



#post ordrs from user 
@app.route('/post_order',methods=['POST'])
def postOrder():
    Date=d1
    current_time = now.strftime("%H:%M:%S")
    storeID=request.json["store_ID"]
    orderlist={
    "userid":request.json["userid"],
    "store_ID":storeID,
    "date":Date,
    "status_order":[
        {"time":"00:00","status":"จัดส่งสำเร็จ","check":False},
        {"time":"00:00","status":"สินค้ากำลังจัดส่ง","check":False},
        {"time":"00:00","status":"ผู้ขายกำลังเตรียมสินค้า","check":False},
        {"time":"00:00","status":"ยืนยันคำสั่งซื้อ","check":False}],
    "status":"รอผู้ขายยืนยันคำสั่งซื้อ",
    "order_products":request.json["order_products"],
    "orderTime": current_time,
    "Pickup_time":request.json["Pickup_time"],
    "note":request.json["note"]
    }
    result=db.orders.insert_one(orderlist)
    if result:
         response=fcm.sendNotification(storeID)
         if(response==200):
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
    result_orders=db.orders.find({"userid":userid,"status":"รอผู้ขายยืนยันคำสั่งซื้อ"})
    storeid=""
    for x in result_orders:
        storeid=x['store_ID']
        storename=getstoreData(storeid)['name']
        storeimg=getstoreData(storeid)['store_img']
        orders.append(
        {
            'bill_id': str(x['_id']),
            'storename':storename,
            'store_img':storeimg,
            'status_order':x['status']
         })
    return {"meesage":"getorder success","order":orders}


#get ordersAction for web from user status operating  
@app.route('/getorderAction/<string:userid>/<string:status>',methods=['GET'])
def getorderAction(userid,status):
    orders=[]
    result_orders=db.orders.find({"userid":userid,'status':status})
    storeid=""
    for x in result_orders:
        storeid=x['store_ID']
        storename=getstoreData(storeid)['name']
        storeimg=getstoreData(storeid)['store_img']
        orders.append(
        {
            'bill_id': str(x['_id']),
            'storename':storename,
            'store_img':storeimg,
            'status_order':x['status']
         })
    return {"meesage":"getorderAction","order":orders}




#getDetails for web 
@app.route('/getorderDetail/<string:bill_id>',methods=['GET'])
def getorderDetail(bill_id):
    orders=[]
    result_order=db.orders.find({'_id':ObjectId(bill_id)})
    for x in result_order:
        orders.append({'orderList':x['order_products'],"status_order":x['status_order']})
    return {"meesage":"getorder detail success","orders":orders,'bill_id':bill_id}



#get order tracking for web status order success by user 
@app.route('/getordertracking/<string:userid>',methods=['GET'])
def getorderTcaking(userid):
    ordersTrace=[]
    storeid=""
    storeData=''   
    result=db.orders.find({"userid":userid,"status":"จัดส่งสำเร็จ"})
    for x in result:
        storeid=x['store_ID']
        storeData=getstoreData(storeid)
        ordersTrace.append({
            'bill_id': str(x['_id']),
            'storename': str(storeData['name']),
            'store_img':storeData['store_img'],
            'status_order':x['status']
        })     
    return {"meesage":"getorder tracking success","orders":ordersTrace}


#post store  register for vendor 
@app.route('/Createstore',methods=['POST'])
def postStore():
    storeID="GV"+genBill()
    storename=request.json["storename"]
    coordinates=request.json["coordinates"]
    userid=request.json["userid"]
    lat=request.json["lat"]
    longs=request.json["long"]
    result=db.store.insert_one({
         "store_ID":storeID,
         "storename":storename,
         "coordinates":int(coordinates),
         "userid":userid,
         "lat":lat,
         "long":longs,
         "token":""
         })
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
    products=request.json["products"]
    store_ID=request.json["store_ID"]
    Dates=request.json["Date"]
    Delivery_time=request.json["Delivery_time"]
    Url_path=store_ID+str(uuid.uuid4()) 
    link_expired=request.json["link_expired"]
    result=db.LinkStore.insert_one(
    {   
        "products":products,
        "store_ID":store_ID,
        "Date":Dates,
        "Delivery_time":Delivery_time,
        "Url_path":Url_path,
        "link_expired":link_expired
    })
    if(result):
        return {"message":"create_link_store success","status":True,"link_store":Url_path}



#getData LinkStores for MobileApp
@app.route('/getDataLinkStores/<string:storeID>',methods=['GET'])
def getDataLinkStores(storeID):
    outputLinks=[]
    results=db.LinkStore.find({'store_ID':storeID})
    for x in results:
        outputLinks.append({
                            'id':str(x['_id']),                          
                            'Date':x['Date'],
                            'Delivery_time':x['Delivery_time'],
                            'Url_path':x['Url_path'],
                            'link_expired':x['link_expired']
                            })

    return jsonify({"message":"GetDataLinkStore success","Links":outputLinks})  


#delete LinkStore 
@app.route('/DeleteLink/<string:LinkID>',methods=['DELETE'])
def DeleteLink(LinkID):
    result = db.LinkStore.delete_many({'_id':ObjectId(LinkID)})
    if result :
        return {"message":"delete sucess"}



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
                            "product_name":product["product_name"],
                            "product_price":int(product["product_price"]) ,
                            "product_img":product["product_img"],
                            "number":0})                          
        storeData=getstoreData(storeID)['name']
        return {"products":output,"storeID":storeID,"storename":storeData}



#update status order  for mobile application 
@app.route('/updateStatusOrder/<string:bill_id>/<string:status>',methods=['PUT'])
def updateStatusOrder(bill_id,status):  
    current_time = now.strftime("%H:%M:%S")
    
    if status == 'order_confirmation':
        db.orders.update_one(
                {
                "_id":ObjectId(bill_id),"status_order.status":"ยืนยันคำสั่งซื้อ"},
                {"$set":{"status":"ยืนยันคำสั่งซื้อ","status_order.$.check":True,"status_order.$.time":current_time} }
                )
    elif status =='Preparing':
         db.orders.update_one(
                {
                "_id":ObjectId(bill_id),"status_order.status":"ผู้ขายกำลังเตรียมสินค้า"},
                {"$set":{"status":"ผู้ขายกำลังเตรียมสินค้า","status_order.$.check":True,"status_order.$.time":current_time} }
                )
    elif status =='shipping':
         db.orders.update_one(
                {
                "_id":ObjectId(bill_id),"status_order.status":"สินค้ากำลังจัดส่ง"},
                {"$set":{"status":"สินค้ากำลังจัดส่ง","status_order.$.check":True,"status_order.$.time":current_time} }
                )
    elif status =='Successful_delivery':
         db.orders.update_one(
                {
                "_id":ObjectId(bill_id),"status_order.status":"จัดส่งสำเร็จ"},
                {"$set":{"status":"จัดส่งสำเร็จ","status_order.$.check":True,"status_order.$.time":current_time} }
                )

    return {"message":"update status success"}



#post customer contract
@app.route('/customerContract',methods=['POST'])
def postcustomerContact():
    userid=request.json["userid"]
    latitude=request.json["latitude"]
    longitude=request.json["longitude"]
    adress=request.json["adress"] 
    if db.customer_contract.find_one({'userid':userid}):
        return  {"status":False,"message":"Contact information has been added."}
    else:
        result=db.customer_contract.insert_one(
        {'userid':userid,
        'latitude':latitude,
        'longitude':longitude,
        'adress':adress})
        if(result):
            return  {"status":True,"message":"postCustomerContract Success."}



#get customer  one contract 
@app.route('/getcustomerContact/<string:userid>',methods=['GET'])
def getContactUser(userid):
    output=[]
    result=db.customer_contract.find({'userid':userid})
    users=db.Users.find_one({'_id':ObjectId(userid)})
    if result :
        for x in result:
            output.append({
                        'adress':x['adress'],
                        'latitude':x['latitude'],
                        'longitude':x['longitude'],
                        'numberphone':users['numberphone'],
                        'name':users['name']
                        })
        return {"status":True,"message":"getContactUser Success","usercontact": output }

     


#function get data products 
def getProductList(productList):
    finalpro=''
    for n in productList:
            finalpro+="\n"+n['product_name']+" "+str(n['number'])
    return(finalpro)


#get order for mobileApplication by vender 
@app.route('/GetorderStore/<string:store_ID>/<string:status>',methods=['GET'])
def GetorderStore(store_ID,status):
    orderStore=[]
    results=db.orders.find({'store_ID':store_ID,'status':status})
    productList=''
    if(results):
        for x in results:      
            productList=x['order_products']
            usersdata=GetuserData(x['userid'])
            orderStore.append({
                'bill_id': str(x['_id']) , 
                'Pickup_time':x['Pickup_time'],
                'note':x['note'],               
                'name':usersdata['name'],
                'numberphone':usersdata['numberphone'],
                'adress':usersdata['adress'],
                'lat':usersdata['lat'],
                'lang':usersdata['lang'],
                'products':getProductList(productList),
                'ordertime':x['orderTime']       
                })         
        return jsonify(orderStore) 
    
           



#save review score 
@app.route('/SaveReview',methods = ['GET','POST'])
def SaveReview():

    order_id=request.form.get("orderID")
    rate_detail=request.form.get("rate_detail")
    value=request.form.get("value")

    check_review=db.Rateting.find_one({'orderID':order_id})
    if check_review:
        return {"message":"your  reviwe  is already or Edit reviwe"}
    else:
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
            'review_img' : photo.filename,
            'status' : True,
            'message' : 'save reviews is billID'+order_id})
        resp.status_code = 200
        db.Rateting.insert_one({'orderID':order_id,'img_upload':photo.filename,'rate_detail':rate_detail,'value':int(value)})
        return resp
    else:
        resp = jsonify(errors)
        resp.status_code = 500
        return resp  
     


#get review score 
@app.route('/GetReview/<string:orderID>',methods=['GET'])
def GetReview(orderID):
    output={}
    result = db.Rateting.find({'orderID':orderID})
    for x in result:
        output={'orderID':x['orderID'] ,'img_upload':x['img_upload'], 'rate_detail':x['rate_detail'] ,'value':x['value']}
    return output



#update reviw score 
@app.route('/updateReview',methods=['PUT'])
def updateReview():
    orderID=request.json["bill_id"]
    rate_detail=request.json["rate_detail"]
    query={'orderID':orderID}
    value=request.json["value"]
    newvalue = {
                "$set":{
                        "rate_detail":rate_detail,
                        "value":value
                       }
    }
    update=db.Rateting.update_one(query,newvalue)
    if update:
        return {"messasge":"update your review succes orderID is "+orderID}



@app.route('/upload', methods=['POST'])
def upload_image():
    title=request.form.get("title")
    print(title)
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

@app.route('/getimage/<string:filename>')
def getimg(filename):
    Files='uploads/products/'+filename
    return send_file(Files,mimetype="image/jpg")


@app.route('/GetimageReview/<string:filename>')
def Getimg(filename):
    Files='uploads/reviews/'+filename
    return send_file(Files,mimetype="image/jpg")


@app.route('/sendEmail',methods=['POST'])
def SendEmail():
    email=request.json['email']
    senEmail(email)
    return {"message":"เช็ครหัสยืนยันในอีเมลของคุณ"}


@app.route('/gettokens/<string:storeID>',methods=['GET'])
def gettokens(storeID):
    result=db.store.find({'store_ID':storeID})
    Token=""
    for a in result:
        Token=a['token']
    if Token=="":
        return {"message":"token is Empty","status":False}
    else:
        return {"message":"gettoken ok","status":True}



#update token for device Mobile App.
@app.route('/updateTokens',methods=['PUT'])
def updateToken():
    storeID=request.json["store_ID"]
    token=request.json["token"]
    query={'store_ID':storeID}
    value={
        "$set":
            {'token':token}
    }
    update=db.store.update_one(query,value)
    if(update):
        return {"message":"updated tokens storeID is "+storeID}
 




#ร้องขออนุมัติ 
@app.route('/GetAllshops',methods=['GET'])
def GetAllshops():
    output=[]
    _id=""
    result = db.store.find({})
    for a in result:
        _id=a['userid']
        userdetail= GetuserData(_id)
        output.append({
            'author':
                {
                    'avatar':'',
                    'name':userdetail['name'],
                    'email':userdetail['email']
                },
                    'func': {
                    'job': a['storename'],
                    'department': a['store_ID'],
			            },
			'status': a['status_confirm'],
			'employed':a['registration_date']           
                })
    return jsonify(output)     



#อนุมัติ 
@app.route('/Getapproved',methods=['GET'])
def Getapproved():
    output=[]
    _id=""
    result = db.store.find({'status_confirm':True})
    for a in result:
        _id=a['userid']
        userdetail= GetuserData(_id)
        output.append({
            'author':
                {
                    'avatar':'',
                    'name':userdetail['name'],
                    'email':userdetail['email']
                },
                    'func': {
                    'job': a['storename'],
                    'department': a['store_ID'],
			            },
			'status': a['status_confirm'],
			'employed':a['registration_date']           
            })
    return jsonify(output) 



#ยังไม่อนุมัติ 
@app.route('/Getdisapproved',methods=['GET'])
def Getdisapproved():
    output=[]
    _id=""
    result = db.store.find({'status_confirm':False})
    for a in result:
        _id=a['userid']
        userdetail= GetuserData(_id)
        output.append({
            'author':
                {
                    'avatar':'',
                    'name':userdetail['name'],
                    'email':userdetail['email']
                },
                    'func': {
                    'job': a['storename'],
                    'department': a['store_ID'],
			            },
			'status': a['status_confirm'],
			'employed':a['registration_date']           
            })
    return jsonify(output) 


@app.route('/confirmStore/<string:storeID>')
def confirmstore(storeID):
    query={'store_ID':storeID}
    value={
        "$set":
            {'status_confirm':True}
    }
    update=db.store.update_one(query,value)
    if(update):
        return {"message":"updated statusconfirm success","status":True}



if __name__ == '__main__':
    app.run(debug=True,host="localhost",port=5000)



