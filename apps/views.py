from django.shortcuts import render
 # -*- coding: utf-8 -*-
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.core.mail import EmailMessage,EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from organizations.models import Organization
from accounts.models import UserInfo
from .utils import update_beneficios_app, validate_saam_email

from dateutil import parser
from random import randint
from requests.auth import HTTPBasicAuth
from datetime import datetime

import json
import requests
import base64
from core.views import update_beneficios
from core.errors import get_error
from core.utils import get_app_permissions_front,  get_jwt_token, delete_token, update_multicotizador
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from datetime import datetime, timedelta
# Create your views here.


def f_intToBase64(a):
    a = base64.b64encode(bytes(str(a), encoding='utf-8'))
    return a

def f_base64ToInt(s):
    return int(base64.b64decode(s))

@csrf_exempt
@api_view(['GET'])
def activate_app_user(request,bs64):
    try:
        z = bs64.replace('\'','')[1:]
        user_info  = UserInfo.objects.get(activation_number = f_base64ToInt(z))
        user = user_info.user
        user.is_active = True
        user.save()
        user_info.activation_number = None
        user_info.save()
        return JsonResponse({'status':'Success', 'status_code':'200'})
    except Exception as e: 
        print(e)
        return JsonResponse({'status':'500', 'error': str(e) })

@csrf_exempt
@api_view(['GET'])
def activate_app_user_kalifa(request,bs64):
    try:
        z = bs64.replace('\'','')[1:]
        user_info  = UserInfo.objects.get(activation_number = f_base64ToInt(z))
        user = user_info.user
        user.is_active = True
        user.save()
        user_info.activation_number = None
        user_info.save()
        return HttpResponse(render_to_string('kalifa_ok.html', {}))
    except Exception as e: 
        return HttpResponse(render_to_string('kalifa_warning.html', {}))



@csrf_exempt
@api_view(['POST'])
def restart_password_app_user(request):
    bs64 = request.data['bs64']
    password = request.data['password']
    try:
        z = bs64.replace('\'','')[1:]
        user_info  = UserInfo.objects.get(activation_number = f_base64ToInt(z))
        user = user_info.user
        user.set_password(password)
        user.save()
        user_info.activation_number = None
        user_info.save()

        return JsonResponse({'status':'200'})
    except Exception as e: 
        print(e)
        return JsonResponse({'status':'500', 'error': str(e) })



@csrf_exempt
@api_view(['POST'])
def send_new_password(request):
    email = request.data['email']
    try:
        user = User.objects.get(email = email)
    except Exception as userget:
        return JsonResponse({'error':'El email ingresado no existe'})

    if user and user.is_active == False :
        return JsonResponse({'error':'El usuario no está activo'})        
    
    try:
        user_info = UserInfo.objects.get(user = user)    
    except Exception as userget:
        user_info =  UserInfo(user =user)
    subject = "Reestablecimiento de contraseña"

    while True:
        activation_number = int(random_username_generator(user.first_name).replace(user.first_name+'_',''))
        if not UserInfo.objects.filter(activation_number = activation_number).exists():
            user_info.activation_number = activation_number
            user_info.save()
            break


    encoded = f_intToBase64(user_info.activation_number)
    encoded = str(encoded).replace('\'','')

    link = settings.FORGET_PASSWORD_LINK + "%s" % str(encoded)
    print('--user--info',user_info.user.email,email)
    message=render_to_string("reset_password.html",{'username' : user.username,'link':link})
    email = EmailMultiAlternatives(subject, message, from_email=settings.EMAIL_HOST_USER, to=[str(user_info.user.email)])
    email.content_subtype="html"
    email.mixed_subtype = 'related'
    email.send()

    return JsonResponse({'status':'sent','success':True})
    #html = 'recover_password_email.html'
