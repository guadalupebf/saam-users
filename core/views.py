from django.contrib.auth.models import User
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .utils import get_jwt_token, delete_token, update_multicotizador
from .serializers import ApplicationSerializer, DemoRequestSerializer
from .models import Application, DemoRequest

from organizations.models import OrganizationApplication

from accounts.models import UserInfo, Profile
from accounts.tasks import get_jwt
from accounts.serializers import UserInfoAvatarSerializer, UserInfoSerializer
from core.utils import get_app_permissions, get_app_permissions_front
from core.errors import get_error

from datetime import datetime, timedelta
import requests
import json
from pdb import set_trace
from presigned_url import get_url_file


def update_beneficios(user, user_info):
    api_url = settings.BENEFICIOS_CONF['API_URL']

    params = {
        "user_username": user.username,
        "user_email": user.email,
        "org_name": user_info.org.name if user_info else '',
        "org_urlname": user_info.org.urlname if user_info else '',
        "user_first_name" : user.first_name,
        "user_last_name" : user.last_name,
    }
    print('¿¿¿¿¿¿¿¿¿¿¿¿¿¿¿¿¿¿',params)
    r = requests.post(api_url, params, verify=False)




class LoginCas(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
      
        from_email = False
        role = 0
        if '@' in request.data['username']:
            _user = User.objects.filter(email=request.data['username'])
            if _user.exists():
                # remember old state
                # if isinstance(request.data, QueryDict):
                auth_data = json.loads(json.dumps(request.data)) # <----- QueryDict expects string values
                  # сhange the values you want
                auth_data['username'] = _user[0].username

                
                request.POST._mutable = True # <----- mutable needs to be modified on POST and not on data
                request.data.update(auth_data)
                request.POST._mutable = False
                
                from_email = True

        try:
            serializer = self.serializer_class(data=request.data, context={'request':request})

            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            if not created:
                token.created = datetime.now()
                token.save()

            if user.is_superuser:
                org ='manager'
            else:
                try:
                    org = user.userinfo.org.urlname
                except Exception as e:
                    print('eror------',e,user.userinfo)
                    org = user.userinfo.org
                    print('eror------',org)
            token_jwt = get_jwt(user.id, org, None)

            try:
                role = user.userinfo.role
            except:
                role = 0
            headers = {
                'Content-Type': 'application/json' ,
                'Authorization': 'Bearer %s' % token_jwt
            }

            ui = UserInfo.objects.filter(user = user).first()

            response = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username':user.username,
                'email': user.email,
                'is_superuser':user.is_superuser,
                'is_staff':user.is_staff,
                'user_id': user.id,
                'token': token.pk,
                'role': role,
                'tutorial':  False,
                'org':{'id':0}

            }
            if not user.is_superuser:
                try:
                    response['org'] = {
                        'alias': user.userinfo.org.alias,
                        'id': user.userinfo.org.id,
                        'billiable': user.userinfo.org.billiable,
                        'crear_usuarios_app': ui.org.crear_usuarios_app
                    }
                except Exception as et:
                    print('---------',et)                    
                    response['org'] = {
                        'alias': user.userinfo.org.alias if user.userinfo.org else '',
                        'id': user.userinfo.org.id if user.userinfo.org else '',
                        'billiable': user.userinfo.org.billiable if  user.userinfo.org else '',
                        'crear_usuarios_app': ui.org.crear_usuarios_app if ui.org else ''
                    }
                response['avatar'] = UserInfoAvatarSerializer(user.userinfo, context = {'request': request}, many = False).data
            if UserInfo.objects.filter(user=user).exists():
                response['userinfo'] = UserInfoSerializer(user.userinfo, context = {'request': request}, many = False).data
            return Response(response, status=200)
        except Exception as e:
            print("Exception  to cas autentication=>",str(e))
            return Response("Usuario y/o contraseña invalidos" + str(e), status=404)


