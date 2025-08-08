from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client['ticketing_system']
db.tickets.drop()
db.comments.drop()
print('Database collections dropped successfully')