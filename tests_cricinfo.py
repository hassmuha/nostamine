import requests
import json
import re

#id="1075988"
id="1075990"

def match(id):
    m = "http://www.espncricinfo.com/matches/engine/match/" + id + ".json"
    return m

def get_json(url):
    r = requests.get(m)
    return r.json()

def match_json(my_json):
        return my_json['match']




##Only When not COMPLETE
def latest_batting(my_json):
    try:
        info =[]
        for current_batsman in my_json['centre']['common']['batting']:
            if current_batsman["notout"] == "1" :
                info.append(current_batsman["known_as"] + "_" + current_batsman["runs"] + "_" + current_batsman["balls_faced"])
        for current_bowler in my_json['centre']['common']['bowling']:
            if "live_current_name" in current_bowler :
                info.append(current_bowler["known_as"] + "_" + current_bowler["overs"] + "_" + current_bowler["conceded"]+ "_" + current_bowler["maidens"]+ "_" + current_bowler["wickets"])
        return info
    except:
        return None

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
        scoreToDisplay = "%s %s/%s overs:%s vs %s %s/%s" % (playingTeams.get(team[idx_bat]["team_id"]),
        team[idx_bat]["runs"],
        team[idx_bat]["wickets"],
        team[idx_bat]["overs"],
        playingTeams.get(team[idx_bowl]["team_id"]),
        team[idx_bowl]["runs"],
        team[idx_bowl]["wickets"])
    else:
        scoreToDisplay = "%s %s/%s overs:%s vs %s" % (playingTeams.get(team[idx_bat]["team_id"]),team[idx_bat]["runs"],team[idx_bat]["wickets"],team[idx_bat]["overs"],playingTeams.get(innings.get("bowling_team_id")))
    return (scoreToDisplay)

##CHECK FOR COMPLETION
def check_complete(my_json):
    if  my_json.get('match').get('match_status') == "complete":
        return True
    else:
        return False

##RESULTS
def result(my_json):
    return my_json['live']['status']

m = match(id)
info = get_json(m)
print json.dumps(info["match"]["current_summary"], indent=4)
a = info["match"]["current_summary"]
[a,b] = a.split("ov,")
print a
print b[:-1]
print latest_batting(info)
print result(info)
print check_complete(info)
print live_scorecard(info)
