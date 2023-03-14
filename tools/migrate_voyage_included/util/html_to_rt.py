import json
from urllib.request import Request, urlopen


def html_to_rt(html):
    if not html:
        return None
    
    req = Request("http://localhost:3000/convert")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    json_data = json.dumps({"from": "html", "to": "richtext", "html": html})
    json_data_as_bytes = json_data.encode("utf-8")
    req.add_header("Content-Length", str(len(json_data_as_bytes)))
    response = urlopen(req, json_data_as_bytes).read()
    return json.loads(response)