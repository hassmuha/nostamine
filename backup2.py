from flask import Flask, request
from pycricbuzz import Cricbuzz
import json
import requests
import pymongo
import os

import time
import datetime
import pprint
import string

app = Flask(__name__)
# connect to MongoDB with the defaults
#mongo = PyMongo(app)
client = pymongo.MongoClient(os.environ.get('MONGODB_URI'))
db = client.get_default_database()
posts = db['bet']

# This needs to be filled with the Page Access Token that will be provided
# by the Facebook App that will be created.
PAT = 'EAAIeJYNmvk0BACXjV9sUcwwNnfg0EM2y5zv2prZAH6ilxX9ouAHZBM1ZC9Hn96cUSVRCtK5fXuo1qnbZAMZC0jysfdhURw5Kq6VmB0g80AX9LpZCF7Ro0NcOXZCR4ZBCfvAsGU4aeRJD8mZBaGhBzZB00x5bbOZAluuS7IelpZAOTPbq1AZDZD'

#CRICKET APPI!
c = Cricbuzz()
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
  for sender, message in messaging_events(payload):
    print "Incoming from %s: %s" % (sender, message)
    # modifid by Hassan : to fix the echo problem. the problem is message echo option is on by default and whenever page send a message to user one more status message follows
    if message == "get_score" :
        getmatches(PAT,sender,message)
    elif message[:3] == "GS_":
        send_scoreupdate(PAT,sender,message)
    elif message == "new_bet" :
        team_select(PAT, sender, message)
    elif message in ["Karachi", "Lahore", "Quetta", "Peshawer","Islamabad"]:
        send_message(PAT, sender, message)
        print message
    elif message != "I can't echo this" :
#    	send_message(PAT, sender, message)
        print "I am here"

  return "ok"


##Cricket API

def getmatches(token, recipient, text):
    matches = c.matches()
    data = []
    for match in matches:
        data.append({"content_type":"text", "title":match['mchdesc'], "payload":"GS_%s"%(match['id'])})
    quickreplies(token,recipient,data)


def quickreplies(token,recipient,json_string):
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
          params={"access_token": token},
          data=json.dumps({
           "recipient": {"id": recipient},
           "message":{
              "text":"Todays Matches:",
              "quick_replies": json_string
            }
          }),
          headers={'Content-type': 'application/json'})

def send_scoreupdate(token, recipient, text):
    matchid = text[3:]
    data1= c.scorecard(matchid)
    matchinfo = data1["matchinfo"]
    scorecard = data1["scorecard"]
    innings= len(scorecard)
    if innings == 1:
        print "%s" %(matchinfo["status"])
        cscore = "%s %s/%s Overs:%s vs \n%s" %(data1["scorecard"][0]["batteam"],
        data1["scorecard"][0]["runs"],data1["scorecard"][0]["wickets"],data1["scorecard"][0]["overs"],
        data1["scorecard"][0]["bowlteam"])
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
          params={"access_token": token},
          data=json.dumps({
            "recipient": {"id": recipient},
            "message": {
                "text":cscore
            }
          }),
          headers={'Content-type': 'application/json'})
        print cscore
    if innings == 2:
        print "%s" %(matchinfo["status"])
        cscore = "%s %s/%s Overs:%s vs \n%s %s/%s Overs:%s" % (data1["scorecard"][0]["batteam"],
        data1["scorecard"][0]["runs"],data1["scorecard"][0]["wickets"],data1["scorecard"][0]["overs"],
        data1["scorecard"][0]["bowlteam"],data1["scorecard"][1]["runs"],data1["scorecard"][1]["wickets"],data1["scorecard"][1]["overs"])
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
          params={"access_token": token},
          data=json.dumps({
            "recipient": {"id": recipient},
            "message": {
                "text":cscore
            }
          }),
          headers={'Content-type': 'application/json'})
        print cscore

def messaging_events(payload):
  """Generate tuples of (sender_id, message_text) from the
  provided payload.
  """
  data = json.loads(payload)
  messaging_events = data["entry"][0]["messaging"]
  for event in messaging_events:
    if "message" in event and "quick_reply" in event["message"]:
        yield event["sender"]["id"], event["message"]["quick_reply"]["payload"].encode('unicode_escape')
    elif "message" in event and "text" in event["message"]:
        yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape')
    elif "postback" in event:
        print "debug 0"
        print event
        yield event["sender"]["id"], event["postback"]["payload"].encode('unicode_escape')
    else:
        yield event["sender"]["id"], "I can't echo this"

#  for event in messaging_events:
#    if "message" in event and "text" in event["message"]:
#      yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape')
#    else:
#      yield event["sender"]["id"], "I can't echo this"

# this will add a new document for the bet in database
def addbet_database(fbID, bet, betid):
  post = {  "fbID": fbID,
            "decision": bet,
            "betid": betid,
            "Participant": [(fbID,bet)]}
  post_id = posts.insert_one(post).inserted_id
  #pprint.pprint(posts.find_one({"fbID": fbID}))
  for cursor in posts.find({"fbID": fbID}):
      print cursor
  print post_id

