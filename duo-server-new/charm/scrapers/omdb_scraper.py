import omdb
from omdb import OMDBClient

#i=tt3896198&apikey=2064710e
client = OMDBClient(apikey='2064710e')
data = client.get(year=2017, media_type='movie')
print(data)

# res = omdb.request(y=2018, r='xml', type='movie')
# print(res.content)