from flask import Flask, request
import json
import requests
import pymongo
import os

app = Flask(__name__)
# connect to MongoDB with the defaults
#mongo = PyMongo(app)
#client = pymongo.MongoClient(os.environ.get('MONGODB_URI'))
#db = client.get_default_database()

# This needs to be filled with the Page Access Token that will be provided
# by the Facebook App that will be created.
PAT = 'EAAIeJYNmvk0BACXjV9sUcwwNnfg0EM2y5zv2prZAH6ilxX9ouAHZBM1ZC9Hn96cUSVRCtK5fXuo1qnbZAMZC0jysfdhURw5Kq6VmB0g80AX9LpZCF7Ro0NcOXZCR4ZBCfvAsGU4aeRJD8mZBaGhBzZB00x5bbOZAluuS7IelpZAOTPbq1AZDZD'

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
    if message == "new_bet" :
        team_select(PAT, sender, message)
    elif message in ["Karachi", "Lahore", "Quetta", "Peshawer","Islamabad"]:
        send_message(PAT, sender, message)
        print message
    elif message != "I can't echo this" :
#    	send_message(PAT, sender, message)
        print "I am here"

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
                                "title":"Challenge accepted",
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
                                "title":"Challenge accepted",
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
                                "title":"Challenge accepted",
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
                                "title":"Challenge accepted",
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
                                "title":"Challenge accepted",
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
                                "type":"postback",
                                "title":"Challenge accepted",
                                "payload":"BETID"
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

if __name__ == "__main__":
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
      params={"access_token": PAT},
      data={
        "setting_type":"call_to_actions",
        "thread_state":"new_thread",
        "call_to_actions":[
        {
            "payload":"new_bet"
        }
        ]
        },
      headers={'Content-type': 'application/json'})
      print "GET STARTED"
    if r.status_code != requests.codes.ok:
      print r.text
    app.run()
