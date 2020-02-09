from flask import Flask, request
import json
import requests
import pymongo
import os

import time
import datetime
import pprint
import string
import threading


from pycricbuzz import Cricbuzz

from bs4 import BeautifulSoup
import re

app = Flask(__name__)
# connect to MongoDB with the defaults
#mongo = PyMongo(app)
#blabla
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
team_map = {"KK":"Karachi King","IU":"Islamabad United","PZ":"Peshawar Zalmi","QG":"Quetta Gladiators","LQ":"Lahore Qalandars"}


match_status = [{"match":"XX","matchid":"","lastupdate":0,"status":""},{"match":"XX","matchid":"","lastupdate":0,"status":""}]
#date format 2017:2:5
#@app.route("/")
#def hello():
#    return "Hello World!"
REFRESHTIME = 1


@app.route('/', methods=['GET'])
def handle_verification():
  print "Handling Verification."
  if request.args.get('hub.verify_token', '') == 'my_voice_is_my_password_verify_me':
    print "Verification successful!"
    return request.args.get('hub.challenge', '')
  else:
    print "Verification failed!"
    return 'You can find our privacy-policy here http://www.iubenda.com/privacy-policy/8026149'

@app.route('/', methods=['POST'])
def handle_messages():
  global match_status
  match_status_l = match_status
  print "Handling Messages"
  payload = request.get_data()
  #payload = request.data()
  print payload
  for sender, message, refID in messaging_events(payload):
    betID_found = 0
    try:
        # getting associated betid if present from the message
        #2017:02:06,KK:QG,0,KK,1592912027389410
        [msg_date,msg_match,msg_matchidx,msg_bet,msg_fbid]=message.split(',')
        message_u = message
        betID_found = 1
    except ValueError:
        message_u = message

    print "Incoming from %s: %s" % (sender, message_u)
    if message_u == "new_bet" and refID:
        # reffered user and using for the first time
        send_default_quickreplies(PAT, sender)
        # get user info from fb
        (first_name,last_name,locale,timezone,gender) = get_userInfo(PAT, sender)
        adduser_dbcoluser(sender,first_name, last_name, locale, timezone, gender)
        #update the refferal
        addfrnd_dbcoluser(refID,sender)
        # send refID that sender has accept the message
        temp_msg = "Your Friend %s %s has accepted your challenge" % (first_name,last_name)
        send_text(PAT, refID, temp_msg)
        send_default_quickreplies(PAT, refID)
    elif message_u == "new_bet" :
        # first time user
        send_default_quickreplies(PAT, sender)
        # get user info from fb
        (first_name,last_name,locale,timezone,gender) = get_userInfo(PAT, sender)
        adduser_dbcoluser(sender,first_name, last_name, locale, timezone, gender)
    elif refID:
        # already existing user reffered again
        send_default_quickreplies(PAT, sender)

        # get user info from fb
        (first_name,last_name,locale,timezone,gender) = get_userInfo(PAT, sender)
        #update the refferal
        addfrnd_dbcoluser(refID,sender)
        # send initiator a msg
        temp_msg = "Your Friend %s %s has accepted your challenge" % (first_name,last_name)
        send_text(PAT, refID, temp_msg)
        send_default_quickreplies(PAT, refID)
    elif message_u == "get_score" :
        print "get score here"
        # counter increment by 1 each time user click
        incgetScoreClicks_dbcoluser(sender)
        # display all matches
        send_currentmatch(PAT, sender)
    elif "GS_" in message_u:
        [key,matchids,status]=message_u.split('_')
        matchidx = int(matchids)
        #get_livescore(matchid)
        if status == "preview":
            matchsts = match_status_l[matchidx]["status"]
            send_text(PAT, sender, matchsts)
        elif status == "complete":
            matchsts = match_status_l[matchidx]["status"]
            send_text(PAT, sender, matchsts)
        else:
            dt = datetime.datetime.now()
            currenttime = dt.hour * 60 + dt.minute
            if currenttime > match_status_l[matchidx]["lastupdate"] + REFRESHTIME:
                matchsts = get_livescore(match_status_l[matchidx]["matchid"])
                match = match_status_l[matchidx]["match"]
                matchid = match_status_l[matchidx]["matchid"]
                update_matchstatus(matchidx,match,matchid,currenttime,matchsts)
            else:
                matchsts = match_status_l[matchidx]["status"]
            send_text(PAT, sender, matchsts)
        send_default_quickreplies(PAT, sender)
        # send score
    elif message_u == "chlg_friend" :
        # anytime when user want to share result
        send_summary_share(PAT, sender)
    elif message_u == "start_bet" :
        dt = datetime.datetime.now()
        date = '{0}'.format('{:%Y:%m:%d}'.format(dt))
        matchidx = 0
        match,start,result,status = getmatches_dbcolPSL(date,matchidx)
        if match:
            send_bet(PAT, sender, match,matchidx,date)
        else:
            text = "No match planned for today"
            send_text(PAT, sender, text)
            send_default_quickreplies(PAT, sender)
    elif betID_found:
        date = msg_date
        matchidx = int(msg_matchidx)
        match,start,result,status = getmatches_dbcolPSL(date,matchidx)
        [start_h,start_m]=start.split(':')

        dt = datetime.datetime.now()
        currenttime = '{0}'.format('{:%H:%M}'.format(dt))
        [current_h,current_m]=currenttime.split(':')
        print currenttime
        print start
        if (int(current_h)*60) + int(current_m) <= (int(start_h)*60)+int(start_m):
            #add the bet to db
            text = "Your Bet for match %s played today has been registered" % (msg_match)
            send_text(PAT, sender, text)
            status_add = addbet_dbcoluser(msg_fbid,msg_match,msg_bet,msg_date)
            if status_add == "NAU":
                (first_name,last_name,locale,timezone,gender) = get_userInfo(PAT, msg_fbid)
                adduser_dbcoluser(msg_fbid,first_name, last_name, locale, timezone, gender)
                addbet_dbcoluser(msg_fbid,msg_match,msg_bet,msg_date)
        else:
            text = "Your Bet for match %s played today cannot be registered. It has been already started or already played" % (msg_match)
            send_text(PAT, sender, text)

        # for next match
        match,start,result,status = getmatches_dbcolPSL(date,matchidx+1)
        if match:
            send_bet(PAT, sender, match,matchidx+1,date)
        else:
            send_default_quickreplies(PAT, sender)
    elif "send_msg" in message_u and sender in [admin_hassmuha, admin_anadeem] :
        try:
            # getting associated betid if present from the message
            #2017:02:06,KK:QG,0,KK,1592912027389410
            [key ,message_tosent] = message_u.split(':')
        except ValueError:
            return "NOK"
        t = threading.Thread(target=send_alluser_text, args=(PAT,message_tosent,))
        t.start()
        print "thread start"
        #send_alluser_default_quickreplies(PAT)
    elif "send_all" in message_u and sender in [admin_hassmuha, admin_anadeem] :
        try:
            # getting associated betid if present from the message
            #2017:02:06,KK:QG,0,KK,1592912027389410
            [key,admin_command] = message_u.split(':')
        except ValueError:
            return "NOK"
        if "result" in admin_command:
            dt = datetime.datetime.now()
            todaydate = '{0}'.format('{:%Y:%m:%d}'.format(dt))
            t = threading.Thread(target=send_alluser_result, args=(PAT,todaydate,))
            t.start()
            print "thread start"
    elif "admin" in message_u and sender in [admin_hassmuha, admin_anadeem] :
        try:
            # getting associated betid if present from the message
            #2017:02:06,KK:QG,0,KK,1592912027389410
            [key,admin_command] = message_u.split(':')
        except ValueError:
            return "NOK"
        #UTM update today's match
        if "UTM" in admin_command:
            dt = datetime.datetime.now()
            date = '{0}'.format('{:%Y:%m:%d}'.format(dt))
            for matchidx in range(0, 2):
                match,start,result,status = getmatches_dbcolPSL(date,matchidx)
                if match:
                    matchid = ""
                    # matchid comes from calling another function from cricinfo
                    matchid = get_matchid(match)
                    print "Debug"
                    [hh,mm] = start.split(':')
                    start_minutes = (int(hh) * 60) + int(mm)
                    if status == "XX":
                        update_matchstatus(matchidx,match,matchid,start_minutes,"Match will start at %sGMT"%(start))
                    else:
                        update_matchstatus(matchidx,match,matchid,start_minutes,status)
                else:
                    update_matchstatus(matchidx,"XX","",0,"No match planned for today")
        elif "UR" in admin_command:
            dt = datetime.datetime.now()
            date = '{0}'.format('{:%Y:%m:%d}'.format(dt))
            for matchidx in range(0, 2):
                # print 1
                match_complete = check_complete(match_status_l[matchidx]["matchid"])
                #match_complete = check_complete("1075986")
                print match_complete
                if match_complete:
                    dt = datetime.datetime.now()
                    currenttime = dt.hour * 60 + dt.minute
                    match = match_status_l[matchidx]["match"]
                    matchid = match_status_l[matchidx]["matchid"]
                    update_matchstatus(matchidx,match,matchid,currenttime,match_complete)

                    if "karachi" in match_complete.lower():
                        result = "KK"
                    elif "lahore" in match_complete.lower():
                        result = "LQ"
                    elif "peshawar" in match_complete.lower():
                        result = "PZ"
                    elif "islamabad" in match_complete.lower():
                        result = "IU"
                    else:
                        result = "QG"
                    addresult_dbcolPSL(date,match_status_l[matchidx]["match"],result,match_complete)
        elif "SS" in admin_command:
            t = threading.Thread(target=send_alluser_score, args=(PAT,))
            t.start()
            print "thread start"
        elif "SQ" in admin_command:
            t = threading.Thread(target=send_alluser_default_quickreplies, args=(PAT,))
            t.start()
            print "thread start"
    elif "test" in message_u and sender in [admin_hassmuha, admin_anadeem] :
        try:
            # getting associated betid if present from the message
            #2017:02:06,KK:QG,0,KK,1592912027389410
            [key,admin_command] = message_u.split(':')
        except ValueError:
            return "NOK"
        #interface to call inituser_db
        if "INITUSER" in admin_command:
            try:
                #for post_user in db_coluser.find({"fbID": {'$exists': True}}):
                #    inituser_dbcoluser(post_user["fbID"])
                inituser_dbcoluser(sender)
            except ValueError:
                send_text(PAT, sender, "inituser_db Failed")
                return "NOK"
            send_text(PAT, sender, "inituser_db Done")

        send_text(PAT, admin_hassmuha, admin_command)
    elif message_u == "debug db" and sender in [admin_hassmuha, admin_anadeem] :
        #adduser_dbcoluser(sender,"first_name", "last_name", "locale", 1, "gender")
        addbet_dbcoluser(sender,"KK:QG","QG","2017:02:07")
        #addfrnd_dbcoluser(sender,sender)
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
    post = db_coluser.find_one({"fbID": fbID})
    if not post:
        post = {  "fbID": fbID,
                  "first_name" : first_name,
                  "last_name" : last_name,
                  "locale" : locale,
                  "timezone" : timezone,
                  "gender" : gender,
                  "getScoreClicks": 0,
                  "friends": [],
                  "bets":[],
                  "betrating":0}
        post_id = db_coluser.insert_one(post).inserted_id
    pprint.pprint(db_coluser.find_one({"fbID": fbID}))