#
    ## requests.post('https://mail.mbservicios.com/mails/demo-request/', {
    #requests.post('http://localhost:8005/mails/demo-request/', {
    #    "email" : user_info.user.email,
    #    "name": "%s %s"%(user_info.user.first_name, user_info.user.last_name),
    #    "html": html,
    #    "link" : link,
    #    "subject": "Re-establecimiento de contraseña",
    #    "dias_de_prueba": 0
    #})
    #return Response(status = status.HTTP_202_ACCEPTED)
    


@csrf_exempt
@api_view(['POST'])
def resend_activation_email(request):
    email = request.data['email']
    org = request.POST.get('org', '')
    try:
        user = User.objects.get(email = email)
    except: 
        return JsonResponse({'error':'El email ingresado no existe'})

    if user and user.is_active:
        return JsonResponse({'error':'El usuario ya está activo'})        
    
    user_info = UserInfo.objects.get(user = user)
    active_email_user(user_info, org, request.build_absolute_uri().replace('resend-activation-email', ''))
    return JsonResponse({'status':'resent'})



@csrf_exempt
@api_view(['POST'])
def create_user(request):
    try:
        email = request.data['email']
        password = request.data['password']
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        org = request.POST.get('org', '')
    except: 
        return JsonResponse({'status':'400', 'error':'Falta informacion en la peticion email, password, first_name y last_name'})

    if not email or not password or not first_name or not last_name:
        return JsonResponse({'status':'400', 'error':'Falta informacion en la peticion email, password, first_name y last_name'})

    email = email.lower()
    first_name = first_name.replace(' ','_').lower()

    # if User.objects.filter(email = email).exists():
    #     return JsonResponse({'status':'400', 'error':'El email ya existe'})
    if User.objects.filter(email = email).exists():
        u = User.objects.only('id', 'is_active', 'last_login').get(email=email) 
        return JsonResponse({'status':'400', 'error':'El email ya existe', 'user': {'id': u.id, 'is_active': u.is_active, 'last_login': u.last_login}}) 
    
    user = random_username_generator(first_name)
    while User.objects.filter(username = user).exists():
        user = random_username_generator(first_name)
    user= User.objects.create_user(user,email,password)
    user.first_name = first_name
    user.last_name = last_name
    user.is_active = False
    user.save()
    user_info =  UserInfo(user =user)
    while True:
        activation_number = int(random_username_generator(first_name).replace(first_name+'_',''))
        if not UserInfo.objects.filter(activation_number = activation_number).exists():
            user_info.activation_number = activation_number
            user_info.save()
            break
    active_email_user(user_info, org, request.build_absolute_uri().replace('cas-create-user', ''))

    return JsonResponse({'status':'201','success':True, 'data':{'username':user.username}})


@csrf_exempt
@api_view(['POST'])
def app_us_login(request):
    username = request.POST.get('username','')
    password = request.POST.get('password','')
    org = request.POST.get('org','')

    x = username.find('@')
    if x>=0 : 
        try:
            user_email = User.objects.get(email = username)
            username = user_email.username
        except:
            return JsonResponse({'error': 'Usuario no existe, verifica tus credenciales'}, status=405)

    user = authenticate(
        username=username,
        password=request.POST.get('password','')
    )
    if user and user.is_active:
        token = update_beneficios_app(user, org)
        
        try:
            org_url= user.userinfo.org.urlname,
            org_name= user.userinfo.org.name,
            org_address= user.userinfo.org.address,
            org_logo = 'media/' +str(json.dumps(str(user.userinfo.org.logo))).replace("\"","")
        except:
            org_url= ''
            org_name= ''
            org_address= ''
            org_logo = ''
        try:
            ui = user.userinfo
        except:
            ui=None
        obj = {
            'username':user.username,
            'first_name':user.first_name,
            'last_name':user.last_name,
            'org_url': org_url,
            'org_name': org_name,
            'org_address': org_address,
            'org_logo' : org_logo,            
            'token': token,
            'phone' : user.userinfo.phone if ui else '',
            'rfc' : user.userinfo.rfc if ui else '',
            'second_last_name' : '' ,
            'birthdate' : user.userinfo.birthdate if ui else '',
            'gender' : user.userinfo.gender if ui else '',
            'email': user.email,
            'user': user.id
        }
        return JsonResponse(obj, status=200)
    else:
        return JsonResponse({'error': 'Usuario no existe, verifica tus credenciales'}, status=404)


