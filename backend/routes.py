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
    """
    route method for health check
    """
    return {"status": "ok"}, 200

@app.route('/count', methods=['GET'])
def count():
    """
    route method to get the number of documents
    """
    try:
        count = db.songs.count_documents({})
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": "Something went wrong"}, 500
    if not count:
        return {"error": "No data available"}, 404
    return {"count": count}, 200

@app.route('/song', methods=["GET"])
def songs():
    """
    route method for getting a list of documents
    """
    try:
        # retrieving all the documents and saving as a list
        songs = list(db.songs.find({}))
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": "Something went wrong"}, 500
    if not songs:
        # if nothing was returned from find, status code 404 sent
        return {"error": "No data available"}, 404
    # parse_json is used since songs is non-serializable
    return {"songs": parse_json(songs)}, 200

@app.route('/song/<int:id>', methods=["GET"])
def get_song_by_id(id):
    """
    route method for retrieving a document by id 
    variable passed in request
    """
    try:
        # searching for a specific document by the id key
        song = db.songs.find_one({"id": id})
        # if nothing was returned, send status code 404
        if not song:
            return jsonify({"message": f"Song with id {id} not found"}), 404
        # parse_json used since song is non-serializable
        return parse_json(song), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Something went wrong"}), 500
    
@app.route('/song', methods=["POST"])
def create_song():
    """
    route method for the POST request 
    """
    try:
        # retrieving the json data sent in the request
        new_song = request.json
        
        # if nothing was returned status code 422 sent in response
        if not new_song:
            return jsonify({"message": "Invalid data"}), 422

        # checks if a document with the id of the data sent already
        # exists and if so, sends a status code 302 in response
        if db.songs.find_one({"id": new_song["id"]}):
            return {"Message": f"song with id {new_song['id']} already present"}, 302
        # retrieving the mongodb inserted id
        inserted_id = db.songs.insert_one(new_song).inserted_id
        # sending inserted_id back in response with status code 200
        return jsonify({"inserted id": parse_json(inserted_id)}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    """
    route method to update a document with passed in id
    """
    try:
        # retrieving json data from request
        song_update = request.json
        # searching to see if document with id exists
        song = db.songs.find_one({"id": id})
        if song is None:
            return jsonify({"message": "song not found"}), 404
        # creating a changes object using json from request
        changes = {"$set": song_update}
        # updating the document matching passed id with the changes object
        is_updated = db.songs.update_one({"id": id}, changes)
        # verifying that the update was actually done and returning message
        # if update was not made
        if is_updated.modified_count == 0:
            return jsonify({"message": "song found, but nothing updated"}), 200
        return parse_json(db.songs.find_one({"id": id})), 201
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    """
    route method for deleting a document by id
    """
    try:
        # tries to delete document
        is_deleted = db.songs.delete_one({"id": id})
        # checking if the result from the delete happend
        if is_deleted.deleted_count == 0:
            return jsonify({"message": "song not found"}), 404
        return {},204
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Something went wrong"}), 500