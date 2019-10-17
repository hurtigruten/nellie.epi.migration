from urllib.request import Request, urlopen
import json

req = Request('https://global.hurtigruten.com/rest/excursion/excursions', headers={'User-Agent': 'Mozilla/5.0'})
webpage = urlopen(req).read()
data = json.loads(webpage)
print(len(data))