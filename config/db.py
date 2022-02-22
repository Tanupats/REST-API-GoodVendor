from pymongo import MongoClient
import certifi
client = MongoClient("mongodb+srv://music2021:music0983460756@cluster0.wjhzl.mongodb.net/myFirstDatabase?retryWrites=true&w=majority",tlsCAFile=certifi.where())
db=client["GoodVendor"]
users=db.Users
print("Connect DB success",client.list_database_names())

