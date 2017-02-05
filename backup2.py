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
  for sender, message, betid in messaging_events(payload):
    try:
        # getting associated betid if present from the message
        [message_u,betid_type,betid_assoc]=message.split(',')
    except ValueError:
        message_u = message
        betid_assoc = ""
        betid_type = '0'

    print "Incoming from %s: %s" % (sender, message_u)
    # modifid by Hassan : to fix the echo problem. the problem is message echo option is on by default and whenever page send a message to user one more status message follows
    if message_u == "new_bet" and betid:
        # reffered user and using for the first time
        print "reffered user and using for the first time"
        send_team(PAT, sender, message_u, betid)
        adduser_database(sender) # add new user to the db
    elif betid:
        # reffered user but already communicated with the bot
        print "reffered user but already communicated with the bot"
        send_team(PAT, sender, message_u, betid)
        adduser_database(sender) # add new user to the db
    elif message_u == "new_bet" :
        send_team(PAT, sender, message_u, "")
        adduser_database(sender) # add new user to the db
    elif message_u in ["Karachi", "Lahore", "Quetta", "Peshawar","Islamabad"]:
        send_summary(PAT, sender, message_u, betid_assoc, betid_type)
        print message_u
    elif message_u == "get_score" :
        getmatches(PAT,sender,message)
    elif message_u[:3] == "GS_" :
        send_scoreupdate(PAT,sender,message)
    elif message_u == "start bet" and sender in [admin_hassmuha, admin_anadeem] :
        send_dailybet(PAT)
    elif message_u != "I can't echo this" :
#    	send_summary(PAT, sender, message)
        print "I am here"

  return "ok"

def messaging_events(payload):
  """Generate tuples of (sender_id, message_text) from the
  provided payload.
  """
  data = json.loads(payload)
  messaging_events = data["entry"][0]["messaging"]
  for event in messaging_events:
    if "message" in event and "quick_reply" in event["message"]:
        yield event["sender"]["id"], event["message"]["quick_reply"]["payload"].encode('unicode_escape'), ""
        # refferal want to share with others
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

#  for event in messaging_events:
#    if "message" in event and "text" in event["message"]:
#      yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape')
#    else:
#      yield event["sender"]["id"], "I can't echo this"

# this will either create a document/or append the user to the already exiting document
def adduser_database(fbID):
    post = posts.find_one({"noUsers": { "$gt": 0 }})
    if post:
        if fbID not in post["users"]:
            result = posts.update_one({"noUsers": { "$gt": 0 }},{'$inc': {'noUsers': 1}},{"$push": { "users" : [fbID]}} , {'upsert':False})
            print "matched no of users document %i" % result.matched_count
            print "modified no of users document %i" % result.modified_count
    else:
        post = {  "noUsers": 1,
                  "users": [fbID]}
        post_id = posts.insert_one(post).inserted_id
        #pprint.pprint(posts.find_one({"fbID": fbID}))
        pprint.pprint(posts.find_one({"betid": betid}))

# this will add a new document for the bet in database
def addbet_database(fbID, first_name, last_name, locale, timezone, gender, bet, betid):
  post = {  "fbID": fbID,
            "first_name" : first_name,
            "last_name" : last_name,
            "locale" : locale,
            "timezone" : timezone,
            "gender" : gender,
            "decision": bet,
            "betid": betid,
            "Participant": [(fbID,bet)]}
  post_id = posts.insert_one(post).inserted_id
  #pprint.pprint(posts.find_one({"fbID": fbID}))
  pprint.pprint(posts.find_one({"betid": betid}))

def appendbet_database(fbID, bet, betid):
  # this is for the add entry to old bet
  print betid
  pprint.pprint(posts.find_one({"betid": betid}))

  post = posts.update({"betid": betid},{"$push": { "Participant" : [fbID,bet]}} )

  pprint.pprint(posts.find_one({"betid": betid}))

# dummy function to create the documents in PSL collection
def createPSL_database():
    #"2017:2:5"
    for i in range(9,29):
        post = {  "date": "2017:2:%i"%i,
                  "matches": []}
        # example "matches": [(KK:QG,KK)]
        post_id = db_colPSL.insert_one(post).inserted_id
        print i
    for i in range(1,8):
        post = {  "date": "2017:3:%i"%i,
                  "matches": []}
        post_id = db_colPSL.insert_one(post).inserted_id
        print i

