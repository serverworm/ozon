from curl_cffi import requests
import json

# формируем сессию и получаем куки
s = requests.Session()
s.get("https://www.ozon.ru")
print(*str(s.cookies).split(", "), sep="\n")

r = s.get("https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=/product/futbolka-rustactic-politsiya-991026398")

json_data = json.loads(r.content.decode())
print(json_data["seo"]["title"])
print(json.loads(json_data["seo"]["script"][0]["innerHTML"])["description"])
print(json.loads(json_data["seo"]["script"][0]["innerHTML"])["image"])
print(json.loads(json_data["seo"]["script"][0]["innerHTML"])["offers"]["price"] + " " +
      json.loads(json_data["seo"]["script"][0]["innerHTML"])["offers"]["priceCurrency"])
print(json.loads(json_data["seo"]["script"][0]["innerHTML"])["sku"])