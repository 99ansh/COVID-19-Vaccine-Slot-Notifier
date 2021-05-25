import requests
import json
from pymongo import MongoClient, collection
client = MongoClient("mongodb://localhost:27017")
database = client["temp"]
states_districts = database["states_districts"]
states_districts.remove({})

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
}

response = requests.get(
    "https://cdn-api.co-vin.in/api/v2/admin/location/states", headers=headers
)
states = json.loads(response.text)["states"]

custom_state_id=1

for state in states:
    state_id = state["state_id"]
    state_name = state["state_name"].strip()
    print(state_name)
    response = requests.get(
        "https://cdn-api.co-vin.in/api/v2/admin/location/districts/" + str(state_id),
        headers=headers,
    )
    custom_district_id=1
    temp=[]
    districts = json.loads(response.text)["districts"]
    for district in districts:
        district_id = district["district_id"]
        district_name = district["district_name"].strip()
        data={"state_name":state_name,"custom_state_id":custom_state_id,"district_name":district_name,"custom_district_id":custom_district_id,"actual_district_id":district_id}
        states_districts.insert_one(data)
        custom_district_id+=1
    custom_state_id+=1