from django.conf import settings
from rest_framework.authtoken.models import Token

from core.utils import get_jwt_token,delete_token

from datetime import datetime
from datetime import timedelta
import requests
import json


def update_beneficios_app(user, org=''):
    api_url = settings.SAAM_API_IP + 'app-datavalidate'
    params = {
        "user_username": user.username,
        "user_email": user.email,
        "user_password": user.password,
        "user_first_name" : user.first_name,
        "user_last_name" : user.last_name
    }

    r = requests.post(api_url, params, verify=False)
    result= json.loads(r.text)
    delete_token(user.id)
    if Token.objects.filter(user=user).exists():
        Token.objects.filter(user=user).delete()
    token, created = Token.objects.get_or_create(user=user)
    print(token)
    expiration_date =  (datetime.now() + timedelta(minutes=settings.TOKEN_DURATION)).strftime('%Y-%m-%d %H:%M:%S')
    jwt_token = {
        'token': token.key,
        "applications":list(),
        "org": {
            "id":0,
            "name":org
            },
        'expiration_date': expiration_date
        }
    return {'token': get_jwt_token(jwt_token)}


def validate_saam_email(email):
    # headers = {
    #     'Authorization': 'Token %s' % UserInfo.objects.get(user=request.user).saam_token
    # }
    r = requests.get(settings.SAAM_API_IP + 'validate-ibis-siss/?email='+str(email), )
    return json.loads(r.text.lower())