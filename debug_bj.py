import urllib.request
import json
import urllib.parse

key = "4a8be77cc644d042ef16ee0a5e194bfc"
url = f"https://restapi.amap.com/v3/config/district?keywords={urllib.parse.quote('北京市')}&subdistrict=1&key={key}"

with urllib.request.urlopen(url) as response:
    data = json.loads(response.read())
    print(json.dumps(data, indent=2, ensure_ascii=False))
