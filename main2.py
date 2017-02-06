from flask import Flask, request
import json
import requests
import pymongo
import os

import time
import datetime
import pprint
import string
from pycricbuzz import Cricbuzz

app = Flask(__name__)
# connect to MongoDB with the defaults
#mongo = PyMongo(app)
client = pymongo.MongoClient(os.environ.get('MONGODB_URI'))

db = client.get_default_database()
posts = db['bet']

# Database for Admin Purpose and PSL daily matches stored there
#db = client.get_default_database()
db_colPSL = db['PSL']

# New database for per game betting
db_coluser = db['user']

admin_hassmuha = "1592912027389410"
admin_anadeem = "1056172017822417"

# This needs to be filled with the Page Access Token that will be provided
# by the Facebook App that will be created.
PAT = 'EAAIeJYNmvk0BACXjV9sUcwwNnfg0EM2y5zv2prZAH6ilxX9ouAHZBM1ZC9Hn96cUSVRCtK5fXuo1qnbZAMZC0jysfdhURw5Kq6VmB0g80AX9LpZCF7Ro0NcOXZCR4ZBCfvAsGU4aeRJD8mZBaGhBzZB00x5bbOZAluuS7IelpZAOTPbq1AZDZD'

#CRICKET APPI!
cricAPI = Cricbuzz()
cricapi_key = 'wCPnOMbHOydrHhFZWAqKcjvnWav1'
matchapiurl = 'http://cricapi.com/api/matches'


#@app.route("/")
#def hello():
#    return "Hello World!"



@app.route('/', methods=['GET'])
def handle_verification():
  print "Handling Verification."
  if request.args.get('hub.verify_token', '') == 'my_voice_is_my_password_verify_me':
    print "Verification successful!"
    return request.args.get('hub.challenge', '')
  else:
    print "Verification failed!"
    return 'Error, wrong validation token'

@app.route('/', methods=['POST'])
def handle_messages():
  print "Handling Messages"
  payload = request.get_data()
  #payload = request.data()
  print payload
  for sender, message, refID in messaging_events(payload):
    try:
        # getting associated betid if present from the message
        [message_u,betid_type,betid_assoc]=message.split(',')
    except ValueError:
        message_u = message
        betid_assoc = ""
        betid_type = '0'

    print "Incoming from %s: %s" % (sender, message_u)
    if message_u == "new_bet" and refID:
        # reffered user and using for the first time
        send_default_quickreplies(PAT, sender)
        # get user info from fb
        userinfo = get_userInfo(PAT, sender)
        first_name = ""
        last_name = ""
        locale = ""
        timezone = ""
        gender = ""
        if userinfo:
            first_name = userinfo["first_name"]
            last_name = userinfo["last_name"]
            locale = userinfo["locale"]
            timezone = userinfo["timezone"]
            gender = userinfo["gender"]
        adduser_dbcoluser(sender,first_name, last_name, locale, timezone, gender)
        #update the refferal
        addfrnd_dbcoluser(refID,sender)
    elif message_u == "new_bet" :
        # first time user
        send_default_quickreplies(PAT, sender)
        # get user info from fb
        userinfo = get_userInfo(PAT, sender)
        first_name = ""
        last_name = ""
        locale = ""
        timezone = ""
        gender = ""
        if userinfo:
            first_name = userinfo["first_name"]
            last_name = userinfo["last_name"]
            locale = userinfo["locale"]
            timezone = userinfo["timezone"]
            gender = userinfo["gender"]
        adduser_dbcoluser(sender,first_name, last_name, locale, timezone, gender)
    elif message_u == "debug db" and sender in [admin_hassmuha, admin_anadeem] :
        adduser_dbcoluser(sender,"first_name", "last_name", "locale", 1, "gender")
        addbet_dbcoluser(sender,"Karachi:Islamabad","Islamabad","2017:2:6")
        addfrnd_dbcoluser(sender,sender)
    elif message_u == "debug default buttons" and sender in [admin_hassmuha, admin_anadeem] :
        send_default_quickreplies(PAT, sender)
    elif message_u != "I can't echo this" :
