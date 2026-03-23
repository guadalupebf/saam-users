import requests
import json
from core.utils import get_jwt_token
from django.conf import settings

def save_orginfo_saam(org):
    try:
        payload = {
            "org": org
        }
        headers = {
            'Content-Type': 'application/json' ,
            'Authorization':  get_jwt_token({'key_cas': settings.KEY_CAS})
        }
        r = requests.post(settings.SAAM_API_IP + 'add-orginfo/', json.dumps(payload), headers = headers, verify=False)
        if(r.status_code == 200):
            return True
        return False
    except:
        return False