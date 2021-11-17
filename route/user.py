from flask import Flask
user=Flask()


@user.route('/user',methods=['GET'])
def Getusers():
    return {"mesage get router new ":True}

