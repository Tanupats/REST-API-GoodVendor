
from cmath import asin, cos, sqrt
from unittest import result
from bson import ObjectId
from flask.helpers import send_file
from flask import Flask,request,jsonify
from twilio.rest import Client
from flask_cors import CORS
from models.login import genotp,addNumberPhoneUser,genBill
from models.user import GetuserData
from models.sendEmail import senEmail
from config.db import db
import uuid
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import time
app = Flask(__name__)
CORS(app) 



#set API send SMS to Device 
app.config['ACCOUNT_SID']="AC972c43f1b33f1b1fdf504a65febf75a4"
app.config['AUTH_TOKEN']="8362f3acd03acc13db35b8124f9768bc"
app.config['PHONE_NUMBER']="+13868537656"


#set phat for upload File 
UPLOAD_FOLDER = 'uploads/reviews'
UPLOAD_FOLDER_PRODUCT='uploads/products'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_PRODUCT']=UPLOAD_FOLDER_PRODUCT
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#get dateTime 
today = datetime.today()
day = today.strftime("%d/%m/%Y")

@app.route('/',methods=['GET'])
def home():
    return {"message":"hello"}

#Login OTP for users 
@app.route('/api/LoginOTP',methods=['POST'])
def LoginOTP() :    
    numberphone=request.json["numberphone"]  
    otp=genotp()
    account_sid = app.config['ACCOUNT_SID']
    auth_token = app.config['AUTH_TOKEN']
    PHONE_NUMBER= app.config['PHONE_NUMBER']
    client = Client(account_sid, auth_token)
    client.api.account.messages.create(to="+66"+numberphone,from_=PHONE_NUMBER,body="GV-OTP : "+str(otp))
    addNumberPhoneUser(numberphone,otp)
    return {"message":"ตรวจสอบรหัสยืนยัน OTP ที่ส่งไปยังหมายเลขโทรศัพท์ +66"+numberphone}


#verify OTP 
@app.route('/api/verifyOTP',methods=['POST'])
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
@app.route('/api/Adduser',methods=['POST'])
def Adduser():
    if request.method == 'POST':
        email=request.json["email"]
        password=request.json["password"]
        name=request.json["name"]
        lastname=request.json["lastname"]
        phoneNumber=request.json["numberphone"]
        userType=request.json["User_Type"]
        #if db.Users.find_one({'numberphone':phoneNumber}):
            #return {"messages":"phoneNumber has registered","status":False}
        #else:        
        result=db.Users.insert_one(
            {"email":email,
            "password":password,
            "name":name,
            "lastname":lastname,
            "numberphone":phoneNumber,
            "User_Type":userType        
            })
        if result:
            return {"messages":"Successful registration","status":True,"userid":str(result.inserted_id)}



#login for users  
@app.route('/api/Login',methods=['POST'])
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
            "userinfo":
            {
                "userid": str(results['_id']),
                "name":results['name'],
                "lastname":results['lastname']}      
            } 
    else:
        return { "message":"เข้าสู่ระบบไม่สำเร็จ","status":False }

              

#getdata user 
@app.route('/api/getuser/<string:userid>',methods=['GET'])
def getuser(userid):
    output={}
    _id=ObjectId(userid)
    result=db.Users.find({'_id':_id})
    for user in result:
        output={"name":user['name'] +" "+ user['lastname'],"numberphone":user['numberphone']}
    print(list(result))
    return  jsonify(output)




#get products  from store  for mobileApp 
@app.route('/api/GetProducts/<string:store_ID>',methods = ['GET'])
def Getproduct(store_ID):   
    product=[]
    for x in db.product.find({'store_ID':store_ID}):
          product.append({"product_id":str(x["_id"]),
                          "product_name":x["proname"],
                          "product_price":x["price"],
                          "product_img":x["pro_img"],
                          "number":x["stock_quantity"],
                          "value":False
                          })   
    return jsonify(product)



