import math,random
from config.db import db


#function gennerate OTP form user 
def genotp():    
    digits = "0123456789"
    OTP = ""
    for i in range(4) :
        OTP += digits[math.floor(random.random() * 10)]
    print(OTP)    
    return OTP

#function save phonenumber and OTP 
def addNumberPhoneUser(phonenumber,otp):
    db.OTP.insert_one({'numberphone':phonenumber,'otp':otp})