class LoginSaam(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        
        try:
            org = ''
            permissions = ''
            apps_dict = None
            role = None
            serializer = self.serializer_class(data=request.data, context={'request':request})
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            isLoginLite=False
            if 'lite' in request.data:
                isLoginLite=request.data['lite']
            if user:
                Token.objects.filter(user=user).delete()
                # print('user--------',user,UserInfo.objects.filter(user=user)[0].org.urlname)
                # if UserInfo.objects.filter(user=user).exists():
                #     if UserInfo.objects.filter(user=user)[0].org.urlname =='pruebas':
                #         print('users------',Token.objects.filter(user=user))
                # else:
                #     Token.objects.filter(user=user).delete()

            token, created = Token.objects.get_or_create(user=user)
            if not created:
                token.created = datetime.now()
                token.save()
            jwt_json = {'token': token.key}
            
            if UserInfo.objects.filter(user=user).exists():
                user_info = UserInfo.objects.get(user=user)
                if isLoginLite:
                    # Si el usuario NO es lite y la organización NO es 'pruebas'
                    if not user_info.is_user_lite and request.data.get('org') != 'pruebas':
                        Token.objects.filter(user=user).delete()
                        return Response(get_error('user_notpermitted'), status=status.HTTP_404_NOT_FOUND)

                elif user_info.is_user_lite:
                    # Si intenta login normal, pero es lite => bloquear
                    print('LoginLite DESACTIVADO, pero usuario es lite:', user_info.is_user_lite)
                    Token.objects.filter(user=user).delete()
                    return Response(get_error('user_notpermitted'), status=status.HTTP_404_NOT_FOUND)
                else:
                    print('normal')
                # if isLoginLite:
                #     print('iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii',isLoginLite,user_info.is_user_lite,request.data['org'])
                #     if not user_info.is_user_lite or 'org' in request.data and request.data['org'] !='pruebas':
                #         Token.objects.filter(user=user).delete()
                #         return Response(get_error('user_notpermitted'), status=status.HTTP_404_NOT_FOUND) 
                # elif user_info.is_user_lite:
                #     print('iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii',isLoginLite,user_info.is_user_lite)
                #     Token.objects.filter(user=user).delete()
                #     return Response(get_error('user_notpermitted'), status=status.HTTP_404_NOT_FOUND) 
                permissions = get_app_permissions_front(user_info.id)
                role = user_info.role
                app_list = user_info.user_profiles.filter(is_active=True).values_list('application__name', flat=True)
                apps_dict =  {"applications":list()}
                jwt_json.update(apps_dict)
                if user_info.org:
                    if not 'org' in request.data or user_info.org.urlname != request.data['org']:
                        return Response(get_error('invalid_org'), status=status.HTTP_400_BAD_REQUEST)
                        # talvez seria mejor manejar un raise Exception
                    try:
                        # logo_mini = user_info.org.logo_mini.name
                        logo_mini = get_url_file(user_info.org.logo_mini) 
                    except Exception as e:
                        logo_mini = ''


                    org = {
                        "id": user_info.org.id, 
                        "name":user_info.org.urlname, 
                        'urlname':user_info.org.urlname, 
                        'logo_mini':logo_mini,
                        "whatsappweb":user_info.org.whatsappweb,
                        "phone_mensajeria":user_info.org.phone_mensajeria, 
                        "phone_sms":user_info.org.phone_sms,
                    }
                    org_apps = OrganizationApplication.objects.filter(organization=user_info.org)
                    if org_apps.exists():
                        token_jwt = get_jwt(user.id, user_info.org, None)
                        headers = {
                            'Content-Type': 'application/json' ,
                            'Authorization': 'Bearer %s' % token_jwt
                        }
                        try:
                            if user_info.org.billiable:
                                response= requests.get(settings.PAYMENT_API_IP + 'planes/suscripciones-cliente/'+ user_info.org.urlname, headers = headers)
                                if response.status_code == 200:
                                    request_ = response.json()
                                else:
                                    request_ = [{}]

                        except Exception as e:
                            print("Error al obener subscripciones =>", str(e))

                        for oa in org_apps:
                            if user_info.org.billiable:
                                app_plan_active = False  
                                for r in request_:
                                    if 'status' in r and r['status'] == 'active':
                                        for _app in r['plan']['apps']:
                                            if _app['name'].lower() == oa.application.name.lower():
                                                app_plan_active = True


                                org['active_{}'.format(oa.application.name.lower())] = True if oa.is_active and app_plan_active else False
                            else:
                                org['active_{}'.format(oa.application.name.lower())] = oa.is_active
                    jwt_json.update({"org": {"id":user_info.org.id, "name":user_info.org.urlname}})
            else:        
                return Response(get_error('user_info_is_missing'), status=status.HTTP_404_NOT_FOUND)
            expiration_date =  (datetime.now() + timedelta(minutes=settings.TOKEN_DURATION)).strftime('%Y-%m-%d %H:%M:%S')
            jwt_json.update({'expiration_date': expiration_date})
            print(jwt_json)
            print('token**********',token)
            print('**********',user)
            token_jwt = get_jwt_token(jwt_json)
            print('ooooooooooooooooo',token_jwt)
            crud_permissions={
                'crear':True,
                'editar': True,
                'eliminar': True
            }
            update_beneficios(user, user_info)
            print('then updatebeneficions',user,user_info)
            response = {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username':user.username,
                'superuser':user.is_superuser,
                'staff':user.is_staff,
                #'staff':False,
                'user_id': user.id,
                'org': org,
                'token_jwt': token_jwt,
                'permissions': permissions,
                'crud_permissions': crud_permissions,                
                'role': role,
                'cobranza_pendiente': user_info.org.cobranza_pendiente,
                'crear_usuarios_app': user_info.org.crear_usuarios_app,
                'another_tasks': user_info.another_tasks
            }

            user_info.ultimo_acceso_saam = datetime.now()
            user_info.save()

            if apps_dict:
                response.update(apps_dict)

            delete_token(user.id) # elimina el token del mismo usuario en caso de existir en saam
            return Response(response, status=200)
        except Exception as e:
            print("Exception  to SAAM autentication=>",str(e))
            return Response(get_error('invalid_user_password'), status=404)

class LoginMC(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            urlname = request.POST.get('urlname')
            org= request.POST.get('org', '')

            try:
                serializer = self.serializer_class(data=request.data, context={'request':request})
                serializer.is_valid(raise_exception=True)
                user = serializer.validated_data['user']
                #Token.objects.filter(user=user).delete()
                token_cas, created = Token.objects.get_or_create(user=user)
                if not created:
                    token_cas.created = datetime.now()
                    token_cas.save()
            except Exception as e:
                return Response(get_error('invalid_user_password'), status=404)
            if user:
                #if org == 'kalifa':
                # if org :
                #     token = update_multicotizador(user,urlname, org)
                # else:
                #     token = update_multicotizador(user,urlname)
                role= '4'
                try:
                    role = user.userinfo.role
                except:
                    pass

                response = {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username':user.username,
                    'email': user.email,
                    'is_superuser':user.is_superuser,
                    'user_id': user.id,
                    'rol':role,
                    'token': get_jwt_token({'token':token_cas.key}),
                    'mc':urlname,
                    # 'caratula': token['caratula'] if token and 'caratula' in token else ''
                    'caratula': ''
                }
                return Response(response, status=200)
            else:
                return Response(get_error('invalid_user_password'), status=404)
        except Exception as e:
            return Response(str(e), status=404)


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = None

    def get_queryset(self):
        return Application.objects.all().order_by('-id')


class DemoRequestViewSet(viewsets.ModelViewSet):
    serializer_class = DemoRequestSerializer
    pagination_class = None

    def get_queryset(self):
        return DemoRequest.objects.all()
    

@api_view(['POST'])
def test_request(request):
    email = request.data['email']
    name = request.data['name']
    telefono = request.data['telefono']
    html = 'demo_auto_activation_email.html'
    if DemoRequest.objects.filter(email = email.lower()).exists():
        raise ValidationError(get_error('record_already_exist'))
    demo = DemoRequest.objects.create(
        name = name,
        email = email.lower(),
        telefono = telefono
    )
    link = settings.ACTIVATION_LINK + str(demo.id)


    requests.post(settings.MAIL_SERVICE+'mails/demo-request-reminder-register/', {
        "email" : demo.email,
        "name": demo.name,
        "phone": demo.telefono,
        "html": 'saam_cliente_registrado_correo_1er_dia.html',
        "subject": "¿Quieres mejorar tu productividad? ¡Te decimos cómo!"
    })

    requests.post(settings.MAIL_SERVICE + 'mails/demo-request/', {
        "email" : email,
        "name": name,
        "telefono": telefono,
        "html": html,
        "link" : link,
        "subject": "Solicitud de Presentación SAAM",
        "dias_de_prueba": 7
    })

    html = 'demo_auto_activation_email_request.html'

    requests.post(settings.MAIL_SERVICE+'mails/demo-request-admin/', {
        "email" : email,
        "name": name,
        "phone": telefono,
        "html": html,
        "link" : link,
        "subject": "Solicitud de cliente para presentación SAAM",
        "dias_de_prueba": 7
    })


    return Response(status = status.HTTP_202_ACCEPTED)



@api_view(['POST'])
def email_request_exist(request):
    dr = DemoRequest.objects.filter(email = request.data['email'].lower()).exists()
    users = User.objects.filter(email = request.data['email'].lower()).exists()
    return Response( dr or users, status = status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def valid_token(request):
    return Response({'valid': True}, status = status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_user_info(request):
    response = {}
    permissions = {}
    org = ''

    try:
        user = request.user    
        if UserInfo.objects.filter(user=user).exists():
            user_info = UserInfo.objects.get(user=user)
            permissions = get_app_permissions(user_info.id)
            another_tasks = user_info.another_tasks
            org = user_info.org.urlname if user_info.org else ''
        else:
            another_tasks = False

        response = {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username':user.username,
            'is_superuser':user.is_superuser,
            'is_staff':user.is_staff,
            'user_id': user.id,
            'permissions': permissions,
            'another_tasks': another_tasks,
            'org':org
        }
    except Exception as e:
        print(str(e))
        return Response(response, status = status.HTTP_400_BAD_REQUEST)
    return Response(response, status = status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_user_info_ms(request):
    response = {}
    permissions = {}
    org = ''

    try:
        user = request.user    
        if UserInfo.objects.filter(user=user).exists():
            user_info = UserInfo.objects.get(user=user)
            permissions = get_app_permissions(user_info.id)
            another_tasks = user_info.another_tasks
            org = user_info.org.urlname
        else:
            another_tasks = False

        response = {
            'email': user.email,
            'username':user.username,
            'is_superuser':user.is_superuser,
            'is_staff':user.is_staff,
            'user_id': user.id,
            'org':org
        }
    except Exception as e:
        print(str(e))
        return Response(response, status = status.HTTP_400_BAD_REQUEST)
    return Response(response, status = status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((AllowAny, ))
def delete_session_saamlite(request, *args, **kwargs):   
    response = {}
    try:
        user = User.objects.get(username = request.data['username'])
        token= Token.objects.filter(user=user)  
        if UserInfo.objects.filter(user=user).exists():
            user_info = UserInfo.objects.filter(user=user,org__urlname=request.data['org']) .exists()
            if not user_info:
                return Response(get_error('user_info_is_missing'), status=status.HTTP_404_NOT_FOUND)           
            if user:
                token_delete = Token.objects.filter(user=user).delete()
        else:        
            return Response(get_error('user_info_is_missing'), status=status.HTTP_404_NOT_FOUND)

        k = delete_token(user.id) # elimina el token del mismo usuario en caso de existir en saam
        return Response(k, status=200)
    except Exception as e:
        print(str(e))
        return Response(response, status = status.HTTP_400_BAD_REQUEST)