@csrf_exempt
@api_view(['POST'])
def app_us_login_portal(request):
    username = request.POST.get('username','')
    password = request.POST.get('password','')
    org = request.POST.get('org','')

    x = username.find('@')
    avatar = ''
    try:
        if x>=0 : 
            try:
                user = User.objects.get(email = username)
                username = user.username
            except:
                return JsonResponse({'error': 'Usuario no existe, verifica tus credenciales'}, status=405)
            if user:
                Token.objects.filter(user=user).delete()

            token, created = Token.objects.get_or_create(user=user)
            
            if not created:
                token.created = datetime.now()
                token.save()
            jwt_json = {'token': token.key}
            
            if UserInfo.objects.filter(user=user).exists():
                user_info = UserInfo.objects.get(user=user)
                permissions = get_app_permissions_front(user_info.id)
                role = user_info.role
                app_list = user_info.user_profiles.filter(is_active=True).values_list('application__name', flat=True)
                apps_dict =  {"applications":list()}
                jwt_json.update(apps_dict)
                try:
                    avatar = user_info.avatar.name
                except:
                    avatar = ''
                if user_info.org:
                    try:
                        logo_mini = user_info.org.logo_mini.name
                    except:
                        logo_mini = ''


                    org = {
                        "id": user_info.org.id, 
                        "name":user_info.org.urlname, 
                        'urlname':user_info.org.urlname, 
                        'logo_mini':logo_mini
                    }
                    try:
                        jwt_json.update({"org": {"id":user_info.org.id, "name":user_info.org.urlname}})
                    except Exception as ers:
                        print('norrr',ers)
                        jwt_json.update({"org": {"id":None, "name":None}})
            else:        
                return Response(get_error('user_info_is_missing'), status=status.HTTP_404_NOT_FOUND)
            expiration_date =  (datetime.now() + timedelta(minutes=settings.TOKEN_DURATION)).strftime('%Y-%m-%d %H:%M:%S')
            jwt_json.update({'expiration_date': expiration_date})
            print(jwt_json)
            token_jwt = get_jwt_token(jwt_json)
            crud_permissions={
                'crear':True,
                'editar': True,
                'eliminar': True
            }
            update_beneficios(user, user_info)
            response = {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username':user.username,
                'superuser':user.is_superuser,
                'avatar':avatar,
                'staff':user.is_staff,
                'user_id': user.id,
                'org': org,
                'token_jwt': token_jwt,
                'permissions': permissions,
                'crud_permissions': crud_permissions,                
                'role': role,
                'cobranza_pendiente': user_info.org.cobranza_pendiente,
                'crear_usuarios_app': user_info.org.crear_usuarios_app
            }
            if apps_dict:
                response.update(apps_dict)
            delete_token(user.id) # elimina el token del mismo usuario en caso de existir en saam
            return Response(response, status=200)
        else:
            try:
                user = User.objects.get(username = username)
                username = user.username
            except:
                return JsonResponse({'error': 'Usuario no existe, verifica tus credenciales'}, status=405)
            print('user----',user,username,password)
            if user:
                Token.objects.filter(user=user).delete()

            token, created = Token.objects.get_or_create(user=user)
            
            if not created:
                token.created = datetime.now()
                token.save()
            jwt_json = {'token': token.key}
            
            if UserInfo.objects.filter(user=user).exists():
                user_info = UserInfo.objects.get(user=user)
                permissions = get_app_permissions_front(user_info.id)
                role = user_info.role
                app_list = user_info.user_profiles.filter(is_active=True).values_list('application__name', flat=True)
                apps_dict =  {"applications":list()}
                jwt_json.update(apps_dict)
                try:
                    avatar = user_info.avatar.name
                except:
                    avatar = ''
                if user_info.org:
                    try:
                        logo_mini = user_info.org.logo_mini.name
                    except:
                        logo_mini = ''


                    org = {
                        "id": user_info.org.id, 
                        "name":user_info.org.urlname, 
                        'urlname':user_info.org.urlname, 
                        'logo_mini':logo_mini
                    }
                    try:
                        jwt_json.update({"org": {"id":user_info.org.id, "name":user_info.org.urlname}})
                    except Exception as ers:
                        print('norrr',ers)
                        jwt_json.update({"org": {"id":None, "name":None}})
            else:        
                return Response(get_error('user_info_is_missing'), status=status.HTTP_404_NOT_FOUND)
            expiration_date =  (datetime.now() + timedelta(minutes=settings.TOKEN_DURATION)).strftime('%Y-%m-%d %H:%M:%S')
            jwt_json.update({'expiration_date': expiration_date})
            print(jwt_json)
            token_jwt = get_jwt_token(jwt_json)
            crud_permissions={
                'crear':True,
                'editar': True,
                'eliminar': True
            }
            update_beneficios(user, user_info)
            response = {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username':user.username,
                'superuser':user.is_superuser,
                'avatar':avatar,
                'staff':False,
                'user_id': user.id,
                'org': org,
                'token_jwt': token_jwt,
                'permissions': permissions,
                'crud_permissions': crud_permissions,                
                'role': role,
                'cobranza_pendiente': user_info.org.cobranza_pendiente,
                'crear_usuarios_app': user_info.org.crear_usuarios_app
            }
            if apps_dict:
                response.update(apps_dict)

            delete_token(user.id) # elimina el token del mismo usuario en caso de existir en saam
            return Response(response, status=200)
    except Exception as e:
        print("Exception  to SAAM autentication=>",str(e))
        return Response(get_error('invalid_user_password'), status=404)