def addbet_dbcoluser(fbID,match,bet,date):
    #post = db_coluser.find_one({"fbID": fbID,"bets.match":match,"bets.date":date})

    post = db_coluser.find_one({"fbID": fbID})
    if not post:
        return "NAU" #not a user


    pprint.pprint(post)
    post_bet = {"match":match,"bet":bet,"date":date}
    if post_bet not in post["bets"]:
        db_coluser.update_one({"fbID": fbID},{"$push": { "bets" : post_bet}} )
        print "new entry added"
    else:
        db_coluser.update_one({"fbID": fbID,"bets.match":match,"bets.date":date},{ "$set": { "bets.$.bet":bet }})
        print "last entry updated"
        #post = db_coluser.find_one({"fbID": fbID,"bets.match":match,"bets.date":date},{"bets."})
    # check what to use for replace
    pprint.pprint(db_coluser.find_one({"fbID": fbID}))

    return "OK"

def addresult_dbcolPSL(date,match,result,status):
    #print date + match + result + status
    db_colPSL.update_one({"date": date,"matches.match":match},{ "$set": { "matches.$.result":result, "matches.$.status":status}})

def addfrnd_dbcoluser(fbID,frnfbID):
    post_user = db_coluser.find_one({"fbID": fbID})
    if post_user:
        if {"fbID":frnfbID} not in post_user["friends"]:
            post_temp = {
                "fbID":frnfbID
            }
            post_temp2 = db_coluser.update_one({"fbID": fbID},{"$push": { "friends" : post_temp}} )
    # check what to use for replace
    # pprint.pprint(db_coluser.find_one({"fbID": fbID}))