#add product from store
@app.route('/api/addproduct',methods = ['GET','POST'])
def Addproduct():
    Price=request.form.get("price")
    quantity=request.form.get("stock_quantity")
    proname=request.form.get("proname")
    storeId=request.form.get("store_ID")
  
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
        result =  db.product.insert_one({ 
                                   'proname':proname,
                                   'price':Price,
                                   'pro_img':photo.filename,
                                   'stock_quantity':quantity,
                                   'store_ID':storeId
                    })
        resp = jsonify({
            'pro_img' : photo.filename,
            'status' : True,
            'message' : 'Images successfully uploaded and save dataProduct'})
        resp.status_code = 200
       
        if result:
            
            return resp
    else:
        resp = jsonify(errors) 
        
        resp.status_code = 500
        return resp
        


#get product from productID 
@app.route('/api/getProduct/<string:_id>',methods=['GET'])
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
@app.route('/api/UpdateProduct/<string:proID>',methods=['PUT'])
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


#send notification 
import fcmManager as fcm


#post ordrs from user to mobileApp 
@app.route('/api/post_order',methods=['POST'])
def postOrder():
    time = request.json["ordertime"]
    storeID=request.json["store_ID"]
    total=request.json["total"]
    orderlist={
    "userid":request.json["userid"],
    "store_ID":storeID,
    "date":day,
    "status_order":[
        {"time":"00:00","status":"จัดส่งสำเร็จ","check":False},
        {"time":"00:00","status":"สินค้ากำลังจัดส่ง","check":False},
        {"time":"00:00","status":"ผู้ขายกำลังเตรียมสินค้า","check":False},
        {"time":"00:00","status":"ยืนยันคำสั่งซื้อ","check":False}],
    "status":"รอผู้ขายยืนยันคำสั่งซื้อ",
    "order_products":request.json["order_products"],
    "orderTime": time,
    "Pickup_time":request.json["Pickup_time"],
    "note":request.json["note"],
    "total":total,
    }
    result=db.orders.insert_one(orderlist)
    if result:
         title='แจ้งเตือนคำสั่งซื้อสินค้าใหม่ตอนนี้'
         body='สถาน่ะรอผู้ขายยืนยันคำสั่งซื้อ'
         data={'click_action':'FLUTTER_NOTIFICATION_CLICK','neworder':'1234'}
         response=fcm.sendNotification(storeID,title,body,data)
         if(response==200):
            print(response)
            return {"message":"post order your success"}



def getstoreData(storeid):
    output={}
    if storeid:
        result=db.store.find({'store_ID':storeid})
        for x in result:
            output={'name':x['storename'],'store_img':x['store_img']}
        return output
    else :return {'name':''} 


#get orders for web from user 
@app.route('/api/getorder/<string:userid>',methods=['GET'])
def getorder(userid):
    orders=[]
    result_orders=db.orders.find({"userid":userid,"status":"รอผู้ขายยืนยันคำสั่งซื้อ"}).sort('orderTime',-1)
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
            'status_order':x['status'],
            'total':x['total'],
            'order_time':x['orderTime']
         })
    return {"message":"getorder success","order":orders}



#get ordersAction for web from user status operating  
@app.route('/api/getorderAction/<string:userid>/<string:status>',methods=['GET'])
def getorderAction(userid,status):
    orders=[]
    
    result_orders=db.orders.find({"userid":userid,'status':status}).sort('orderTime',-1)
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
            'status_order':x['status'],
            'total':x['total'],
            'order_time':x['orderTime']
         })
    return {"meesage":"getorderAction","order":orders}




#getDetails for web 
@app.route('/api/getorderDetail/<string:bill_id>',methods=['GET'])
def getorderDetail(bill_id):
    orders=[]
    result_order=db.orders.find({'_id':ObjectId(bill_id)})
    for x in result_order:
        orders.append({'orderList':x['order_products'],"status_order":x['status_order']})
    return {"meesage":"getorder detail success","orders":orders,'bill_id':bill_id}



#post store  register for vendor 
@app.route('/api/Createstore',methods=['POST'])
def postStore():
    storeID="GV"+genBill()
    storename=request.json["storename"]
    coordinates=request.json["coordinates"]
    userid=request.json["userid"]
    lat=request.json["lat"]
    longs=request.json["long"]
    token=request.json["token"]
    result=db.store.insert_one({
         "store_ID":storeID,
         "storename":storename,
         "coordinates":int(coordinates),
         "userid":userid,
         "lat":lat,
         "long":longs,
         "store_img":"https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSFylME2j0-3Lllfe1N6nGX5qjgYBHHXTbojA&usqp=CAU",
         "token":token,
         "registration_date":day,
         "status_confirm":"ยื่นคำร้อง"
         })
    if(result):
        return {"message":"add store your success","status":True}