def random_username_generator(first_name):
    #  lenght of string returned 9
    range_start = 10**(9-1)
    range_end = (10**9)-1
    if first_name:
        user = first_name + '_' + str(randint(range_start, range_end))
    else:
        user = 'usuario_' + str(randint(range_start, range_end))
    if User.objects.filter(username = user).exists():
        random_username_generator(first_name)
    else:
        return user



def active_email_user(user_info, org=None, host=None):

    subject = "Activación de usuario"
    encoded = f_intToBase64(user_info.activation_number)
    encoded = str(encoded).replace('\'','')
    link = settings.ACTIVATION_LINK_USER + "%s" % str(encoded)
    html = 'activation_email.html'
    if org == 'kalifa':
        link = host+ 'activate-user/kalifa/'+"%s" % str(encoded)
        html = 'kalifa_activate.html'
    #result = requests.post('https://mail.mbservicios.com/mails/demo-request/', {
    #requests.post('http://localhost:8005/mails/demo-request/', {
    #    "email" : user_info.user.email,
    #    "name": "%s %s"%(user_info.user.first_name, user_info.user.last_name),
    #    "html": html,
    #    "link" : link,
    #    "subject": "Activación de usuario APP móvil",
    #    "dias_de_prueba": 0
    #})
    #return Response(status = status.HTTP_202_ACCEPTED)
    message = render_to_string(html,{'username' : user_info.user.username,'link':link})
    email = EmailMultiAlternatives(subject, message, from_email=settings.EMAIL_HOST_USER, to=[str(user_info.user.email)])
    email.content_subtype="html"
    email.mixed_subtype = 'related'
    email.send()