def incgetScoreClicks_dbcoluser(fbID):
    post = db_coluser.update_one({"fbID": fbID},{"$inc": { "getScoreClicks" : 1}} )

def incbetrating_dbcoluser(fbID):
    post = db_coluser.update_one({"fbID": fbID},{"$inc": { "betrating" : 5}} )

# initialize existing user to default
def inituser_dbcoluser(fbID):
    #db_coluser.update_one({"fbID": fbID},[{ "$set": { "betrating":0 }},{ "$set": { "bets":[] }},{ "$set": { "getScoreClicks":0 }}])
    db_coluser.update_one({"fbID": fbID},{ "$set": { "betrating":0,"bets":[],"getScoreClicks":0}})

def send_default_quickreplies(token, recipient):
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
      params={"access_token": token},
      data=json.dumps({
        "recipient": {"id": recipient},
        "message": {
          "text":"Select the Options Below, or anytime click the menu left to text box",
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
              },
              {
                "content_type": "text",
                "title": "View Schedule",
                "payload": "schedule"
              }
          ]
        }
      }),
      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
      print r.text

def send_summary_share(token, recipient):
    murl = 'http://m.me/NostalMine?ref={0}'.format(recipient)
    url = "http://imagizer.imageshack.us/a/img924/6956/aRKza2.png"
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
                          "title":"Shakoor: Let's Predict PSL",
                          "subtitle":"A chatbot for live PSL score update and challenging friends on daily predictions",
                          "image_url":url,
                          "buttons":[
#                              {
 #                                 "type":"element_share"
  #                            }
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

def send_text(token, recipient, text):
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
      params={"access_token": token},
      data=json.dumps({
        "recipient": {"id": recipient},
        "message": {
          "text":text
        }
      }),
      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
      print r.text

# send all user some text
def send_alluser_text(token, text):
    for post in db_coluser.find({"fbID": {'$exists': True}},{ "fbID": 1}):
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
          params={"access_token": token},
          data=json.dumps({
            "recipient": {"id": post["fbID"]},
            "message": {
              "text":text
            }
          }),
          headers={'Content-type': 'application/json'})
        if r.status_code != requests.codes.ok:
          print r.text