#get Mystore  for mobile Application  
@app.route('/api/getstore/<string:userid>',methods=['GET'])
def getstore(userid):
    mystore={}
    status=''
    result=db.store.find({'userid':userid})
    for x in result:
        if x['status_confirm']=='ยื่นคำร้อง':
            status=False
        else:status=x['status_confirm'] 
        mystore={       "storeID":x['store_ID'],
                        "id":str(x['_id']),
                        "storename":x['storename'],
                        "store_img":x['store_img'],
                        "status_confirm":status
                        }
    return jsonify(mystore)


 
#create_link_store for mobile Application 
@app.route('/api/createlink',methods=['POST'])
def createLink():  
    products=request.json["products"]
    store_ID=request.json["store_ID"]
    Dates=request.json["Date"]
    dateTimest=time.mktime(datetime.strptime(Dates,"%d/%m/%Y").timetuple())
    Delivery_time=request.json["Delivery_time"]
    Url_path=store_ID+str(uuid.uuid4()) 
    link_expired=request.json["link_expired"]
    todayTime=today.timestamp()

    if dateTimest >= todayTime:
        
        result=db.LinkStore.insert_one(
        {   
            "products":products,
            "store_ID":store_ID,
            "Date":dateTimest,
            "Delivery_time":Delivery_time,
            "Url_path":Url_path,
            "link_expired":link_expired
        })
        if(result):
            return {"message":"create_link_store success","status":True,"link_store":Url_path}
    
    else:
        return {"message":"ข้อมูลวันที่ไม่ถูกต้อง","status":False}
 

#getData LinkStores for MobileApp
@app.route('/api/getDataLinkStores/<string:storeID>',methods=['GET'])
def getDataLinkStores(storeID):
    outputLinks=[]
    results=db.LinkStore.find({"store_ID":storeID}).sort("Date",-1)
    for x in results:
        date_cre=datetime.fromtimestamp(x['Date'])
        outputLinks.append({
                            'id':str(x['_id']),                          
                            'Date': date_cre,
                            'Delivery_time':x['Delivery_time'],
                            'Url_path':x['Url_path'],
                            'link_expired':x['link_expired']
                            })

    return jsonify(outputLinks)  


#delete LinkStore 
@app.route('/api/DeleteLink/<string:LinkID>',methods=['DELETE'])
def DeleteLink(LinkID):
    result = db.LinkStore.delete_many({'_id':ObjectId(LinkID)})
    if result :
        return {"message":"delete sucess"}



#getproduct from link store sale for WebApp 
@app.route('/api/GetProductShop/<string:linkStoreID>',methods=['GET'])
def GetProductShop(linkStoreID):
    products=[]
    output=[]
    storeID=""
    date=""
    Delivery_time=""
    result = db.LinkStore.find({'Url_path':linkStoreID})
    if result:
        for x in result:
            products=x['products']
            storeID=x['store_ID']
            date=datetime.fromtimestamp(x['Date'])
            Delivery_time=x['Delivery_time']
        for product in products:
            output.append({ 
                            "product_id":product["product_id"],
                            "product_name":product["product_name"],
                            "product_price":int(product["product_price"]) ,
                            "product_img":product["product_img"],
                            "number":0})                          
        storeData=getstoreData(storeID)['name']    
        return {"products":output,"storeID":storeID,"storename":storeData,"date":date,"Delivery_time":Delivery_time}



