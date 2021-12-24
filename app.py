from typing_extensions import Required
from flask import Flask, json, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb+srv://restbarao1:Q4wh7PKcJH4y1VcF@clusteradalto.3bnro.mongodb.net/adalto?retryWrites=true&w=majority")
db = client.SimilarityDB
users = db["users"]



def UserExist(username):
    if users.count_documents({"username":username}) > 0:
        return True
    else:
        return False

def verifyPw(username,password):
    if not UserExist(username):
        return False
    hashed_pw = users.find({
        "username":username
    })[0]["password"]

    if bcrypt.hashpw(password.encode('utf8'),hashed_pw)==hashed_pw:
        return True
    else:
        return False


def countTokens(username):
    return users.find({
        "username":username
    })[0]["tokens"]

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJson = {
                "status":301,
                "msg":"Invalid username"
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'),bcrypt.gensalt())

        users.insert_one({
            "username":username,
            "password":hashed_pw,
            "tokens":6
        })

        retJson = {
            "status":200,
            "msg":"You've successfully signed up to the API"
        }
        return jsonify(retJson)

class Detect(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        if not UserExist(username):
            retJson = {
                "status":301,
                "msg":"Invalid username"
            }
            return jsonify(retJson)

        if not verifyPw(username,password):
            retJson = {
                "status":302,
                "msg":"Invalid password"
            }
            return jsonify(retJson)
        
        num_tokens = countTokens(username)

        if num_tokens <=0:
            retJson = {
                "status":303,
                "msg":"Out of tokens"
            }
            return jsonify(retJson)
    
        nlp = spacy.load("pt_core_news_sm")

        tex1 = nlp(text1)
        tex2 = nlp(text2)

        ratio = tex1.similarity(tex2)

        retJson = {
            "status":200,
            "similarity":ratio,
            "msg":"Similarity score calculated successfully"
        }

        users.update_one({
            "username":username
        },{"$set":{
            "tokens":countTokens(username)-1
        }})
        return jsonify(retJson)

class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["admin_pw"]
        refill = postedData["refill"]

        correct_pw = "abc123"

        if not password==correct_pw:
            retJson = {
                "status":304,
                "msg":"Invalid admin password"
            }
            return jsonify(retJson)

        if not UserExist(username):
            retJson = {
                "status":301,
                "msg":"Invalid username"
            }
            return jsonify(retJson)
       
        users.update_one({
            "username":username
        },{
            "$set":{
                "tokens":refill
            }
        })

        retJson = {
            "status":200,
            "msg":"Refilled successfully"
        }
        return jsonify(retJson)
        
api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')


if __name__=="__main__":
    app.run(host='0.0.0.0')

        
