print result.deleted_count
SEED_DATA = [
  {
    'decade' : '1970s',
    'artist' : 'Debby Boone',
    'song' : 'You Light Up My Life',
    'weeksAtOne' : 10
  },
  {
    'decade' : '1980s',
    'artist' : 'Olivia Newton-John',
    'song' : 'Physical',
    'weeksAtOne' : 10
  },
  {
    'decade' : '1990s',
    'artist' : 'Mariah Carey',
    'song' : 'One Sweet Day',
    'weeksAtOne' : 16
  }
]
songs.insert(SEED_DATA)

# Then we need to give Boyz II Men credit for their contribution to
# the hit "One Sweet Day".

query = {'song': 'One Sweet Day'}

songs.update(query, {'$set': {'artist': 'Mariah Carey ft. Boyz II Men'}})

# Finally we run a query which returns all the hits that spent 10 or
# more weeks at number 1.

cursor = songs.find({'weeksAtOne': {'$gte': 10}}).sort('decade', 1)

for doc in cursor:
    print ('%s %s %s' %
           (doc['decade'], doc['song'], doc['artist'], doc['weeksAtOne']))