#update status order  for mobile application 
@app.route('/api/updateStatusOrder/<string:bill_id>/<string:status>',methods=['PUT'])
def updateStatusOrder(bill_id,status): 
    datecurrent=request.json["time"]
    if status == 'order_confirmation':
        db.orders.update_one(
                {
                "_id":ObjectId(bill_id),"status_order.status":"ยืนยันคำสั่งซื้อ"},
                {"$set":{"status":"ยืนยันคำสั่งซื้อ","status_order.$.check":True,"status_order.$.time":datecurrent} }
                )
    elif status =='Preparing':
         db.orders.update_one(
                {
                "_id":ObjectId(bill_id),"status_order.status":"ผู้ขายกำลังเตรียมสินค้า"},
                {"$set":{"status":"ผู้ขายกำลังเตรียมสินค้า","status_order.$.check":True,"status_order.$.time":datecurrent} }
                )
    elif status =='shipping':
         db.orders.update_one(
                {
                "_id":ObjectId(bill_id),"status_order.status":"สินค้ากำลังจัดส่ง"},
                {"$set":{"status":"สินค้ากำลังจัดส่ง","status_order.$.check":True,"status_order.$.time":datecurrent} }
                )
    elif status =='Successful_delivery':
         db.orders.update_one(
                {
                "_id":ObjectId(bill_id),"status_order.status":"จัดส่งสำเร็จ"},
                {"$set":{"status":"จัดส่งสำเร็จ","status_order.$.check":True,"status_order.$.time":datecurrent} }
                )

    return {"message":"update status success"}


#post customer contract
@app.route('/api/PostContract',methods=['POST'])
def postcustomerContact():
    data=request.json
    result=db.customer_contract.insert_one(data)
    if(result):
        return  {"status":True,"message":"postCustomerContract Success."}



#update contract  
@app.route('/api/updateContract/<string:userid>',methods=['PUT'])
def updatecontract(userid): 
    lat=request.json["latitude"]
    long=request.json["longitude"]
    adress=request.json["adress"]
    details=request.json["details"]
    query={'userid':userid}
    newvalue = {"$set":{"latitude":lat,"longitude":long,"adress":adress,"details":details }}
    if db.customer_contract.update_one(query,newvalue):
        return {"message":"update contract user id is"+userid}



#get customer  one contract 
@app.route('/api/getcustomerContact/<string:userid>',methods=['GET'])
def getContactUser(userid):
    output={}
    result=db.customer_contract.find({'userid':userid})
    users=db.Users.find_one({'_id':ObjectId(userid)})
    if result:
        for x in result:
            output={
                        'adress':x['adress'],
                        'details':x['details'],
                        'latitude':x['latitude'],
                        'longitude':x['longitude'],
                        'numberphone':users['numberphone'],
                        'name':users['name']+"  "+users['lastname']
                        }
    if output:
        return {"status":True,"message":"getContactUser Success","usercontact": output }       
    else:   
        return{"status":False,"message":"No ContactUser",}                 
            

     


#function get data products 
def getProductList(productList):
    finalpro=''
    for n in productList:
            finalpro+="\n"+n['product_name']+" "+str(n['number'])
    return(finalpro)


#get order for mobileApplication by vender 
@app.route('/api/GetorderStore/<string:store_ID>/<string:status>',methods=['GET'])
def GetorderStore(store_ID,status):
    orderStore=[]
    results=db.orders.find({'store_ID':store_ID,'status':status}).sort('orderTime',-1)
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
                'ordertime':x['orderTime'],    
                'total':x['total']      
                })         
        return jsonify(orderStore) 



#getorder  delivery
@app.route('/api/GetorderDelivery/<string:store_ID>',methods=['GET'])
def GetorderDelivery(store_ID):
    orderStore=[]
    resultspre=db.orders.find({'store_ID':store_ID,'status':'สินค้ากำลังจัดส่ง'})

    if(resultspre):  
        for x in resultspre:           
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
                'ordertime':x['orderTime'],
                'status':x['status'],
                'total':x['total']     
                })  

        return jsonify(orderStore) 
    


#save review score 
@app.route('/api/SaveReview',methods = ['GET','POST'])
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
@app.route('/api/GetReview/<string:orderID>',methods=['GET'])
def GetReview(orderID):
    output={}
    result = db.Rateting.find({'orderID':orderID})
    for x in result:
        output={'orderID':x['orderID'] ,'img_upload':x['img_upload'], 'rate_detail':x['rate_detail'] ,'value':x['value']}
    if output :
        return output
    else :return {'status':False}



#update reviw score 
@app.route('/api/updateReview',methods=['PUT'])
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



@app.route('/api/upload', methods=['POST'])
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

@app.route('/api/getimage/<string:filename>')
def getimg(filename):
    Files='uploads/products/'+filename
    return send_file(Files,mimetype="image/jpg")


@app.route('/api/GetimageReview/<string:filename>')
def Getimg(filename):
    Files='uploads/reviews/'+filename
    return send_file(Files,mimetype="image/jpg")