def queryAlluser_database():
    usersfbId = []
    posts.find()

def send_team(token, recipient, text, betid):
  """Send the message text to recipient with id recipient.
  """
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

  #r = requests.post("https://graph.facebook.com/v2.6/me/messages",
    #params={"access_token": token},
    #data=json.dumps({
    #  "recipient": {"id": recipient},
    #  "message": {"text": text.decode('unicode_escape')}
    #}),
    #headers={'Content-type': 'application/json'})
  if betid:
      # also include betid with payload
      KK_payload = "Karachi,1,%s" % (betid)
      IU_paload = "Islamabad,1,%s" % (betid)
      LQ_payload = "Lahore,1,%s" % (betid)
      QG_payload = "Quetta,1,%s" % (betid)
      PZ_payload = "Peshawar,1,%s" % (betid)
  else:
      KK_payload = "Karachi,0,"
      IU_paload = "Islamabad,0,"
      LQ_payload = "Lahore,0,"
      QG_payload = "Quetta,0,"
      PZ_payload = "Peshawar,0,"
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
                                "payload":KK_payload
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
                                "payload":IU_paload
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
                                "payload":LQ_payload
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
                                "payload":QG_payload
                            }
                        ]
                    },
                    {
                        "title":"Peshawar Zalmi",
                        "subtitle":"Peshawar Zalmi will win PSL 2017!",
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
                                "payload":PZ_payload
                            }
                        ]
                    }
                ]
                }
            }
        }

    }),
    headers={'Content-type': 'application/json'})

def send_summary(token, recipient, text, betid_assoc, betid_type):
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
  if betid_type == '2':
      # for a reffered user who initiated another bet by sharing with his friends
      murl = 'http://m.me/NostalMine?ref={0}'.format(betid_assoc)
  else:
      murl = 'http://m.me/NostalMine?ref={0}'.format(betid)
  print betid

  if betid_assoc and betid_type == '1':
      first_name_orig = ""
      last_name_orig = ""
      first_name = ""
      last_name = ""
      # requesting users info
      origfbID = posts.find_one({"betid": betid_assoc})["fbID"]
      r_orig = requests.get("https://graph.facebook.com/v2.6/%s" % (origfbID),
        params={"fields":"first_name,last_name","access_token": token})
      if r_orig.status_code != requests.codes.ok:
        print r_orig.text
      try:
          user_data = r_orig.json()
          print json.dumps(user_data,indent=4)
      except ValueError:
          print "No user data found"
          user_data = ""
      if user_data:
          first_name_orig = user_data["first_name"]
          last_name_orig = user_data["last_name"]

      # current user fb info
      r = requests.get("https://graph.facebook.com/v2.6/%s" % (recipient),
        params={"fields":"first_name,last_name","access_token": token})
      if r.status_code != requests.codes.ok:
        print r.text
      try:
          user_data = r.json()
          print json.dumps(user_data,indent=4)
      except ValueError:
          print "No user data found"
          user_data = ""
      if user_data:
          first_name = user_data["first_name"]
          last_name = user_data["last_name"]

      r = requests.post("https://graph.facebook.com/v2.6/me/messages",
        params={"access_token": token},
        data=json.dumps({
          "recipient": {"id": origfbID},
          "message": {
            "text":"%s, your friend %s %s has accepted the challenge and he is betting for %s"%(first_name_orig,first_name,last_name,FullName)
          }
        }),
        headers={'Content-type': 'application/json'})
      if r.status_code != requests.codes.ok:
        print r.text

      new_betid = "%s,2,%s" % (text, betid)
      r = requests.post("https://graph.facebook.com/v2.6/me/messages",
        params={"access_token": token},
        data=json.dumps({
          "recipient": {"id": recipient},
          "message": {
            "text":"You have selected %s. Your friend %s %s has been notified."%(FullName,first_name_orig, last_name_orig),
            "quick_replies":[
                {
                "content_type":"text",
                "title":"Summarize and Share",
                "payload":new_betid
                }
            ]
          }
        }),
        headers={'Content-type': 'application/json'})
      if r.status_code != requests.codes.ok:
        print r.text

      appendbet_database(recipient, text, betid_assoc)
  elif betid_assoc and betid_type == '2':
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

      # requesting user info
      r = requests.get("https://graph.facebook.com/v2.6/%s" % (recipient),
        params={"fields":"first_name,last_name,profile_pic,locale,timezone,gender","access_token": token})
      if r.status_code != requests.codes.ok:
        print r.text
      try:
          user_data = r.json()
          print json.dumps(user_data,indent=4)
      except ValueError:
          print "No user data found"
          user_data = ""
      if user_data:
          first_name = user_data["first_name"]
          last_name = user_data["last_name"]
          locale = user_data["locale"]
          timezone = user_data["timezone"]
          gender = user_data["gender"]
      addbet_database(recipient, first_name, last_name, locale, timezone, gender, text, betid_assoc)
      #addbet_database(recipient, text, betid_assoc)
  else:
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

      # requesting user info
      r = requests.get("https://graph.facebook.com/v2.6/%s" % (recipient),
        params={"fields":"first_name,last_name,profile_pic,locale,timezone,gender","access_token": token})
      if r.status_code != requests.codes.ok:
        print r.text
      try:
          user_data = r.json()
          print json.dumps(user_data,indent=4)
      except ValueError:
          print "No user data found"
          user_data = ""
      if user_data:
          first_name = user_data["first_name"]
          last_name = user_data["last_name"]
          locale = user_data["locale"]
          timezone = user_data["timezone"]
          gender = user_data["gender"]
      addbet_database(recipient, first_name, last_name, locale, timezone, gender, text, betid)
      #addbet_database(recipient, text, betid)
