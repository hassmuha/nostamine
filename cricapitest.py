from pycricbuzz import Cricbuzz
import json
c = Cricbuzz()
matches = c.matches()
print json.dumps(matches,indent=4) #for pretty prinitng
data = []
for match in matches:
    data.append({"content_type":"text", "title":match['mchdesc'], "payload":match['id']})
print json.dumps(data,indent=4)
data1=json.dumps({
 "recipient": {"id": "567"},
 "message":{
    "text":"Pick a color:",
    "quick_replies": data
  }
})
print data1