@csrf_exempt
def login_bibis(request):
    email = request.POST.get('email')
    org =  request.POST.get('org', '')
    email_validated = validate_saam_email(email)
    if not email_validated['response']:
        return JsonResponse({'status':'500', 'error':'El email no forma parte de un certificado'})

    
    if User.objects.filter(email__iexact = email).exists():
        return JsonResponse({'status':'500', 'error':'El email ya existe'})
    username = random_username_generator(email_validated['first_name'])
    try:
        username = str(username).replace(' ','_')
    except Exception as err_username:
        print('________>>>',err_username)
        username = username
    while User.objects.filter(username = username).exists():
        username = random_username_generator(email_validated['first_name'])
    password = '123456'
    user= User.objects.create_user(username,email,password)
    user.set_password(password)

    user.first_name = email_validated['first_name']
    user.last_name = email_validated['last_name']
    user.is_active = False
    user.save()
    user_info =  UserInfo(user =user)
    while True:
        activation_number = int(random_username_generator(email_validated['first_name']).replace(email_validated['first_name']+'_',''))
        if not UserInfo.objects.filter(activation_number = activation_number).exists():
            user_info.activation_number = activation_number
            user_info.save()
            break
    active_email_bibis(request,user_info, password, org)
    return JsonResponse({'status':'201', 'data':{'username':user.username}})


def active_email_bibis(request, user_info, password, org=None):
    subject = "Activación de usuario"
    portal ='clientes'
    if org and org!='prevex':
        portal ='{}-clientes'.format(org)

    encoded = f_intToBase64(user_info.activation_number)
    encoded = str(encoded).replace('\'','')
    link = settings.ACTIVATION_LINK_USER+ "%s" % str(encoded)
    message=render_to_string("activation_email_bibis.html",{'username' : user_info.user.username,'link':link, 'password':password,'portal':portal})
    email = EmailMultiAlternatives(subject, message, from_email=settings.EMAIL_HOST_USER, to=[str(user_info.user.email)])
    email.content_subtype="html"
    email.mixed_subtype = 'related'
    activate_app_user(request,encoded)
    email.send()


def informacion_email_user_app(user_info, org=None, host=None, subject =None, mensaje = None, password = None, first = None, last = None,remitente=None, request = None):
    subject = subject if subject else "Informacion de usuario"
    encoded = f_intToBase64(user_info.activation_number)
    encoded = str(encoded).replace('\'','')
    link = settings.ACTIVATION_LINK_USER + "%s" % str(encoded)
    html = 'user_created.html'
    # remitente = remitente+' <'+str(remitente)+'>'
    from_email = remitente
    message = render_to_string(html,{'username' : user_info.user.username,'link':link,'mensaje': mensaje,'asunto':subject,'password':password,'first':first,'last':last,'email':user_info.user.email})
    # email = EmailMultiAlternatives(subject, message, from_email=from_email, to=[str(user_info.user.email)])
    # email = EmailMultiAlternatives(subject, message, from_email=settings.EMAIL_HOST_USER, to=[str('guadalupe.becerril@ixulabs.com')])
    email = EmailMultiAlternatives(subject, message, from_email=settings.EMAIL_HOST_USER, to=[str(user_info.user.email)])
    email.content_subtype="html"
    email.mixed_subtype = 'related'
    email.send()

def sendEmailUserAppCreated(user_info, org=None, host=None, subject =None, mensaje = None, password = None, first = None, last = None, request = None):
    org = Organization.objects.get(urlname=org)
    result = {
        'org': {
            'name': org.name, 
            'urlname': org.urlname, 
            'address': org.address, 
            'phone': org.phone, 
            'email': org.email, 
            'webpage': org.webpage, 
            'logo': org.logo.name,
            'banner': ''
        }
    }
    org_info = result['org']
    encoded = f_intToBase64(user_info.activation_number)
    encoded = str(encoded).replace('\'','')
    if request.user.email:
        remitente = "{} <{}>".format(org_info['name'], request.user.email)
    elif org_info['email']:
        remitente = "{} <{}>".format(org_info['name'], org_info['email'])
    else:
        remitente = "{} <no-reply@miurabox.com>".format(org_info['name'])
    # ---------------------------------------------
    data = {
        'subject': subject,
        'mensaje': mensaje,
        'username': user_info.user.username,
        'receiver':[user_info.user.email],
        # 'receiver':['guadalupe.becerril@ixulabs.com'],
        'remitente':remitente,
        'password':password,
        'first':user_info.user.first_name,
        'last':user_info.user.last_name,
        'cc':[],
        'org':org_info['urlname'],
        'b_header': '',
        'b_footer': '',
        'email':user_info.user.email
    }      
    try:
        url = settings.MAIL_SERVICE + "mails/send-email-userapp/"
        req = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'} )  
    except Exception as e:
        print('Error reminder =>', str(e))
    # -- -- -- -- --