##Cricket API
def send_dailybet(token):
    # getuser_database() # might result a list and then iterate over to get all updates
    # currently I am creating documents in the database with all the dates
    # createPSL_database()
    print token

def getmatches(token, recipient, text):
    matches = cricAPI.matches()
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
    data2= cricAPI.livescore(matchid)
    matchinfo = data2["matchinfo"]
    if(matchinfo["type"] == "ODI" or matchinfo["type"] == "T20"):
        cscore = Oneday(data2)
        print cscore
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
        params={"access_token": token},
        data=json.dumps({
            "recipient": {"id": recipient},
            "message": {
                "text":cscore
            }
          }),
          headers={'Content-type': 'application/json'})
    #print cscore

def Oneday(data2):
    batsmen= len(data2["batting"]["batsman"])
    bowlers= len(data2["bowling"]["bowler"])
    matchinfo1 = data2["matchinfo"]
    status = "Status : %s\n" &(matchinfo1["status"])
    if "runs" in data2["bowling"]["score"][0] :
        batteam = "%s %s/%s Overs:%s" %(data2["batting"]["team"],data2["batting"]["score"][0]["runs"],data2["batting"]["score"][0]["wickets"],data2["batting"]["score"][0]["overs"])
        bowlteam = "\n%s %s/%s Overs:%s" %(data2["bowling"]["team"],data2["bowling"]["score"][0]["runs"],data2["bowling"]["score"][0]["wickets"],data2["bowling"]["score"][0]["overs"])
        if(batsmen == 2):
            batsmeninfo = "\n\t%-20s %-4s %-4s %-4s %-4s \n\t%-20s %-4s %-4s %-4s %-4s" %(data2["batting"]["batsman"][0]["name"],
            data2["batting"]["batsman"][0]["runs"],data2["batting"]["batsman"][0]["balls"],data2["batting"]["batsman"][0]["fours"],data2["batting"]["batsman"][0]["six"],
            data2["batting"]["batsman"][1]["name"],data2["batting"]["batsman"][1]["runs"],data2["batting"]["batsman"][1]["balls"],data2["batting"]["batsman"][1]["fours"],data2["batting"]["batsman"][1]["six"])
        elif(batsmen == 1):
            batsmeninfo = "\n\t%-20s %-4s %-4s %-4s %-4s" %(data2["batting"]["batsman"][0]["name"],
            data2["batting"]["batsman"][0]["runs"],data2["batting"]["batsman"][0]["balls"],data2["batting"]["batsman"][0]["fours"],data2["batting"]["batsman"][0]["six"])
        else:
            batsmeninfo = ""
        if(bowlers == 2):
            bowlerinfo = "\n\t%-20s %-4s %-4s %-4s %-4s \n\t%-20s %-4s %-4s %-4s %-4s" %(data2["bowling"]["bowler"][0]["name"],
            data2["bowling"]["bowler"][0]["overs"],data2["bowling"]["bowler"][0]["runs"],data2["bowling"]["bowler"][0]["maidens"],data2["bowling"]["bowler"][0]["wickets"],
            data2["bowling"]["bowler"][1]["name"],data2["bowling"]["bowler"][1]["overs"],data2["bowling"]["bowler"][1]["runs"],data2["bowling"]["bowler"][1]["maidens"],data2["bowling"]["bowler"][1]["wickets"])
        if(bowlers == 1):
            bowlerinfo = "\n\t%-20s %-4s %-4s %-4s %-4s " %(data2["bowling"]["bowler"][0]["name"],
            data2["bowling"]["bowler"][0]["overs"],data2["bowling"]["bowler"][0]["runs"],data2["bowling"]["bowler"][0]["maidens"],data2["bowling"]["bowler"][0]["wickets"])
        else:
            if(bowlers == 1):
                bowlerinfo = ""
        #print batteam
        #print batsmeninfo
        #print bowlteam
        #print bowlerinfo
        cscore = status + batteam + batsmeninfo + bowlteam + bowlerinfo
        return cscore
    else:
        batteam = "%s %s/%s Overs:%s" %(data2["batting"]["team"],data2["batting"]["score"][0]["runs"],data2["batting"]["score"][0]["wickets"],data2["batting"]["score"][0]["overs"])
        bowlteam = "\n%s" %(data2["bowling"]["team"])
        if(batsmen == 2):
            batsmeninfo = "\n\t%-20s %-4s %-4s %-4s %-4s \n\t%-20s %-4s %-4s %-4s %-4s" %(data2["batting"]["batsman"][0]["name"],
            data2["batting"]["batsman"][0]["runs"],data2["batting"]["batsman"][0]["balls"],data2["batting"]["batsman"][0]["fours"],data2["batting"]["batsman"][0]["six"],
            data2["batting"]["batsman"][1]["name"],data2["batting"]["batsman"][1]["runs"],data2["batting"]["batsman"][1]["balls"],data2["batting"]["batsman"][1]["fours"],data2["batting"]["batsman"][1]["six"])
        elif(batsmen == 1):
            batsmeninfo = "\n\t%-20s %-4s %-4s %-4s %-4s" %(data2["batting"]["batsman"][0]["name"],
            data2["batting"]["batsman"][0]["runs"],data2["batting"]["batsman"][0]["balls"],data2["batting"]["batsman"][0]["fours"],data2["batting"]["batsman"][0]["six"])
        else:
            batsmeninfo = ""
        if(bowlers == 2):
            bowlerinfo = "\n\t%-20s %-4s %-4s %-4s %-4s \n\t%-20s %-4s %-4s %-4s %-4s" %(data2["bowling"]["bowler"][0]["name"],
            data2["bowling"]["bowler"][0]["overs"],data2["bowling"]["bowler"][0]["runs"],data2["bowling"]["bowler"][0]["maidens"],data2["bowling"]["bowler"][0]["wickets"],
            data2["bowling"]["bowler"][1]["name"],data2["bowling"]["bowler"][1]["overs"],data2["bowling"]["bowler"][1]["runs"],data2["bowling"]["bowler"][1]["maidens"],data2["bowling"]["bowler"][1]["wickets"])
        if(bowlers == 1):
            bowlerinfo = "\n\t%-20s %-4s %-4s %-4s %-4s " %(data2["bowling"]["bowler"][0]["name"],
            data2["bowling"]["bowler"][0]["overs"],data2["bowling"]["bowler"][0]["runs"],data2["bowling"]["bowler"][0]["maidens"],data2["bowling"]["bowler"][0]["wickets"])
        else:
            if(bowlers == 1):
                bowlerinfo = ""
        #print batteam
        #print batsmeninfo
        #print bowlteam
        #print bowlerinfo
        cscore = status + batteam + batsmeninfo + bowlteam + bowlerinfo
        return cscore


if __name__ == "__main__":
    app.run()
