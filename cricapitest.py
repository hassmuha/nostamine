from pycricbuzz import Cricbuzz
import json


def Oneday(data2):
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
        cscore = batteam + batsmeninfo + bowlteam + bowlerinfo
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
        cscore = batteam + batsmeninfo + bowlteam + bowlerinfo
        return cscore
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
data2 = c.livescore(18012)
matchinfo = data2["matchinfo"]
scorecard = data1["scorecard"]
innings= len(scorecard)
batsmen= len(data2["batting"]["batsman"])
bowlers= len(data2["bowling"]["bowler"])
#data2=c.scorecard(1)
print json.dumps(data2,indent=4)
print "%s"%(data2["batting"]["score"][0]["overs"])
if(matchinfo["type"] == "ODI" or matchinfo["type"] == "T20"):
    c = Oneday(data2)
    print c