def send_alluser_score(token):
    for post_user in db_coluser.find({"fbID": {'$exists': True}}):
        text = ""
        text = text + ("Your Current Score : %d\n*Your Friends Status*" % (post_user["betrating"]))
        idx = 0
        for idx,frn in enumerate(post_user["friends"]):
            frnfbID = frn["fbID"]
            post_frnd = db_coluser.find_one({"fbID": frnfbID})
            text = text + ("\n  %s %s : %d" % (post_frnd["first_name"],post_frnd["last_name"],post_frnd["betrating"]))
        if idx == 0:
            text = text + ("\n  None of your friend has accepted your Challenge")
        send_text(token, post_user["fbID"], text)


def send_alluser_result(token, date):
    post_PSL = db_colPSL.find_one({"date": date})
    for post_match in post_PSL["matches"]:
        print "debug"
        if post_match["result"] != "XX":
            print post_match["result"]

            if post_match["result"] == "KK":
                team_imgurl = "https://pslt20.blob.core.windows.net/team/1453111172542-team.png"
                team_weburl = "http://match.psl-t20.com/teams/karachi-kings"
                team_name = "Karachi Kings"
            elif post_match["result"] == "IU":
                team_imgurl = "https://pslt20.blob.core.windows.net/team/1453111086101-team.png"
                team_weburl = "http://match.psl-t20.com/teams/islamabad-united"
                team_name = "Islamabad United"
            elif post_match["result"] == "LQ":
                team_imgurl = "https://pslt20.blob.core.windows.net/team/1453111135284-team.png"
                team_weburl = "http://match.psl-t20.com/teams/lahore-qalandars"
                team_name = "Lahore Qalandars"
            elif post_match["result"] == "QG":
                team_imgurl = "https://pslt20.blob.core.windows.net/team/1453111043838-team.png"
                team_weburl = "http://match.psl-t20.com/teams/quetta-gladiators"
                team_name = "Quetta Gladiators"
            else:
                team_imgurl = "https://pslt20.blob.core.windows.net/team/1453111156446-team.png"
                team_weburl = "http://match.psl-t20.com/teams/peshawar-zalmi"
                team_name = "Peshawar Zalmi"

            win_title = "Congratulations!!"
            for post_user in db_coluser.find({"fbID": {'$exists': True}}):
                if {u'match': post_match["match"], u'bet': post_match["result"], u'date': date} in post_user["bets"]:
                    print "find result"
                    print post_user
                    # send msg abt the winner
                    win_subtitle = "%s wins today" % (team_name)
                    murl = 'http://m.me/NostalMine?ref={0}'.format(post_user["fbID"])
                    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                        "recipient": {"id": post_user["fbID"]},
                        "message": {
                          "attachment":{
                              "type":"template",
                              "payload":{
                                  "template_type":"generic",
                                  "elements":[
                                      {
                                          "title":win_title,
                                          "subtitle":win_subtitle,
                                          "image_url":team_imgurl,
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
                    incbetrating_dbcoluser(post_user["fbID"])
                else:
                    # send msg abt the lost
                    lost_text = "Sorry you lost the bet, %s wins today" % (team_name)
                    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                        "recipient": {"id": post_user["fbID"]},
                        "message": {
                          "text":lost_text
                        }
                      }),
                      headers={'Content-type': 'application/json'})
                    if r.status_code != requests.codes.ok:
                      print r.text

    print "debug1"

def send_alluser_default_quickreplies(token):
    for post in db_coluser.find({"fbID": {'$exists': True}},{ "fbID": 1}):
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
          params={"access_token": token},
          data=json.dumps({
            "recipient": {"id": post["fbID"]},
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

#match no is just for the allignment for iteratively send new match
def send_bet(token, recipient, match,matchno, date):
    print match
    [team1,team2]=match.split(':')
    team1_payload = "%s,%s,%i,%s,%s" % (date,match,matchno,team1,recipient)
    if team1 == "KK":
        team1_imgurl = "https://pslt20.blob.core.windows.net/team/1453111172542-team.png"
        team1_weburl = "http://match.psl-t20.com/teams/karachi-kings"
        team1_title = "Karachi Kings"
        team1_subtitle = "Karachi Kings will win the match on %s" % (date)
    elif team1 == "IU":
        team1_imgurl = "https://pslt20.blob.core.windows.net/team/1453111086101-team.png"
        team1_weburl = "http://match.psl-t20.com/teams/islamabad-united"
        team1_title = "Islamabad United"
        team1_subtitle = "Islamabad United will win the match on %s" % (date)
    elif team1 == "LQ":
        team1_imgurl = "https://pslt20.blob.core.windows.net/team/1453111135284-team.png"
        team1_weburl = "http://match.psl-t20.com/teams/lahore-qalandars"
        team1_title = "Lahore Qalandars"
        team1_subtitle = "Lahore Qalandars will win the match on %s" % (date)
    elif team1 == "QG":
        team1_imgurl = "https://pslt20.blob.core.windows.net/team/1453111043838-team.png"
        team1_weburl = "http://match.psl-t20.com/teams/quetta-gladiators"
        team1_title = "Quetta Gladiators"
        team1_subtitle = "Quetta Gladiators will win the match on %s" % (date)
    else:
        team1_imgurl = "https://pslt20.blob.core.windows.net/team/1453111156446-team.png"
        team1_weburl = "http://match.psl-t20.com/teams/peshawar-zalmi"
        team1_title = "Peshawar Zalmi"
        team1_subtitle = "Peshawar Zalmi will win the match on %s" % (date)

    team2_payload = "%s,%s,%i,%s,%s" % (date,match,matchno,team2,recipient)
    if team2 == "KK":
        team2_imgurl = "https://pslt20.blob.core.windows.net/team/1453111172542-team.png"
        team2_weburl = "http://match.psl-t20.com/teams/karachi-kings"
        team2_title = "Karachi Kings"
        team2_subtitle = "Karachi Kings will win the match on %s" % (date)
    elif team2 == "IU":
        team2_imgurl = "https://pslt20.blob.core.windows.net/team/1453111086101-team.png"
        team2_weburl = "http://match.psl-t20.com/teams/islamabad-united"
        team2_title = "Islamabad United"
        team2_subtitle = "Islamabad United will win the match on %s" % (date)
    elif team2 == "LQ":
        team2_imgurl = "https://pslt20.blob.core.windows.net/team/1453111135284-team.png"
        team2_weburl = "http://match.psl-t20.com/teams/lahore-qalandars"
        team2_title = "Lahore Qalandars"
        team2_subtitle = "Lahore Qalandars will win the match on %s" % (date)
    elif team2 == "QG":
        team2_imgurl = "https://pslt20.blob.core.windows.net/team/1453111043838-team.png"
        team2_weburl = "http://match.psl-t20.com/teams/quetta-gladiators"
        team2_title = "Quetta Gladiators"
        team2_subtitle = "Quetta Gladiators will win the match on %s" % (date)
    else:
        team2_imgurl = "https://pslt20.blob.core.windows.net/team/1453111156446-team.png"
        team2_weburl = "http://match.psl-t20.com/teams/peshawar-zalmi"
        team2_title = "Peshawar Zalmi"
        team2_subtitle = "Peshawar Zalmi will win the match on %s" % (date)

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
        params={"access_token": token},
        data=json.dumps({
          "recipient": {"id": recipient},
          "message": {
                        "text":"Today's Match %i: who will win?" % (matchno+1),
                        "quick_replies":[
                            {
                            "content_type":"text",
                            "title":team1_title,
                            "payload":team1_payload,
                            "image_url":team1_imgurl
                            },
                            {
                            "content_type":"text",
                            "title":team2_title,
                            "payload":team2_payload,
                            "image_url":team2_imgurl
                            }
                        ]
            }
        }),
        headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
      print r.text

# cricapi
def send_currentmatch(token, recipient):
    global match_status
    match_status_l = match_status
    data = []
    for idx,matchinfo in enumerate(match_status_l):
        if matchinfo["match"] == "XX":
            break
        [team1,team2] = matchinfo["match"].split(':')
        team1_name = team_map[team1]
        team2_name = team_map[team2]

        dt = datetime.datetime.now()
        currenttime = dt.hour * 60 + dt.minute

        if(("Match will start" in matchinfo["status"]) and currenttime < matchinfo["lastupdate"]):
            data.append({"content_type":"text", "title":"%s vs %s" %(team1_name,team2_name), "payload":"GS_%i_preview"%(idx), "image_url": "http://www.cs.odu.edu/~rnagella/harris@nrk/reverse%20engineering/AWForms/res/drawable/icon_yellow_dot.png"})
        elif("won" in matchinfo["status"].lower() or "tied" in matchinfo["status"].lower() or "result" in matchinfo["status"].lower()):
            data.append({"content_type":"text", "title":"%s vs %s" %(team1_name,team2_name), "payload":"GS_%i_complete"%(idx), "image_url": "http://www.clipartbest.com/cliparts/9Tp/eqj/9Tpeqjzjc.png"})
        else:
            data.append({"content_type":"text", "title":"%s vs %s" %(team1_name,team2_name), "payload":"GS_%i_live"%(idx), "image_url": "http://www.cs.odu.edu/~rnagella/harris@nrk/reverse%20engineering/AWForms/res/drawable/icon_green_dot.png"})
    if data:
        send_matches_quickreplies(token,recipient,data)
    else:
        text = "No match planned for today"
        send_text(token, recipient, text)
        send_default_quickreplies(token, recipient)

def send_matches_quickreplies(token,recipient,json_string):
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

def cricapi_livescore(matchinfo):
    batsmen= len(matchinfo["batting"]["batsman"])
    bowlers= len(matchinfo["bowling"]["bowler"])
    if "runs" in matchinfo["bowling"]["score"][0] :
        batteam = "%s %s/%s Overs:%s" %(matchinfo["batting"]["team"],matchinfo["batting"]["score"][0]["runs"],matchinfo["batting"]["score"][0]["wickets"],matchinfo["batting"]["score"][0]["overs"])
        bowlteam = "\n%s %s/%s Overs:%s" %(matchinfo["bowling"]["team"],matchinfo["bowling"]["score"][0]["runs"],matchinfo["bowling"]["score"][0]["wickets"],matchinfo["bowling"]["score"][0]["overs"])
        if(batsmen == 2):
            batsmeninfo = "\n\t%-20s %-4s %-4s %-4s %-4s \n\t%-20s %-4s %-4s %-4s %-4s" %(matchinfo["batting"]["batsman"][0]["name"],
            matchinfo["batting"]["batsman"][0]["runs"],matchinfo["batting"]["batsman"][0]["balls"],matchinfo["batting"]["batsman"][0]["fours"],matchinfo["batting"]["batsman"][0]["six"],
            matchinfo["batting"]["batsman"][1]["name"],matchinfo["batting"]["batsman"][1]["runs"],matchinfo["batting"]["batsman"][1]["balls"],matchinfo["batting"]["batsman"][1]["fours"],matchinfo["batting"]["batsman"][1]["six"])
        elif(batsmen == 1):
            batsmeninfo = "\n\t%-20s %-4s %-4s %-4s %-4s" %(matchinfo["batting"]["batsman"][0]["name"],
            matchinfo["batting"]["batsman"][0]["runs"],matchinfo["batting"]["batsman"][0]["balls"],matchinfo["batting"]["batsman"][0]["fours"],matchinfo["batting"]["batsman"][0]["six"])
        else:
            batsmeninfo = ""
        if(bowlers == 2):
            bowlerinfo = "\n\t%-20s %-4s %-4s %-4s %-4s \n\t%-20s %-4s %-4s %-4s %-4s" %(matchinfo["bowling"]["bowler"][0]["name"],
            matchinfo["bowling"]["bowler"][0]["overs"],matchinfo["bowling"]["bowler"][0]["runs"],matchinfo["bowling"]["bowler"][0]["maidens"],matchinfo["bowling"]["bowler"][0]["wickets"],
            matchinfo["bowling"]["bowler"][1]["name"],matchinfo["bowling"]["bowler"][1]["overs"],matchinfo["bowling"]["bowler"][1]["runs"],matchinfo["bowling"]["bowler"][1]["maidens"],matchinfo["bowling"]["bowler"][1]["wickets"])
        if(bowlers == 1):
            bowlerinfo = "\n\t%-20s %-4s %-4s %-4s %-4s " %(matchinfo["bowling"]["bowler"][0]["name"],
            matchinfo["bowling"]["bowler"][0]["overs"],matchinfo["bowling"]["bowler"][0]["runs"],matchinfo["bowling"]["bowler"][0]["maidens"],matchinfo["bowling"]["bowler"][0]["wickets"])
        else:
            if(bowlers == 1):
                bowlerinfo = ""
        #print batteam
        #print batsmeninfo
        #print bowlteam
        #print bowlerinfo
        cscore = batteam + batsmeninfo + bowlteam + bowlerinfo
        return cscore
    else:
        batteam = "%s %s/%s Overs:%s" %(matchinfo["batting"]["team"],matchinfo["batting"]["score"][0]["runs"],matchinfo["batting"]["score"][0]["wickets"],matchinfo["batting"]["score"][0]["overs"])
        bowlteam = "\n%s" %(matchinfo["bowling"]["team"])
        if(batsmen == 2):
            batsmeninfo = "\n\t%-20s %-4s %-4s %-4s %-4s \n\t%-20s %-4s %-4s %-4s %-4s" %(matchinfo["batting"]["batsman"][0]["name"],
            matchinfo["batting"]["batsman"][0]["runs"],matchinfo["batting"]["batsman"][0]["balls"],matchinfo["batting"]["batsman"][0]["fours"],matchinfo["batting"]["batsman"][0]["six"],
            matchinfo["batting"]["batsman"][1]["name"],matchinfo["batting"]["batsman"][1]["runs"],matchinfo["batting"]["batsman"][1]["balls"],matchinfo["batting"]["batsman"][1]["fours"],matchinfo["batting"]["batsman"][1]["six"])
        elif(batsmen == 1):
            batsmeninfo = "\n\t%-20s %-4s %-4s %-4s %-4s" %(matchinfo["batting"]["batsman"][0]["name"],
            matchinfo["batting"]["batsman"][0]["runs"],matchinfo["batting"]["batsman"][0]["balls"],matchinfo["batting"]["batsman"][0]["fours"],matchinfo["batting"]["batsman"][0]["six"])
        else:
            batsmeninfo = ""
        if(bowlers == 2):
            bowlerinfo = "\n\t%-20s %-4s %-4s %-4s %-4s \n\t%-20s %-4s %-4s %-4s %-4s" %(matchinfo["bowling"]["bowler"][0]["name"],
            matchinfo["bowling"]["bowler"][0]["overs"],matchinfo["bowling"]["bowler"][0]["runs"],matchinfo["bowling"]["bowler"][0]["maidens"],matchinfo["bowling"]["bowler"][0]["wickets"],
            matchinfo["bowling"]["bowler"][1]["name"],matchinfo["bowling"]["bowler"][1]["overs"],matchinfo["bowling"]["bowler"][1]["runs"],matchinfo["bowling"]["bowler"][1]["maidens"],matchinfo["bowling"]["bowler"][1]["wickets"])
        if(bowlers == 1):
            bowlerinfo = "\n\t%-20s %-4s %-4s %-4s %-4s " %(matchinfo["bowling"]["bowler"][0]["name"],
            matchinfo["bowling"]["bowler"][0]["overs"],matchinfo["bowling"]["bowler"][0]["runs"],matchinfo["bowling"]["bowler"][0]["maidens"],matchinfo["bowling"]["bowler"][0]["wickets"])
        else:
            if(bowlers == 1):
                bowlerinfo = ""
        #print batteam
        #print batsmeninfo
        #print bowlteam
        #print bowlerinfo
        cscore = batteam + batsmeninfo + bowlteam + bowlerinfo
        return cscore

def cricapi_preview(matchinfo):
    cscore = matchinfo["mchdesc"] + "\n" + matchinfo["status"]
    return cscore

def cricapi_complete(matchinfo):
    cscore = matchinfo["mchdesc"] + "\n" + matchinfo["status"]
    return cscore

def get_livescore(matchid):
    url = "http://www.espncricinfo.com/matches/engine/match/" + matchid + ".json"
    r = requests.get(url)
    try:
      info_json = r.json()
      scoreline = live_scorecard(info_json)
      playersInfo = latest_batting(info_json)
    except:
      scoreline = ""
      playersInfo = ""
    return (scoreline +"\n"+ playersInfo)

# getting scorecard
def live_scorecard(my_json):
    playingTeams = {team.get("team_id"): team.get("team_name") for team in my_json.get("team")}
    innings = my_json.get("live").get("innings")
    team = []
    for index,inn in enumerate(my_json['innings']):
        team.append({"team_id":inn["batting_team_id"],"overs":inn["overs"],"runs":inn["runs"],"wickets":inn["wickets"]})
        if innings.get("batting_team_id") == inn["batting_team_id"]:
            idx_bat = index

    idx_bowl = 0 if idx_bat else 1

    if len(team) == 2:
        scoreToDisplay = "%s* %s/%s overs:%s vs %s %s/%s" % (playingTeams.get(team[idx_bat]["team_id"]),
        team[idx_bat]["runs"],
        team[idx_bat]["wickets"],
        team[idx_bat]["overs"],
        playingTeams.get(team[idx_bowl]["team_id"]),
        team[idx_bowl]["runs"],
        team[idx_bowl]["wickets"])
    else:
        scoreToDisplay = "%s* %s/%s overs:%s vs %s" % (playingTeams.get(team[idx_bat]["team_id"]),team[idx_bat]["runs"],team[idx_bat]["wickets"],team[idx_bat]["overs"],playingTeams.get(innings.get("bowling_team_id")))
    return scoreToDisplay

##Only When not COMPLETE
def latest_batting(my_json):
    try:
        temp = my_json["match"]["current_summary"]
        [temp_a, temp_b] = temp.split("ov,")
        return temp_b[:-1]
    except:
        return ""
    # try:
    #     info =[]
    #     for current_batsman in my_json['centre']['common']['batting']:
    #         if current_batsman["notout"] == "1" :
    #             info.append(current_batsman["known_as"] + "_" + current_batsman["runs"] + "_" + current_batsman["balls_faced"])
    #     for current_bowler in my_json['centre']['common']['bowling']:
    #         if "live_current_name" in current_bowler :
    #             info.append(current_bowler["known_as"] + "_" + current_bowler["overs"] + "_" + current_bowler["conceded"]+ "_" + current_bowler["maidens"]+ "_" + current_bowler["wickets"])
    #     return info
    # except:
    #     return ""

##CHECK FOR COMPLETION
def check_complete(matchid):
    if matchid:
        url = "http://www.espncricinfo.com/matches/engine/match/" + matchid + ".json"
    else:
        return ""
    r = requests.get(url)
    info_json = r.json()
    if  (info_json.get('match').get('match_status') == "complete" or "won" in info_json['live']['status'] or "tied" in info_json['live']['status'] or "result" in info_json['live']['status']) and "toss" not in info_json['live']['status']:
        return info_json['live']['status']
    else:
        return ""

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
    first_name = ""
    last_name = ""
    locale = ""
    timezone = ""
    gender = ""
    if user_data:
        first_name = user_data["first_name"]
        last_name = user_data["last_name"]
        locale = user_data["locale"]
        timezone = user_data["timezone"]
        gender = user_data["gender"]
    return (first_name,last_name,locale,timezone,gender)

def getmatches_dbcolPSL(date,matchno):
    post = db_colPSL.find_one({"date": date})
    match = ""
    start = ""
    result = ""
    status = ""
    if not post:
        print "PSL DB Error: no match planned for %s" % (date)
    elif matchno < len(post["matches"]):
        match = post["matches"][matchno]["match"]
        start = post["matches"][matchno]["start"]
        result = post["matches"][matchno]["result"]
        status = post["matches"][matchno]["status"]
    return (match,start,result,status)
    # check what to use for replace

def update_matchstatus(matchidx,match,matchid,lastupdate,status):
    global match_status
    match_status[matchidx]['match'] = match
    match_status[matchidx]['matchid'] = matchid
    match_status[matchidx]['lastupdate'] = lastupdate
    match_status[matchidx]['status'] = status

def get_matchid(match):
    url="http://static.cricinfo.com/rss/livescores.xml"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    xml = soup.find_all("item")
    #print xml
    matchId = ""
    for matchinfo in xml:
        [team1,team2] = match.split(':')
        team1_name = team_map[team1]
        team2_name = team_map[team2]
        if team1_name.lower() in matchinfo.title.text.lower() and team2_name.lower() in matchinfo.title.text.lower():
            guid = matchinfo.guid.text
            matchId = re.search(r'\d+', guid).group()
    return matchId

if __name__ == "__main__":
    app.run()
