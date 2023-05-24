import pymongo
client=pymongo.MongoClient("Your MongoD link here")
db=client["database"]
coll=db["faculty_schedule"]
coll.delete_many({})
coll=db["student_schedule"]
coll.delete_many({})
coll=db["slots_list"]
coll.delete_many({})
