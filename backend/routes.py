from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok"}, 200

@app.route('/count', methods=['GET'])
def count():
    try:
        count = db.songs.count_documents({})
    except NameError:
        return {"error": "Something went wrong"}, 500
    if not count:
        return {"error": "No data available"}, 404
    return {"count": count}, 200

@app.route('/song', methods=["GET"])
def songs():
    try:
        songs = list(db.songs.find({}))
    except NameError:
        return {"error": "Something went wrong"}, 500
    if not songs:
        return {"error": "No data available"}, 404
    return {"songs": parse_json(songs)}, 200

@app.route('/song/<id>', methods=["GET"])
def get_song_by_id(id):
    try:
        song = db.songs.find_one({"id": id})
        if not song:
            return jsonify({"message": f"Song with id {id} not found"}), 404
        return parse_json(song), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Something went wrong"}), 500
    
@app.route('/song', methods=["POST"])
def create_song():
    try:
        new_song = request.json
#        db.songs.delete_one({"id": new_song['id']})        
#        song = db.songs.find_one({"id": new_song['id']})
#        if not song:
#            return {"message": f"song id {new_song['id']} not found"}
#        else:
#            return {"message": f"song id {new_song['id']} found"}
        if not new_song:
            return jsonify({"message": "Invalid data"}), 422

        if db.songs.find_one({"id": new_song["id"]}):
            return {"Message": f"song with id {new_song['id']} already present"}, 302

        inserted_id = db.songs.insert_one(new_song).inserted_id

        return jsonify({"inserted id": parse_json(inserted_id)}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Something went wrong"}), 500