@app.route('/api/sendEmail',methods=['POST'])
def SendEmail():
    email=request.json['email']
    senEmail(email)
    return {"message":"เช็ครหัสยืนยันในอีเมลของคุณ"}


@app.route('/api/gettokens/<string:storeID>',methods=['GET'])
def gettokens(storeID):
    result=db.store.find({'store_ID':storeID})
    Token=""
    for a in result:
        Token=a['token']
    if Token=="":
        return {"message":"token is Empty","status":False}
    else:
        return {"message":"gettoken ok","token":Token}



#update token for device Mobile App.
@app.route('/api/updateTokens',methods=['PUT'])
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
 

#คำร้องขออนุมัติเปิดร้านค้าทั้งหมด 
@app.route('/api/GetAllshops',methods=['GET'])
def GetAll():
    output=[]
    result = db.store.find({'status_confirm':'ยื่นคำร้อง'})
    for store in result: 
        output.append({
            'author':
                {
                    'avatar':'',
                    'name':'',
                    'email':''
                },
                'func':
                     {
                    'job': store['storename'],
                    'department': store['store_ID'],
			        },
                        'status_confirm': store['status_confirm'],
                        'employed':store['registration_date']

        })

    return jsonify(output)    



#สถาน่ะอนุมัติแล้ว
@app.route('/api/Getapproved',methods=['GET'])
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



#สถาน่ะยังไม่อนุมัติ 
@app.route('/api/Getdisapproved',methods=['GET'])
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



#อัตเดตสถาน่ะ ร้านค้าเป็นอนุอัติ และส่งแจ้งเตือนไป App mobile 
@app.route('/api/confirmStore/<string:storeID>/<string:statusShop>',methods=['PUT'])
def confirmstore(storeID,statusShop):
    if statusShop=="confirm":
        query={'store_ID':storeID}
        value={
            "$set":
                {'status_confirm':True}
        }
        update=db.store.update_one(query,value)
        if(update):
            title='แจ้งเตือนผลการลงทะเบียนร้านค้ากับ GoodVendor'
            body='ร้านของคุณได้รับการอนุมติเรียบร้อยแล้ว'
            data={'click_action':'FLUTTER_NOTIFICATION_CLICK','confirmStore':'confirm'}
            response=fcm.sendNotification(storeID,title,body,data)
            if(response==200):  
                return {"message":"updated statusconfirm success","status":True}

    if(statusShop=="disconfirm"):
        query={'store_ID':storeID}
        value={
                    "$set":
                        {'status_confirm':False}
                    }
        update=db.store.update_one(query,value)
        if(update):
                    title='แจ้งเตือนผลการลงทะเบียนร้านค้ากับ GoodVendor'
                    body='ร้านของคุณไม่ได้รับการอนุมติ เนื่องจากข้อมูลยังไม่ครบถ้วน'
                    data={'click_action':'FLUTTER_NOTIFICATION_CLICK','confirmStore':'confirm'}
                    response=fcm.sendNotification(storeID,title,body,data)
                    if(response==200):  
                        return {"message":"updated statusconfirm success","status":True}




#ดึงข้อมูลรายละเอียดร้านค้า 
@app.route('/api/shopDetail/<string:storeID>',methods=['GET'])
def getShop(storeID):
    output={}
    result = db.store.find({'store_ID':storeID})   
    for storedata in result:    
        output={     
            'userid':storedata['userid'],
            'storename':storedata['storename'], 
            'store_ID':storedata['store_ID'],
            'coordinates':storedata['coordinates'],
            'lat':storedata['lat'],
            'long':storedata['long'],
            'store_img':storedata['store_img'],
            'registration_date':storedata['registration_date']
            }                      
    return {"storeData":output}


@app.route('/api/Getorderlist/<string:orderID>',methods=['GET'])
def GetrateTing(orderID):
    output={}
    result = db.orders.find({'_id':ObjectId(orderID)})
    for pro in result:
        output={"orderList": pro['order_products'],"total":pro['total'],"userid":pro['userid'],"status":pro['status']}
    return jsonify(output)





if __name__ == '__main__':
    from werkzeug.serving import WSGIRequestHandler
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(debug=True,host="localhost",port=5000)



