import jwt
from django.conf import settings
from accounts.models import UserPermission, UserInfo
from rest_framework import serializers 
import requests
import json

def get_jwt_token(json_info):
    token = None
    try:
        token_bytes = jwt.encode(json_info, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        token = token_bytes.decode()
        # print('Token =>', token)
        
    except Exception as e:
        print('Error al genera el token =>', str(e))    
    return token
    

def decode_token(token):
    json_info = None
    try:
        json_info = jwt.decode(token,settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        # print('json info =>',json_info)
    except Exception as e:
        print('Error al decodificar token el token =>', str(e))    
    return json_info

def delete_token(user_id):
    try:
        headers = {
            'Content-Type': 'application/json' ,
            'Authorization':  get_jwt_token({'key_cas': settings.KEY_CAS})
        }
        r = requests.post(settings.SAAM_API_IP + 'control/delete-session/', headers = headers, data=json.dumps({"user_id":user_id}), verify=False)
        if r.status_code == 200:
            return True
    except Exception as e:
        print("Exception delete Session saam =>", str(e))
    
    return False 


def get_app_permissions(userinfo_id, appname=None):
    permissions = {}
    try:
        user_info = UserInfo.objects.get(id=userinfo_id)  
        if appname:
            profiles = user_info.user_profiles.filter(is_active=True, application__name=appname)
        else:
            profiles = user_info.user_profiles.filter(is_active=True)
        for profile in profiles:
            app_name = profile.application.name
            app_dict = {app_name: ''}
            permission_dict = {}
            user_permissions =  UserPermission.objects.filter(profile=profile, is_active=True).values('permission__model__name', 'permission__name', 'checked', 'is_active')
            for p in user_permissions:
                model = p['permission__model__name'] 
                p_name = p['permission__name']
                p_checked = p['checked']
                p_isactive = p['is_active']
                if not model in permission_dict:
                    permission_dict.update({model: [{"name":p_name, 'checked': p_checked, 'is_active':p_isactive}]})
                else:
                    permission_dict[model].append({"name":p_name, 'checked': p_checked, 'is_active':p_isactive})

            app_dict[app_name] = permission_dict
            permissions.update(app_dict)
    except Exception as e:
        print("Error to get persmission =>", str(e))
    return permissions

def get_app_permissions_front(userinfo_id, appname=None):
    permissions = {}
    try:
        user_info = UserInfo.objects.get(id=userinfo_id)  
        if appname:
            profiles = user_info.user_profiles.filter(is_active=True, application__name=appname)
        else:
            profiles = user_info.user_profiles.filter(is_active=True)
        for profile in profiles:
            app_name = profile.application.name
            app_dict = {app_name: ''}
            permission_dict = {}
            user_permissions =  UserPermission.objects.filter(profile=profile, is_active=True).values('permission__model__name', 'permission__name', 'checked', 'is_active')
            for p in user_permissions:
                model = p['permission__model__name'] 
                p_name = p['permission__name']
                p_checked = p['checked']
                p_isactive = p['is_active']
                if not model in permission_dict:
                    permission_dict.update({model : [{"permission_name":p_name, 'checked': p_checked, 'is_active':p_isactive}]})
                else:
                    permission_dict[model].append({"permission_name":p_name, 'checked': p_checked, 'is_active':p_isactive})
            permission_list = []
            for key, value in permission_dict.items():
                permission_list.append({'model_name': key, 'permissions':value})

            app_dict[app_name] = permission_list
            permissions.update(app_dict)
    except Exception as e:
        print("Error to get persmission =>", str(e))
    return permissions




class Base64ImageField(serializers.ImageField): 
    """ 
    A Django REST framework field for handling image-uploads through raw post data. 
    It uses base64 for encoding and decoding the contents of the file. 

    Heavily based on 
    https://github.com/tomchristie/django-rest-framework/pull/1268 

    Updated for Django REST framework 3. 
    """ 

    def to_internal_value(self, data): 
     from django.core.files.base import ContentFile 
     import base64 
     import six 
     import uuid 

     # Check if this is a base64 string 
     if isinstance(data, six.string_types): 
      # Check if the base64 string is in the "data:" format 
      if 'data:' in data and ';base64,' in data: 
       # Break out the header from the base64 content 
       header, data = data.split(';base64,') 

      # Try to decode the file. Return validation error if it fails. 
      try: 
       decoded_file = base64.b64decode(data) 
      except TypeError: 
       self.fail('invalid_image') 

      # Generate file name: 
      file_name = str(uuid.uuid4())[:12] # 12 characters are more than enough. 
      # Get the file name extension: 
      file_extension = self.get_file_extension(file_name, decoded_file) 

      complete_file_name = "%s.%s" % (file_name, file_extension,) 

      data = ContentFile(decoded_file, name=complete_file_name) 

     return super(Base64ImageField, self).to_internal_value(data) 

    def get_file_extension(self, file_name, decoded_file): 
     import imghdr 

     extension = imghdr.what(file_name, decoded_file) 
     extension = "jpg" if extension == "jpeg" else extension 

     return extension 


def update_multicotizador(user, urlname, org_name=None):
    #api_mul_url = 'https://' + "grupoasapi.multicotizador.com" + '/datavalidate/'
    api_mul_url = settings.MC_API_IP + 'datavalidate/'
    try:
        org = user.userinfo.org.urlname if user.userinfo.org else org_name
    except:
        org=org_name
    #if not org:
    #    raise Exception("Org no valida")
    params = {
        "user_username": user.username,
        "user_first_name": user.first_name,
        "user_last_name": user.last_name,
        "user_email": user.email,
        "user_password": user.password,
        "urlname": urlname,
        "org":org
    }
    try:
        a = requests.post(api_mul_url, params)
        return (a.json())

    except Exception as e:
        print("Exception", e)
        return (str(e))

    
    #return (json.loads(a.text))