@csrf_exempt
@api_view(['POST'])
def create_users_app(request):
    uss = request.data
    data_users = []
    checkEmail = request.data['checkEmail'] if 'checkEmail' in request.data else False
    subject = request.data['asunto'] if 'asunto' in request.data else 'Información de usuario creado para App'
    mensaje = request.data['mensaje'] if 'mensaje' in request.data else ' Su usuario ha sido'
    remitente = request.data['remitente'] if 'remitente' in request.data else ''    
    for y in request.data['data']:        
        try:
            email = y['CORREO']
            password = y['CONTRASENA']
            first_name = y['NOMBRE']
            last_name = y['APELLIDOS']
            org = request.GET.get('org', '')
        except: 
            return JsonResponse({'status':'400', 'error':'Falta información en la petición CORREO, CONTRASENA, NOMBRE y/o APELLIDOS'})

        if not email or not password or not first_name or not last_name:
            return JsonResponse({'status':'400', 'error':'Falta información en la petición email, password, first_name y last_name'})

        email = email.lower()
        email = email.strip()
        first_name = first_name.replace(' ','_').lower()

        if User.objects.filter(email = email).exists():
            return JsonResponse({'status':'400', 'error':'El email ya existe ' +str(y['CORREO'])})
        user_data ={
            'email': email,
            'password':password,
            'first_name':first_name,
            'last_name':last_name,
            'identifier': y['IDENTIFICADOR'] if 'IDENTIFICADOR' in y else '',
        }
        data_users.append(user_data)
    owner =User.objects.get(username = request.user)
    try:
        infoowner = UserInfo.objects.get(user = owner)
        name_org = infoowner.org.urlname
    except:
        infoowner = Organization.objects.get(pk =org)
        name_org = infoowner.urlname
    if data_users:
        for u in data_users:
            user = random_username_generator(u['first_name'])
            while User.objects.filter(username = user).exists():
                user = random_username_generator(u['first_name'])
            user= User.objects.create_user(user,u['email'],u['password'])
            user.first_name = (u['first_name']).upper()
            user.last_name = u['last_name'].upper()
            user.is_active = True
            user.save()
            user_info =  UserInfo(user =user)
            while True:
                activation_number = int(random_username_generator(u['first_name']).replace(u['first_name']+'_',''))
                if not UserInfo.objects.filter(activation_number = activation_number).exists():
                    user_info.activation_number = activation_number
                    user_info.identifier = u['identifier']
                    user_info.owner = owner
                    user_info.name_org = name_org
                    user_info.save()
                    break    
            if checkEmail ==True or checkEmail == 'True':
                checkSMTP = request.data['checkSMTP'] if 'checkSMTP' in request.data else False
                # if checkSMTP ==True or checkSMTP == 'True':
                informacion_email_user_app(user_info, name_org, request.build_absolute_uri().replace('cas-create-users-app', ''), subject, mensaje,password,user.first_name,user.last_name, remitente, request)
                # sendEmailUserAppCreated(user_info, name_org,request.build_absolute_uri().replace('cas-create-users-app', ''), subject, mensaje, password, user.first_name, user.last_name, request)
                # else:
                #     if remitente:
                #         informacion_email_user_app(user_info, name_org, request.build_absolute_uri().replace('cas-create-users-app', ''), subject, mensaje,password,user.first_name,user.last_name, remitente, request)
        
        return JsonResponse({'status':'200', 'error':'Los usuarios han sido creados'})
