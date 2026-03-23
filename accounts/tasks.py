from __future__ import absolute_import, unicode_literals
import celery
from time import sleep
from django.shortcuts import get_object_or_404
from .models import UserInfo
from rest_framework.authtoken.models import Token
from core.utils import get_app_permissions, get_jwt_token
import requests
from django.conf import settings
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import json
import redis
from django.core.cache import cache
# El decorador shared_task sirve para crear tareas independientes a la app.
# Pero notar que podéis usar cualquier librería y clase aquí. Incluido el orm para acceder a la bd.


redisClient = redis.StrictRedis(host = 'localhost', port = 6379, db = 0)


# @celery.task(bind=True)
# def get_claves_from_saam_api(self, _id, org = None):

def get_jwt(_id, org, data = None):
    user = User.objects.get(pk = _id)
    
    token = Token.objects.get(user = user)
    jwt_json = {
        'token': token.key, 
        'is_superuser' : user.is_superuser,
        'username': user.username,
        'org': org
    }
    if data:
        jwt_json['data'] = data


    if UserInfo.objects.filter(user = user).exists():
        user_info = UserInfo.objects.get(user=user)
        permissions = get_app_permissions(user_info.id)
        apps_dict =  {"applications":list(user_info.user_profiles.filter(is_active=True).values_list('application__name', flat=True))}
        jwt_json.update(apps_dict)

        if user_info.org:
            org = user_info.org.urlname
            jwt_json.update({"org": org})

    

    expiration_date =  (datetime.now() + timedelta(minutes=60)).strftime('%Y-%m-%d %H:%M:%S')
    jwt_json.update({'expiration': expiration_date})
    token_jwt = get_jwt_token(jwt_json)
    return token_jwt



def get_aseguradoras_from_saam_api(_id, org):
    token_jwt = get_jwt(_id, org)

    payload = {
        "Authorization": "Bearer %s" % token_jwt
    }
    headers = {
        'Content-Type': 'application/json' ,
        'Authorization': 'Bearer %s' % token_jwt
    }

    r = requests.post(settings.SAAM_API_IP + 'provider-cas/', json.dumps(payload), headers = headers, verify=False)
    if(r.status_code == 200):
        if r.text == []:
            return []
        else:
            return r.json()
    else:
        return None

def get_aseguradoras_from_saam_api_perfil(_id, org):
    token_jwt = get_jwt(_id, org)

    payload = {
        "Authorization": "Bearer %s" % token_jwt
    }
    headers = {
        'Content-Type': 'application/json' ,
        'Authorization': 'Bearer %s' % token_jwt
    }

    r = requests.post(settings.SAAM_API_IP + 'provider-casPerfil/', json.dumps(payload), headers = headers, verify=False)
    if(r.status_code == 200):
        if r.text == []:
            return []
        else:
            return r.json()
    else:
        return None

def get_ramos_from_saam_api(_id, aseguradora_id, org = None):
    token_jwt = get_jwt(_id, org)

    payload = {
        "Authorization": "Bearer %s" % token_jwt
    }
    headers = {
        'Content-Type': 'application/json' ,
        'Authorization': 'Bearer %s' % token_jwt
    }

    r = requests.post(settings.SAAM_API_IP + 'ramos-cas/' + aseguradora_id, json.dumps(payload), headers = headers, verify=False)
    if(r.status_code == 200):
        if r.text == []:
            return []
        else:
            return r.json()
    else:
        return None


def get_subramos_from_saam_api(_id, aseguradora_id, ramo_id, org = None):
    token_jwt = get_jwt(_id, org)

    payload = {
        "Authorization": "Bearer %s" % token_jwt
    }
    headers = {
        'Content-Type': 'application/json' ,
        'Authorization': 'Bearer %s' % token_jwt
    }

    r = requests.post(settings.SAAM_API_IP + 'subramos-cas/' + aseguradora_id + '/' + ramo_id, json.dumps(payload), headers = headers, verify=False)
    if(r.status_code == 200):
        if r.text == []:
            return []
        else:
            return r.json()
    else:
        return None


def get_claves_general_from_saam_api(_id, data, org = None):
    # task_id = self.request.id
    token_jwt = get_jwt(_id, org, data)

    payload = {
        "Authorization": "Bearer %s" % token_jwt
    }
    headers = {
        'Content-Type': 'application/json' ,
        'Authorization': 'Bearer %s' % token_jwt
    }
    r = requests.post(settings.SAAM_API_IP + 'claves-general-cas/', json.dumps(payload), headers = headers, verify=False)
    if(r.status_code == 200):
        if r.text == []:
            return []
        else:
            return r.json()
    else:
        return None



def get_comisiones_from_saam_api(_id, clave_id, org = None):
    # task_id = self.request.id
    token_jwt = get_jwt(_id, org)

    payload = {
        "Authorization": "Bearer %s" % token_jwt
    }
    headers = {
        'Content-Type': 'application/json' ,
        'Authorization': 'Bearer %s' % token_jwt
    }
    r = requests.post(settings.SAAM_API_IP + 'comisiones-cas/'+ clave_id, json.dumps(payload), headers = headers, verify=False)
    if(r.status_code == 200):
        if r.text == []:
            return []
        else:
            return r.json()
    else:
        return None

def create_clave_saam_api(_id, data, org = None):
    # task_id = self.request.id
    token_jwt = get_jwt(_id, org, data)

    payload = {
        "Authorization": "Bearer %s" % token_jwt
    }
    headers = {
        'Content-Type': 'application/json' ,
        'Authorization': 'Bearer %s' % token_jwt
    }

    r = requests.post(settings.SAAM_API_IP + 'clave-cas/', json.dumps(payload), headers = headers, verify=False)
    if(r.status_code == 201):
        return json.loads(r.text)
    else:
        return r.text


def create_comision_saam_api(_id, data, org = None):
    # task_id = self.request.id
    token_jwt = get_jwt(_id, org, data)

    payload = {
        "Authorization": "Bearer %s" % token_jwt
    }
    headers = {
        'Content-Type': 'application/json' ,
        'Authorization': 'Bearer %s' % token_jwt
    }

    r = requests.post(settings.SAAM_API_IP + 'comision-cas/', json.dumps(payload), headers = headers, verify=False)
    if(r.status_code == 201):
        return json.loads(r.text)
    else:
        return r.text

