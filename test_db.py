from flask import Flask, request
import json
import requests
import pymongo
import os

import time
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



#@app.route("/")
#def hello():
    #db = mongo.db
    # First we'll add a few songs. Nothing is required to create the songs
    # collection; it is created automatically when we insert.
    #songs = db['songs']
    # Note that the insert method can take either an array or a single dict.
    #addbet_database('recipient', 'KK', 'recipient')

    #return "Hello World!"



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
    # if message != "I can't echo this" :
    if message == "Hi" :
    	send_message(PAT, sender, message,payload)
  return "ok"

def messaging_events(payload):
  """Generate tuples of (sender_id, message_text) from the
  provided payload.
  """
  data = json.loads(payload)
  messaging_events = data["entry"][0]["messaging"]
  for event in messaging_events:
    if "message" in event and "text" in event["message"]:
      yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape')
    else:
      yield event["sender"]["id"], "I can't echo this"

# this will add a new document for the bet in database
def addbet_database(fbID, bet, betid):
  post = {  "fbID": fbID,
            "decision": bet,
            "betid": betid,
            "Participant": [(fbID,bet),(fbID,bet)]}
  post_id = posts.insert_one(post).inserted_id
  #pprint.pprint(posts.find_one({"fbID": fbID}))
  for cursor in posts.find({"fbID": fbID}):
      print cursor
  print post_id


def send_message(token, recipient, text, payload):
  """Send the message text to recipient with id recipient.
  """

  r = requests.post("https://graph.facebook.com/v2.6/me/messages",
    params={"access_token": token},
    data=json.dumps({
      "recipient": {"id": recipient},
      "message": {"text": text.decode('unicode_escape')}
    }),
    headers={'Content-type': 'application/json'})
  if r.status_code != requests.codes.ok:
    print r.text
  data = json.loads(payload)
  messaging_events = data["entry"][0]["messaging"]
  timestamp = str(messaging_events[0]["timestamp"])
  print timestamp
  print recipient

  betid = '{0}{1}'.format(recipient, timestamp)
  print betid
  addbet_database(recipient, 'KK', betid)

if __name__ == "__main__":
    app.run()