#    	send_summary(PAT, sender, message)
        print "I am here"

  return "ok"
# will return sender_id,(payload in case of quick_reply, postback or text), referral id
def messaging_events(payload):
  """Generate tuples of (sender_id, message_text) from the
  provided payload.
  """
  data = json.loads(payload)
  messaging_events = data["entry"][0]["messaging"]
  for event in messaging_events:
    if "message" in event and "quick_reply" in event["message"]:
        yield event["sender"]["id"], event["message"]["quick_reply"]["payload"].encode('unicode_escape'), ""
    elif "message" in event and "text" in event["message"]:
        yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape'), ""
        # just important text in "new_bet" and "get_score"
    elif "postback" in event and "referral" in event["postback"]:
        # here when the referred user is using the messanger thread for the for the first time
        yield event["sender"]["id"], event["postback"]["payload"].encode('unicode_escape'), event["postback"]["referral"]["ref"]
    elif "referral" in event:
        # here when the referred user has already communicate the messanger
        yield event["sender"]["id"], "", event["referral"]["ref"]
    elif "postback" in event:
        yield event["sender"]["id"], event["postback"]["payload"].encode('unicode_escape'), ""
    else:
        yield event["sender"]["id"], "I can't echo this", ""

# this db is connected to db_coluser
def adduser_dbcoluser(fbID,first_name, last_name, locale, timezone, gender):
    post = posts.find_one({"fbID": fbID})
    if not post:
        post = {  "fbID": fbID,
                  "first_name" : first_name,
                  "last_name" : last_name,
                  "locale" : locale,
                  "timezone" : timezone,
                  "gender" : gender,
                  "getScoreClicks": 0,
                  "friends": [],
                  "bets":[]}
        post_id = db_coluser.insert_one(post).inserted_id
    pprint.pprint(db_coluser.find_one({"fbID": fbID}))

def addbet_dbcoluser(fbID,match,bet,date):
    post = db_coluser.find_one({"fbID": fbID,"bets.match":match,"bets.date":date})
    if not post:
        post = {
            "match":match,
            "bet":bet,
            "date":date
        }
        post = db_coluser.update_one({"fbID": fbID},{"$push": { "bets" : post}} )
    else:
        post = db_coluser.update_one({"fbID": fbID,"bets.match":match,"bets.date":date},{ "$set": { "bets.$.bet":bet }})
        #post = db_coluser.find_one({"fbID": fbID,"bets.match":match,"bets.date":date},{"bets."})
    # check what to use for replace
    pprint.pprint(db_coluser.find_one({"fbID": fbID}))

def addfrnd_dbcoluser(fbID,frnfbID):
    post = db_coluser.find_one({"fbID": fbID,"friends.fbID":frnfbID})
    if not post:
        post = {
            "fbID":frnfbID
        }
        post = db_coluser.update_one({"fbID": fbID},{"$push": { "friends" : post}} )
    # check what to use for replace
    pprint.pprint(db_coluser.find_one({"fbID": fbID}))

def send_default_quickreplies(token, recipient):
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
      params={"access_token": token},
      data=json.dumps({
        "recipient": {"id": recipient},
        "message": {
          "text":"Please Select the Options Below",
          "quick_replies":[
              {
              "content_type":"text",
              "title":"Start Betting",
              "payload":"start_bet"
              },
              {
              "content_type":"text",
              "title":"Get Score",
              "payload":"get_score"
              },
              {
              "content_type":"text",
              "title":"Challenge Friend",
              "payload":"chlg_friend"
              }
          ]
        }
      }),
      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
      print r.text

def get_userInfo(token, recipient):
    r = requests.get("https://graph.facebook.com/v2.6/%s" % (recipient),
      params={"fields":"first_name,last_name,profile_pic,locale,timezone,gender","access_token": token})
    if r.status_code != requests.codes.ok:
      print r.text
    print (r.url)
    try:
        user_data = r.json()
        print json.dumps(user_data,indent=4)
    except ValueError:
        print "No user data found"
        user_data = ""
    return user_data

if __name__ == "__main__":
    app.run()
