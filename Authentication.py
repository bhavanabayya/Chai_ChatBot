import requests
from fedex_config import CLIENT_ID, CLIENT_SECRET

# FedEx sandbox OAuth endpoint
OAUTH_URL = "https://apis-sandbox.fedex.com/oauth/token"

def get_fedex_token():
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    print(" Requesting FedEx access token...")
    response = requests.post(OAUTH_URL, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        # print(" Access Token:", token)
        print(" Successfully obtained FedEx access token.")   
        return token
    else:
        print(" Failed to get token")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return None
