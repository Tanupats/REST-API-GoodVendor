from pymongo import MongoClient
import certifi
client = MongoClient("mongodb+srv://music2021:music0983460756@cluster0.wjhzl.mongodb.net/myFirstDatabase?retryWrites=true&w=majority",tlsCAFile=certifi.where())
#client = MongoClient()#for connect to localhost MongoDB 
db=client["GoodVendor"]#select Database Name is GoodVendor
print("Connect DB success",client.list_database_names())