def team_select(token, recipient, text):
  """Send the message text to recipient with id recipient.
  """

  #r = requests.post("https://graph.facebook.com/v2.6/me/messages",
    #params={"access_token": token},
    #data=json.dumps({
    #  "recipient": {"id": recipient},
    #  "message": {"text": text.decode('unicode_escape')}
    #}),
    #headers={'Content-type': 'application/json'})

  r = requests.post("https://graph.facebook.com/v2.6/me/messages",
    params={"access_token": token},
    data=json.dumps({
      "recipient": {"id": recipient},
      "message": {
        "attachment":{
            "type":"template",
            "payload":{
                "template_type":"generic",
                "elements":[
                    {
                        "title":"Karachi Kings",
                        "subtitle":"Karachi Kings will win PSL 2017!",
                        "image_url":"https://pslt20.blob.core.windows.net/team/1453111172542-team.png",
                        "buttons":[
                            {
                                "type":"web_url",
                                "url":"http://match.psl-t20.com/teams/karachi-kings",
                                "title":"View Team"
                            },
                            {
                                "type":"postback",
                                "title":"Select Team",
                                "payload":"Karachi"
                            }
                        ]
                    },
                    {
                        "title":"Islamabad United",
                        "subtitle":"Islamabad United will win PSL 2017!",
                        "image_url":"https://pslt20.blob.core.windows.net/team/1453111086101-team.png",
                        "buttons":[
                            {
                                "type":"web_url",
                                "url":"http://match.psl-t20.com/teams/islamabad-united",
                                "title":"View Team"
                            },
                            {
                                "type":"postback",
                                "title":"Select Team",
                                "payload":"Islambad"
                            }
                        ]
                    },
                    {
                        "title":"Lahore Qalandars",
                        "subtitle":"Lahore Qalandars will win PSL 2017!",
                        "image_url":"https://pslt20.blob.core.windows.net/team/1453111135284-team.png",
                        "buttons":[
                            {
                                "type":"web_url",
                                "url":"http://match.psl-t20.com/teams/lahore-qalandars",
                                "title":"View Team"
                            },
                            {
                                "type":"postback",
                                "title":"Select Team",
                                "payload":"Lahore"
                            }
                        ]
                    },
                    {
                        "title":"Quetta Gladiators",
                        "subtitle":"Quetta Gladiators will win PSL 2017!",
                        "image_url":"https://pslt20.blob.core.windows.net/team/1453111043838-team.png",
                        "buttons":[
                            {
                                "type":"web_url",
                                "url":"http://match.psl-t20.com/teams/quetta-gladiators",
                                "title":"View Team"
                            },
                            {
                                "type":"postback",
                                "title":"Select Team",
                                "payload":"Quetta"
                            }
                        ]
                    },
                    {
                        "title":"Peshawer Zalmi",
                        "subtitle":"Peshawer Zalmi will win PSL 2017!",
                        "image_url":"https://pslt20.blob.core.windows.net/team/1453111156446-team.png",
                        "buttons":[
                            {
                                "type":"web_url",
                                "url":"http://match.psl-t20.com/teams/peshawar-zalmi",
                                "title":"View Team"
                            },
                            {
                                "type":"postback",
                                "title":"Select Team",
                                "payload":"Peshawer"
                            }
                        ]
                    }
                ]
                }
            }
        }

    }),
    headers={'Content-type': 'application/json'})

def send_message(token, recipient, text):
  """Send the message text to recipient with id recipient.
  """

  #r = requests.post("https://graph.facebook.com/v2.6/me/messages",
    #params={"access_token": token},
    #data=json.dumps({
    #  "recipient": {"id": recipient},
    #  "message": {"text": text.decode('unicode_escape')}
    #}),
    #headers={'Content-type': 'application/json'})
  if text == "Karachi":
      url = "https://pslt20.blob.core.windows.net/team/1453111172542-team.png"
      FullName = "Karachi King"
  elif text == "Islamabad":
      url = "https://pslt20.blob.core.windows.net/team/1453111086101-team.png"
      FullName = "Islamabad United"
  elif text == "Lahore":
      url = "https://pslt20.blob.core.windows.net/team/1453111135284-team.png"
      FullName = "Lahore Gladiators"
  elif text == "Quetta":
      url = "https://pslt20.blob.core.windows.net/team/1453111043838-team.png"
      FullName = "Quetta Gladiators"
  else:
      url = "https://pslt20.blob.core.windows.net/team/1453111156446-team.png"
      FullName = "Peshawar Zalmi"
  betid = '{0}{1}'.format(recipient, '{:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now()))
  murl = 'http://m.me/NostalMine?ref={0}'.format(betid)
  print betid

  r = requests.post("https://graph.facebook.com/v2.6/me/messages",
    params={"access_token": token},
    data=json.dumps({
      "recipient": {"id": recipient},
      "message": {
        "attachment":{
            "type":"template",
            "payload":{
                "template_type":"generic",
                "elements":[
                    {
                        "title":"Bet Summary",
                        "subtitle":"I have selected %s. Best of Luck"%(FullName),
                        "image_url":url,
                        "buttons":[
                            {
                                "type":"element_share"
                            },
                            {
                                "type":"web_url",
                                "url":murl,
                                "title":"Challenge accepted"
                            },
                            {
                                "type":"postback",
                                "title":"Challenge accepted",
                                "payload":betid
                            }
                        ]
                    }
                ]
            }
        }
      }
    }),
    headers={'Content-type': 'application/json'})


  if r.status_code != requests.codes.ok:
    print r.text
  addbet_database(recipient, text, betid)


if __name__ == "__main__":
    app.run()
