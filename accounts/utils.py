import requests
import json
from core.utils import get_jwt_token
from django.conf import settings

def save_userinfo_saam(org, username, firstname, lastname, email, perfilRestringido = 0,saam_exists=False,saam_pair=[]):
    success = False
    if not perfilRestringido:
        perfilRestringido = 0
    try:
        payload = {
            "org": org,
            "username": username,
            "first_name": firstname,
            "last_name": lastname, 
            "email": email,
            "perfilRestringido": perfilRestringido,
            "saam_exists": saam_exists,
            "saam_pair": saam_pair
        }
        headers = {
            'Content-Type': 'application/json' ,
            'Authorization':  get_jwt_token({'key_cas':'In73RN41K3yCa5'})
        }
        r = requests.post(settings.SAAM_API_IP + 'add-userinfo/', json.dumps(payload), headers = headers, verify=False)
        print(r.text)
        if(r.status_code == 200):
            success =  True
    except Exception as e:
        print('Exception to save info user in saam=>', str(e))
        
    return success