@csrf_exempt
@api_view(['POST'])
def create_user_app(request):
    checkEmail = request.data['checkEmail'] if 'checkEmail' in request.data else False
    try:
        email = request.data['email']
        password = request.data['password']
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        identifier = request.data['identifier']
        org = request.GET.get('org', '')
    except: 
        return JsonResponse({'status':'400', 'error':'Falta informacion en la peticion email, password, first_name y last_name'})

    if not email or not password or not first_name or not last_name:
        return JsonResponse({'status':'400', 'error':'Falta informacion en la peticion email, password, first_name y last_name'})

    email = email.lower()
    email = email.strip()
    first_name = first_name.replace(' ','_').lower()

    if User.objects.filter(email = email).exists():
        return JsonResponse({'status':'400', 'error':'El email ya existe'})
    
    user = random_username_generator(first_name)
    while User.objects.filter(username = user).exists():
        user = random_username_generator(first_name)
    user= User.objects.create_user(user,email,password)
    user.first_name = first_name.upper()
    user.last_name = last_name.upper()
    user.is_active = True
    user.save()
    identifier = identifier if identifier else ''
    owner =User.objects.get(username = request.user)
    try:
        infoowner = UserInfo.objects.get(user = owner)
        name_org = infoowner.org.urlname
    except:
        infoowner = Organization.objects.get(pk =org)
        name_org = infoowner.urlname

    user_info =  UserInfo(user =user)
    while True:
        activation_number = int(random_username_generator(first_name).replace(first_name+'_',''))
        if not UserInfo.objects.filter(activation_number = activation_number).exists():
            user_info.activation_number = activation_number
            user_info.identifier = identifier
            user_info.owner = owner
            user_info.name_org = name_org
            user_info.save()
            break
    subject = request.data['asunto'] if 'asunto' in request.data else 'Información de usuario creado para App'
    mensaje = request.data['mensaje'] if 'mensaje' in request.data else ' Su usuario ha sido'
    remitente = request.data['remitente'] if 'remitente' in request.data else ''
    if checkEmail ==True or checkEmail == 'True':
        checkSMTP = request.data['checkSMTP'] if 'checkSMTP' in request.data else False
        print('cheee',checkSMTP,checkEmail,remitente)
        informacion_email_user_app(user_info, name_org, request.build_absolute_uri().replace('cas-create-users-app', ''), subject, mensaje,password,user.first_name,user.last_name, remitente, request)
        # if checkSMTP ==True or checkSMTP == 'True':
        # sendEmailUserAppCreated(user_info, name_org,request.build_absolute_uri().replace('cas-create-users-app', ''), subject, mensaje, password, user.first_name, user.last_name, request)
        # else:
        #     if remitente:
                # informacion_email_user_app(user_info, name_org, request.build_absolute_uri().replace('cas-create-users-app', ''), subject, mensaje,password,user.first_name,user.last_name, remitente, request)

    return JsonResponse({'status':'201', 'data':{'username':user.username}})

# desactivar usuarioo app
@csrf_exempt
@api_view(['POST'])
def desactivate_user_app(request):
    username = request.POST.get('username','')
    password = request.POST.get('password','')
    org = request.POST.get('org','')

    x = username.find('@')
    if x>=0 : 
        try:
            user_email = User.objects.get(email = username)
            username = user_email.username
        except:
            return JsonResponse({'error': 'Usuario no existe, verifica tus credenciales'}, status=405)

    user = authenticate(
        username=username,
        password=request.POST.get('password','')
    )
    if user and user.is_active:
        try:
            Token.objects.filter(user=user).delete()
        except Exception as e:
            print('eror al borrar token usuer--',e)
        print('**desactivando usuario--')
        user.is_active =False
        user.save()
        userinfo = UserInfo.objects.get(user = user)
        if userinfo:
            userinfo.is_active=False
            userinfo.save()   
        obj = {
            'username':user.username,
            'user': user.id,
        }
        return JsonResponse({'status':'200', 'data': 'Usuario desactivado'})
    else:
        return JsonResponse({'error': 'Usuario no existe, verifica tus credenciales'}, status=404)
