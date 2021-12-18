import math,random
from config.db import db


#function gennerate OTP form user 
def genotp():    
    digits = "0123456789"
    OTP = ""
    for i in range(4) :
        OTP += digits[math.floor(random.random() * 10)]    
    return OTP


#get bill number 
def genBill():    
    bill = "0123456789"
    BILL = ""
    for i in range(4) :
        BILL += bill[math.floor(random.random() * 10)]
    return BILL


#function save phonenumber and OTP 
def addNumberPhoneUser(phonenumber,otp):
    db.OTP.insert_one({'numberphone':phonenumber,'otp':otp})


