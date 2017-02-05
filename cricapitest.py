from pycricbuzz import Cricbuzz
import json
c = Cricbuzz()
matches = c.matches()
print json.dumps(matches,indent=4) #for pretty prinitng
data = []
for match in matches:
    data.append({"content_type":"text", "title":match['mchdesc'], "payload":match['id']})
print json.dumps(data,indent=4)

##data1=json.dumps({
## "recipient": {"id": "567"},
## "message":{
##    "text":"Pick a color:",
##    "quick_replies": data
##  }
##})
##print data1
#print json.dumps(c.livescore(1),indent=4)
data1= c.scorecard(2)
matchinfo = data1["matchinfo"]
scorecard = data1["scorecard"]
innings= len(scorecard)
#data2=c.scorecard(1)
#print json.dumps(data1,indent=4)
if innings == 1:
    print "%s" %(matchinfo["status"])
    cscore = "%s %s/%s Overs:%s vs \n%s" %(data1["scorecard"][0]["batteam"],
    data1["scorecard"][0]["runs"],data1["scorecard"][0]["wickets"],data1["scorecard"][0]["overs"],
    data1["scorecard"][0]["bowlteam"])
    print cscore
if innings == 2:
    print "%s" %(matchinfo["status"])
    cscore = "%s %s/%s Overs:%s vs \n%s %s/%s Overs:%s" % (data1["scorecard"][0]["batteam"],
    data1["scorecard"][0]["runs"],data1["scorecard"][0]["wickets"],data1["scorecard"][0]["overs"],
    data1["scorecard"][0]["bowlteam"],data1["scorecard"][1]["runs"],data1["scorecard"][1]["wickets"],data1["scorecard"][1]["overs"])
    print cscore
print matchinfo
#print scorecard
#print json.dumps(scorecard, indent=4)

#print json.dumps(c.commentary(1),indent=4)
