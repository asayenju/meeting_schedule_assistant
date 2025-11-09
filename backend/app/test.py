from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://dungh172005_db_user:Nu2g0wEpeJhfhhZA@cluster0.7mlfurz.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGODB_URI)
db = client["mydatabase"]
print(db.list_collection_names())