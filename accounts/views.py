from django.http import HttpResponse
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.urls import reverse
from core.models import Application

from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, MethodNotAllowed, ValidationError, APIException
from saam.tasks import get_perfiles_usuario_restringido, guardar_perfil_usuario_restringidoname_saam

from .models import ModelPermission, UserInfo, Profile, Permission, UserPermission
from organizations.models import Organization, OrganizationApplication

from .serializers import (ModelPermissionSerializer, UserInfoSerializer, 
    ProfileSerializer, PermissionSerializer, UserSerializer, UserAppInfoSerializer,
    UserPermissionSerializer, UserInfoAvatarSerializer, VendorSerializer)

from core.permissions import IsOrgMember, IsOrgMemberChar
from core.errors import get_error
from core.utils import get_app_permissions

from .tasks import ( get_aseguradoras_from_saam_api, 
    get_ramos_from_saam_api, get_subramos_from_saam_api, 
    get_claves_general_from_saam_api, create_clave_saam_api,
    get_comisiones_from_saam_api, create_comision_saam_api, get_aseguradoras_from_saam_api_perfil
    )

from django.db import transaction, IntegrityError
from accounts.tasks import get_jwt, settings
import requests
from operator import __or__ as OR
import operator

from operator import and_
from datetime import datetime, timedelta
from functools import reduce

from apps.views import authenticate
from django.http import JsonResponse, Http404
from presigned_url import get_url_file

class ModelPermissionViewSet(viewsets.ModelViewSet):
    serializer_class = ModelPermissionSerializer
    permission_classes = (IsAuthenticated, )
    def get_queryset(self):
        if 'application' in self.request.GET:
            return ModelPermission.objects.filter(application__name=self.request.GET.get('application'))
        return ModelPermission.objects.all()
    
class PermissionViewSet(viewsets.ModelViewSet):
    serializer_class = PermissionSerializer
    permission_classes = (IsAuthenticated, )
    def get_queryset(self):
        query = Q() 
        if 'application' in self.request.GET:
            query = Q(model__application__name=self.request.GET.get('application'))
        if 'model'in self.request.GET:
            query = query & Q(model__name=self.request.GET.get('model'))
        if query:
            return Permission.objects.filter(query).order_by('-id')
        
        return Permission.objects.all()

class UserPermissionViewSet(viewsets.ModelViewSet):
    serializer_class = UserPermissionSerializer
    permission_classes = (IsAuthenticated, )
    def get_queryset(self):
        if 'profile' in self.request.GET:
            return UserPermission.objects.filter(profile__descr=self.request.GET.get('profile')).order_by('-id')
        return UserPermission.objects.all().order_by('-id')

    
class UserInfoViewSet(viewsets.ModelViewSet):
    serializer_class = UserInfoSerializer
    permission_classes = (IsAuthenticated, )
    def get_queryset(self):
        return UserInfo.objects.all().order_by('-id')


class UserInfoAvatarViewSet(viewsets.ModelViewSet):
    serializer_class = UserInfoAvatarSerializer
    permission_classes = (IsAuthenticated, )
    def get_queryset(self):
        return UserInfo.objects.all().order_by('-id')

    # def partial_update(self, request, pk=None):
    #     print(request.PATCH)
    #     queryset = UserInfo.objects.all()
    #     cf = get_object_or_404(queryset, pk=pk)
       
    #     serializer = UserInfoSerializer(cf, context={'request': request}, data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data)
    

class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated, IsOrgMember )
    pagination_class = None
    
    def get_queryset(self):
        if int(self.request.GET.get('type_profile',0)) in [0,4]:            
            if int(self.request.GET.get('type_profile',0)) == 4:
                return Profile.objects.filter(
                    org = Organization.objects.get(pk=self.request.GET.get('org')),
                    type_profile = 2 if int(self.request.GET.get('type_profile',0)) == 4 else 1
                ).order_by('-id')
            else:
                return Profile.objects.filter(
                    org = Organization.objects.get(pk=self.request.GET.get('org'))
                ).order_by('-id')
        else:
            if int(self.request.GET.get('type_profile',0)) == 4:
                return Profile.objects.filter(
                    org = Organization.objects.get(pk=self.request.GET.get('org')),
                    type_profile = 2 if int(self.request.GET.get('type_profile',0)) == 4 else 1
                ).order_by('-id')
            else:               
                return Profile.objects.filter(
                    org = Organization.objects.get(pk=self.request.GET.get('org')),
                    type_profile = 2 if int(self.request.GET.get('type_profile',0)) == 2 else 1
                ).order_by('-id')

    def perform_create(self, serializer):
        if not self.request.user.is_superuser and self.request.user.userinfo.role not in [0,1]:
            raise PermissionDenied(get_error('permission_denied'))

        if self.request.user.is_staff and not self.request.user.is_superuser:
            obj = serializer.save(org = self.request.user.userinfo.org)
        elif self.request.GET.get('org', 0) != 0:
            obj = serializer.save(org = Organization.objects.get(pk = int(self.request.GET.get('org'))))   
        else:
            raise ValidationError(get_error('org_does_not_included')) 



#class ProfileApplicationViewSet(viewsets.ModelViewSet):
#    serializer_class = ProfileApplicationSerializer
#    permission_classes = (IsAuthenticated, )
#    def get_queryset(self):
#        return ProfileApplication.objects.all().order_by('-id')
#    
    
class UserInactiveViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsOrgMember)

    def get_queryset(self):
        if self.request.user.is_superuser:
            org = self.request.GET.get('org',0)
            if org != 0:
                return User.objects.filter(is_active=False, userinfo__org=org).order_by('-id')
            return User.objects.filter(is_active=False, is_superuser = True).order_by('-id')
        else:
            if UserInfo.objects.filter(user=self.request.user).exists():
                return User.objects.filter(is_active=False, userinfo__org=self.request.user.userinfo.org).order_by('-id')
            else:
                return []



class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsOrgMember)

    
    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                if not self.request.user.is_superuser and self.request.user.userinfo.role not in [0,1]:
                    raise PermissionDenied(get_error('permission_denied'))
               
                # verificar el numero de usuarios de acuerdo al plan que tienen el cliente
                if self.request.GET.get('org') and self.request.user.is_superuser:
                    org = Organization.objects.get(id = self.request.GET.get('org'))
                elif self.request.GET.get('org'):
                    org = self.request.user.userinfo.org
                else: 
                    org = ''
                if org and org.billiable:
                    token_jwt = get_jwt(self.request.user.id, None, None)
                    headers = {
                        'Content-Type': 'application/json' ,
                        'Authorization': 'Bearer %s' % token_jwt
                    }

                    if org.billiable: 
                        r = requests.get(settings.PAYMENT_API_IP + 'planes/suscripciones-cliente/'+ org.urlname, headers = headers)
                        if r.status_code == 200:
                            r = r.json()
                        else:
                            r = {
                                'plan': {
                                    'users_number':3
                                }
                            }

                        if self.request.user.is_superuser:
                            numero_usuarios_creados = len(UserInfo.objects.filter(org = org))
                        else:
                            numero_usuarios_creados = len(UserInfo.objects.filter(org = org))
                        numero_usuarios_plan = 0

                        for plan in r:
                            if 'status' in plan and plan['status'] == 'active':
                                if 'plan' in plan:
                                    numero_usuarios_plan = plan['plan']['users_number']
                        print(numero_usuarios_plan, numero_usuarios_creados)
                        if numero_usuarios_creados >= numero_usuarios_plan:
                            raise APIException(get_error('max_user_number_reached'))

                # crear el usuario
                obj = serializer.save()
                password =self.request.data['password']
                obj.set_password(password)
                obj.save()
        except IntegrityError as e:
            raise APIException(e)
        except Exception as e:
            raise APIException(e)
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['saam_exists'] = getattr(self, '_saam_exists', False)
        ctx['saam_user_pair'] = getattr(self, '_saam_user_pair', None)  # [user_id, userinfo_id]
        return ctx



    def get_queryset(self):
        if self.request.user.is_superuser:
            org = self.request.GET.get('org',0)
            if org != 0:
                return User.objects.filter(is_active = True, userinfo__org=org).order_by('-id')
            return User.objects.filter(is_active = True, is_superuser = True).order_by('-id')
        else:
            if UserInfo.objects.filter(user=self.request.user).exists():
                return User.objects.filter(is_active = True, userinfo__org=self.request.user.userinfo.org).order_by('-id')
            else:
                return []


    def partial_update(self, request, pk=None):
        queryset = User.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        if not self.request.user.is_superuser and self.request.user.userinfo.role not in [0,1]:
            if cf.id != self.request.user.id:
                raise PermissionDenied(get_error('permission_denied'))
        serializer = UserSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_instance = User.objects.get(id = cf.id)
        
        if 'password' in request.data and request.data['password'] and len(request.data['password']) > 0:
            cf.set_password(request.data['password'])
            cf.save()
        # if not request.user.is_superuser:
        if 'profile' in request.data:
            profile = Profile.objects.get(pk = request.data['profile'])
            profile_to_empty = Profile.objects.filter(application = profile.application, user_info = cf.userinfo)
            for p in profile_to_empty:
                p.user_info.remove(cf.userinfo)
            profile.user_info.add(cf.userinfo)
        if 'userinfo' in request.data and request.data['userinfo']['id']:
            nc = True
            if 'notificarContabilidad' in request.data['userinfo']:
                nc = request.data['userinfo'].pop('notificarContabilidad')
            UserInfo.objects.filter(pk = request.data['userinfo']['id']).update(**request.data['userinfo'])
            request.data['userinfo']['notificarContabilidad'] = nc
            request.data['userinfo']
        if not user_instance.is_active:
            UserInfo.objects.filter(user = user_instance).update(manage_profile=False)
            print('Sin acceso')
        return Response(serializer.data)


class VendorView(viewsets.ReadOnlyModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = (IsAuthenticated, IsOrgMemberChar)
    pagination_class = None

    def partial_update(self, request, pk=None):
        queryset = User.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        if not self.request.user.is_superuser and self.request.user.userinfo.role not in [0,1]:
            if cf.id != self.request.user.id:
                raise PermissionDenied(get_error('permission_denied'))
        serializer = UserSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if 'password' in request.data and request.data['password'] and len(request.data['password']) > 0:
            cf.set_password(request.data['password'])
            cf.save()
        # if not request.user.is_superuser:
        if 'profile' in request.data:
            profile = Profile.objects.get(pk = request.data['profile'])
            profile_to_empty = Profile.objects.filter(application = profile.application, user_info = cf.userinfo)
            for p in profile_to_empty:
                p.user_info.remove(cf.userinfo)
            profile.user_info.add(cf.userinfo)
        if 'userinfo' in request.data and request.data['userinfo']['id']:
            UserInfo.objects.filter(pk = request.data['userinfo']['id']).update(**request.data['userinfo'])
        return Response(serializer.data)


    def destroy(self, request, *args, **kwargs):
        if not self.request.is_superuser:
            raise PermissionDenied(get_error('permission_denied'))
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
        except:
            return Response({'Response': 'Ha ocurrido un error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'Response': 'El elemento ha sido destruido'}, status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        org = self.request.GET.get('org',0)
        if org != 0:
            return User.objects.filter(is_superuser=False, userinfo__org__urlname=org, userinfo__is_vendedor=True).order_by('-id')
        else: 
            return []

class UsuarioView(viewsets.ReadOnlyModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = (IsAuthenticated, IsOrgMemberChar)
    pagination_class = None

    def get_queryset(self,*args, **kwargs):
        org = self.request.GET.get('org',0)
        is_delivery= self.request.data.get('is_delivery', False)
        is_active = self.request.data.get('is_active', True)
        is_superuser = self.request.data.get('is_superuser', False)
        id = self.request.data.get('id', False)
        name = self.request.data.get('name', False)
        if org != 0:
            if id:
                return User.objects.filter(id=id, userinfo__org__urlname=org)
            elif name:
                return User.objects.filter(username=name, userinfo__org__urlname=org)
            else:
                return User.objects.filter(is_superuser=is_superuser,is_active=is_active, userinfo__org__urlname=org, userinfo__is_delivery=is_delivery).order_by('first_name')
        else: 
            return []



@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def exist_email(request):
    user_id = request.data['user_id']
    if not user_id:
        return Response(User.objects.filter(email = request.data['email']).exists())
    else:
        return Response(User.objects.exclude(id = user_id).filter(email = request.data['email']).exists())


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated, ))
def has_users(request):
    profile = Profile.objects.get(id = request.data['profile_id'])
    ui = UserInfo.objects.filter(user_profiles = profile)
    return Response(ui.exists())


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def exist_username(self, username):
    return Response(User.objects.filter(username = username).exists())

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def exist_first_and_lastname(request, first_name, last_name,user_id):
    org = request.GET.get('org')  # recoge el ?org=2
    org_name=Organization.objects.get(id=org)
    if user_id in (None, 'null'):
        usuario_act = None
    else:
        usuario_act = User.objects.get(pk=int(user_id))
        return Response(False)
    request_api_saam = settings.SAAM_API_IP+"check-user/"         # URL de la API externa
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "org": org_name.urlname
    }
    # Opción A: POST con JSON
    resp = requests.post(request_api_saam, json=payload, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    print('data********+',data)
    return Response(data.get("existe", False))

@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def exist_profile_name(request):
    profile_id = request.data['profile_id']
    if not profile_id:
        return Response(Profile.objects.filter(
            name__iexact = request.data['profile_name'], 
            org = Organization.objects.get(
                id = request.GET.get('org'))
            ).exists())
    else:
        return Response(Profile.objects.filter(
            name__iexact = request.data['profile_name'], 
            org = Organization.objects.get(
                id = request.GET.get('org'))
            ).exclude(id = profile_id).exists())


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_permissions(request, appname=None):
    user_info =  request.user.userinfo 
    permissions = get_app_permissions(user_info.id, appname)
    return Response(permissions, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def aseguradoras(request):
    org_name = None
    if request.GET.get('org',None):
        org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
    # task =  get_claves_from_saam_api.delay(request.user.id, org_name,)
    aseguradoras = get_aseguradoras_from_saam_api(request.user.id, org_name,)
    return Response(aseguradoras, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def aseguradorasperfil(request):
    org_name = None
    if request.GET.get('org',None):
        org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
    # task =  get_claves_from_saam_api.delay(request.user.id, org_name,)
    aseguradoras = get_aseguradoras_from_saam_api_perfil(request.user.id, org_name,)
    return Response(aseguradoras, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def ramos(request, aseguradora_id):
    org_name = None
    if request.GET.get('org',None):
        org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
    # task =  get_claves_from_saam_api.delay(request.user.id, org_name,)
    ramos = get_ramos_from_saam_api(request.user.id, aseguradora_id, org_name)
    return Response(ramos, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def subramos(request, aseguradora_id, ramo_id):
    org_name = None
    if request.GET.get('org',None):
        org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
    # task =  get_claves_from_saam_api.delay(request.user.id, org_name,)
    subramos =  get_subramos_from_saam_api(request.user.id, aseguradora_id, ramo_id, org_name)
    return Response(subramos, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def clave_saam(request):
    org = request.GET.get('org',None)
    data = request.data
    if org:
        org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
    else:
        raise PermissionDenied(get_error('org_does_not_included'))
    # task =  get_claves_from_saam_api.delay(request.user.id, org_name,)
    claves =  create_clave_saam_api(request.user.id, data, org_name)
    print(claves)
    return Response(claves, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def crear_comision(request):
    org = request.GET.get('org',None)
    data = request.data
    if org:
        org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
    else:
        raise PermissionDenied(get_error('org_does_not_included'))
    # task =  get_claves_from_saam_api.delay(request.user.id, org_name,)
    claves =  create_comision_saam_api(request.user.id, data, org_name)
    print(claves)
    return Response(claves, status=status.HTTP_200_OK)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated, ))
def claves_general(request):
    org_name =  request.GET.get('org',None)
    data = request.data
    if request.GET.get('org',None):
        org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
    # task =  get_claves_from_saam_api.delay(request.user.id, org_name,)
    claves =  get_claves_general_from_saam_api(request.user.id, data, org_name)
    if claves or len(claves) == 0:
        return Response(claves, status=status.HTTP_200_OK)
    else:
        return Response({'Error':'Hubo un error al cargar las claves'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def comisiones_general(request, clave_id):
    org_name =  request.GET.get('org',None)
    data = request.data
    if request.GET.get('org',None):
        org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
    # task =  get_claves_from_saam_api.delay(request.user.id, org_name,)
    comisiones =  get_comisiones_from_saam_api(request.user.id, clave_id, org_name)
    if comisiones or len(comisiones) == 0:
        return Response(comisiones, status=status.HTTP_200_OK)
    else:
        return Response({'Error':'Hubo un error al cargar las comisiones'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['GET'])
def get_user_picture(request, username):
    try:
        ui = UserInfo.objects.get(user__username = username)
    except User.DoesNotExist:
        return Response({'error': 'El usuario no existe'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        avatar =get_url_file(ui.avatar)  
    except:
        avatar =get_url_file(ui.avatar)  
        

    return Response({'url':avatar if ui.avatar else 'https://miurabox.s3.amazonaws.com/cas/noavatar.png'}, status=status.HTTP_200_OK)

import json
import os
import pandas as pd
from django.db.models import Prefetch

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def report_users(request):
    orgname = request.GET.get('org', None)

    user_info_query = UserInfo.objects.select_related('user', 'org').exclude(name_org__isnull=False)

    if orgname and int(orgname) != 0:
        org = Organization.objects.get(pk=orgname)
        urlname = org.urlname
        user_info_query = user_info_query.filter(org=org)
    else:
        urlname = 'all'

    data_rows = []

    usernames = []

    for ui in user_info_query:
        user_permission = UserPermission.objects.filter(profile__user_info__user=ui.user).select_related('profile').first()
        profile_name = user_permission.profile.name if user_permission else ''

        org_app_active = OrganizationApplication.objects.filter(organization=ui.org, application__name='SAAM').first()
        org_app_active_status = org_app_active.is_active if org_app_active else ''

        usernames.append(ui.user.username)

        data_rows.append({
            'Nombre': ui.user.first_name,
            'Apellido': ui.user.last_name,
            'Nombre de usuario': ui.user.username,
            'ID': ui.user.id,
            'Correo': ui.user.email,
            'Teléfono': ui.phone,
            'Género': ui.get_gender_display(),
            'Fecha de nacimiento': ui.birthdate,
            'Acceso': ui.get_manage_profile_display(),
            'Fecha de creación': ui.user.date_joined.strftime("%d/%m/%Y") if ui.user.date_joined else '',
            'Fecha último acceso SAAM': ui.ultimo_acceso_saam.strftime("%d/%m/%Y: %H:%M:%S") if ui.ultimo_acceso_saam else '',
            'Observaciones Organización': ui.org.observations if ui.org and ui.org.observations else '',
            'RFC': ui.rfc,
            'Rol': ui.get_role_display(),
            'Perfil': profile_name,
            'Org': ui.org.urlname if ui.org else '',
            'Organización activa': org_app_active_status,
            'Activo': ui.user.is_active,
        })

    token_jwt = get_jwt(request.user.id, urlname)

    payload = {"Authorization": "Bearer {}".format(token_jwt), 'usernames': usernames}
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token_jwt)}

    r = requests.post(settings.SAAM_API_IP + 'perfil-usuario-restringido-array-cas/', json.dumps(payload), headers=headers, verify=False)

    perfill_restringido_resp = r.json() if r.status_code == 200 else []

    for i, username in enumerate(usernames):
        restr_profile = perfill_restringido_resp[i] if i < len(perfill_restringido_resp) else 'Sin Perfil'
        data_rows[i]['Tiene Perfil Restringido'] = 'SI' if restr_profile != 'Sin Perfil' else 'NO'
        data_rows[i]['Perfil Restringido'] = restr_profile

    df = pd.DataFrame(data_rows)

    column_order = [
        'Nombre', 'Apellido', 'Nombre de usuario', 'ID', 'Correo', 'Teléfono', 'Género',
        'Fecha de nacimiento', 'Acceso', 'Fecha de creación', 'Fecha último acceso SAAM',
        'Organización activa', 'RFC', 'Rol', 'Perfil', 'Tiene Perfil Restringido',
        'Perfil Restringido', 'Org', 'Observaciones Organización', 'Activo'
    ]

    with pd.ExcelWriter('reporte_de_usuarios_cas.xlsx', engine='xlsxwriter') as writer:
        df[column_order].to_excel(writer, sheet_name='Sheet1', index=False)

    with open('reporte_de_usuarios_cas.xlsx', "rb") as f:
        response = HttpResponse(f, content_type='application/msword')
        response['Content-Disposition'] = 'attachment; filename=reporte_de_usuarios_cas.xlsx'

    os.remove('reporte_de_usuarios_cas.xlsx')

    return response


# @api_view(['GET'])
# @permission_classes((IsAuthenticated, ))
# def report_users(request):
#     orgname =  request.GET.get('org',None)
    
#     if orgname and int(orgname) != 0:
#         org = Organization.objects.get(pk = orgname)
#         urlname  = org.urlname
#         users = UserInfo.objects.filter(org = org).exclude(name_org__isnull = False).order_by('org')
#     else:
#         org = Organization.objects.all()
#         urlname = 'all'
#         users = UserInfo.objects.filter(org__in = org).exclude(name_org__isnull = False).order_by('org')


#     queryset = users.values_list('user__id', flat=True)
#     # users_ids = users.values_list('user__id',flat=True)
#     nombres = []
#     apellidos = []
#     usernames = []
#     ids = []
#     correos = []
#     activos = []
#     phones = []
#     generos = []
#     birthdates = []
#     fecha_creacion = []
#     fecha_last_mov = []
#     org_activa = []
#     org_names = []
#     rfcs = []
#     perfiles = []
#     roles = []
#     perfill_restringido = []
#     manage_admins = []
#     observations = []
    
#     for user in queryset:
#         pr = 'Sin Perfil'

#         user = User.objects.get(id = user)
#         user_info = UserInfo.objects.filter(user = user)
#         if not user_info.exists():
#             continue
#         user_info = user_info.first()


#         profiles = Profile.objects.filter(
#             org = user_info.org,
#             user_info = user_info
#         )
#         if profiles.exists():
#             perfiles.append(profiles.first().name)
#         else:
#             perfiles.append('')

        
#         app_ = Application.objects.filter(name = 'SAAM')
#         app = OrganizationApplication.objects.filter( organization = user_info.org, application__in = app_)

#         if app.exists():
#             app = app.first()
#             org_activa.append(app.is_active)
#         else:
#             org_activa.append('')
#         if user_info.org:
#             if user_info.org.observations:
#                 observations.append(user_info.org.observations)
#             else:
#                 observations.append('')
#         else:
#             observations.append('')
#         if user_info.user.date_joined:
#             fecha_creacion.append(user_info.user.date_joined.strftime("%d/%m/%Y"))
#         else:
#             fecha_creacion.append('')

#         if user_info.ultimo_acceso_saam:
#             fecha_last_mov.append(user_info.ultimo_acceso_saam.strftime("%d/%m/%Y: %H:%M:%S"))
#         else:
#             fecha_last_mov.append('')
        
#         nombres.append(user.first_name)
#         apellidos.append(user.last_name)
#         usernames.append(user.username)
#         ids.append(user.id)
#         correos.append(user.email)
#         activos.append(user.is_active)

#         phones.append(user_info.phone)
#         manage_admins.append(user_info.get_manage_profile_display())
#         org_names.append(user_info.org.urlname)
#         generos.append(user_info.get_gender_display())
#         birthdates.append(user_info.birthdate)
#         rfcs.append(user_info.rfc)
#         roles.append(user_info.get_role_display())
#         perfill_restringido.append(pr)
       

#     token_jwt = get_jwt(request.user.id, urlname)

#     payload = {
#         "Authorization": "Bearer %s" % token_jwt,
#         'usernames': list(usernames)
#     }
#     headers = {
#         'Content-Type': 'application/json' ,
#         'Authorization': 'Bearer %s' % token_jwt
#     }

#     r = requests.post(settings.SAAM_API_IP + 'perfil-usuario-restringido-array-cas/', json.dumps(payload), headers = headers, verify=False)
#     if(r.status_code == 200):
#         perfill_restringido = r.json()
    

#     df = pd.DataFrame({
#         'Nombre': nombres ,  
#         'Apellido': apellidos ,  
#         'Nombre de usuario': usernames  ,
#         'ID': ids ,
#         'Correo': correos ,
#         'Teléfono': phones ,  
#         'Género': [g.get_gender_display() for g in users],  
#         'Fecha de nacimiento': birthdates ,   
#         'Acceso': manage_admins,
#         'Fecha de creación': fecha_creacion,
#         'Fecha último acceso SAAM': fecha_last_mov,
#         'Observaciones Organización': observations ,  
#         'RFC': rfcs ,  
#         'Rol': roles,  
#         'Perfil': # Creating a dictionary with the keys being the names of the people and the values
#         # being the ages of the people.
#         perfiles,
#         'Tiene Perfil Restringido': ['SI' if a != 'Sin Perfil' else 'NO' for a in perfill_restringido],  
#         'Perfil Restringido': perfill_restringido,  
#         'Org': org_names,  
#         'Organización activa': org_activa,
#         'Activo': activos ,  
#     })

#     column_order = [
#         'Nombre',
#         'Apellido',
#         'Nombre de usuario',
#         'ID',
#         'Correo',
#         'Teléfono',
#         'Género',
#         'Fecha de nacimiento',
#         'Acceso',
#         'Fecha de creación',
#         'Fecha último acceso SAAM',
#         'Organización activa',
#         'RFC',
#         'Rol',
#         'Perfil',
#         'Tiene Perfil Restringido',
#         'Perfil Restringido',
#         'Org',
#         'Observaciones Organización',
#         'Activo'
#     ]


#     import os
#     try:
#         os.remove('reporte_de_usuarios_cas.xlsx')
#     except:
#         pass
#     writer = pd.ExcelWriter('reporte_de_usuarios_cas.xlsx', engine='xlsxwriter')
#     # Convert the dataframe to an XlsxWriter Excel object.
#     df[column_order].to_excel(writer, sheet_name='Sheet1', index=False)
#     # Close the Pandas Excel writer and output the Excel file.
#     writer.save()
#     with open('reporte_de_usuarios_cas.xlsx',"rb") as f:
#         response = HttpResponse(f,content_type='application/msword')
#         response['Content-Disposition'] = 'attachment; filename=reporte_de_usuarios_cas.xlsx'
#         os.remove('reporte_de_usuarios_cas.xlsx')
#         return response
    

import json
import pandas as pd
@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def reporte_perfiles(request):
    org_id =  request.GET.get('org',None)
    org = Organization.objects.get(id = org_id)
    
    perfiles = Profile.objects.filter(
        org = org
    )

    campangnas = []
    reporte_polizas = []
    ver_polizas = [] # "Ver pólizas" 
    ver_ots = [] # "Ver OTs" 
    conciliar_recibos = [] # "Conciliar recibos" 
    mensajeria = [] # "Mensajeria" 
    proyecto_fianza = [] # "Proyecto de fianza" 
    despagar_recibos = [] # "Despagar recibos" 
    administrar_notificaciones = [] # "Administrar notificaciones" 
    eliminar_recibos = [] # "Eliminar recibos" 
    correo_asegurados = [] # "Ver correo electrónico de asegurados" 
    reporte_fianzas = [] # "Reporte fianzas" 
    reporte_cobranza = [] # "Reporte cobranza" 
    cmabiar_referenciador = [] # "Cambiar refrenciador en pólizas" 
    pagar_prorrogar = [] # "Pagar y prorrogar" 
    grafica_renovaciones = [] # "Gráfica renovaciones" 
    filtrado_grafica_cobranza = [] # "Filtrado gráfica cobranza" 
    registrar_endosos = [] # "Registrar endosos" 
    administrar_ots = [] # "Administrar OTs" 
    desconciliar_recibos = [] # "Desconciliación de recibos" 
    desliquidar_recibos = [] # "Desliquidar recibos" 
    liquidar_recibos = [] # "Liquidar recibos" 
    reporte_renovaciones = [] # "Reporte renovaciones" 
    eliminar_ots = [] # "Eliminar OTs" 
    administrar_polizas = [] # "Administrar pólizas" 
    administrar_referenciadores = [] # "Administrar referenciadores" 
    reporte_siniestros = [] # "Reporte Siniestros" 
    eliminar_polizas = [] # "Eliminar pólizas" 
    contratantes_grupos = [] # "Ver contratantes y grupos" 
    rehabilirar_polizas = [] # "Rehabilitar pólizas" 
    ver_cobranza = [] # "Ver cobranza" 
    grafica_cobranza = [] # "Gráfica cobranza" 
    administrar_archivos_sensibles = [] # "Administrar archivos sensibles" 
    reporte_endosos = [] # "Reporte Endosos" 
    admin_contratantes_grupos = [] # "Administrar contratantes y grupos" 
    eliminar_endosos = [] # "Eliminar endosos" 
    comisiones = [] # "Comisiones" 
    eliminar_fianzas = [] # "Eliminar fianzas" 
    pagar_referenciadores = [] # "Pagar a referenciadores" 
    cancelar_ots = [] # "Cancelar OTs" 
    grafica_siniestros = [] # "Gráfica siniestros" 
    crear_paquete = [] # "Crear paquete" 
    formatos = [] # "Formatos" 
    kbis = [] # "KBI's" 
    ver_fianzas = [] # "Ver fianzas" 
    admin_fianzas = [] # "Administrar fianzas" 
    cancelar_polizas = [] # "Cancelar pólizas" 
    agenda = [] # "Agenda" 
    grafica_ots = [] # "Gráfica OTs" 
    cancelar_fianzas = [] # "Cancelar fianzas" 
    correos = [] # "Correos" 
    admin_siniestros = [] # "Administrar siniestros" 
    eliminar_grupos = [] # "Eliminar grupos" 
    referenciador_no_obligatorio = [] # "Referenciador no obligatorio" 
    for perfil in perfiles:
        permisos_perfil = UserPermission.objects.filter(
            profile = perfil
        )

        try:
            c = permisos_perfil.get(permission__name = 'Campañas')
            checked = 'Activo' if c.checked else 'Inactivo'
            campangnas.append(checked)
        except:
            campangnas.append('')

        try:
            c = permisos_perfil.get(permission__name = 'Reporte pólizas')
            checked = 'Activo' if c.checked else 'Inactivo'
            reporte_polizas.append(checked)
        except:
            reporte_polizas.append('')

        try:
            c = permisos_perfil.get(permission__name = "Ver OTs")
            checked = 'Activo' if c.checked else 'Inactivo'
            ver_polizas.append(checked)
        except:
            ver_polizas.append('')

        try:
            c = permisos_perfil.get(permission__name = "Ver OTs")
            checked = 'Activo' if c.checked else 'Inactivo'
            ver_ots.append(checked)
        except:
            ver_ots.append('')

        try:
            c = permisos_perfil.get(permission__name = "Conciliar recibos")
            checked = 'Activo' if c.checked else 'Inactivo'
            conciliar_recibos.append(checked)
        except:
            conciliar_recibos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Mensajeria")
            checked = 'Activo' if c.checked else 'Inactivo'
            mensajeria.append(checked)
        except:
            mensajeria.append('')

        try:
            c = permisos_perfil.get(permission__name = "Proyecto de fianza")
            checked = 'Activo' if c.checked else 'Inactivo'
            proyecto_fianza.append(checked)
        except:
            proyecto_fianza.append('')

        try:
            c = permisos_perfil.get(permission__name = "Despagar recibos")
            checked = 'Activo' if c.checked else 'Inactivo'
            despagar_recibos.append(checked)
        except:
            despagar_recibos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Administrar notificaciones")
            checked = 'Activo' if c.checked else 'Inactivo'
            administrar_notificaciones.append(checked)
        except:
            administrar_notificaciones.append('')

        try:
            c = permisos_perfil.get(permission__name = "Eliminar recibos")
            checked = 'Activo' if c.checked else 'Inactivo'
            eliminar_recibos.append(checked)
        except:
            eliminar_recibos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Ver correo electrónico de asegurados")
            checked = 'Activo' if c.checked else 'Inactivo'
            correo_asegurados.append(checked)
        except:
            correo_asegurados.append('')

        try:
            c = permisos_perfil.get(permission__name = "Reporte fianzas")
            checked = 'Activo' if c.checked else 'Inactivo'
            reporte_fianzas.append(checked)
        except:
            reporte_fianzas.append('')

        try:
            c = permisos_perfil.get(permission__name = "Reporte cobranza")
            checked = 'Activo' if c.checked else 'Inactivo'
            reporte_cobranza.append(checked)
        except:
            reporte_cobranza.append('')

        try:
            c = permisos_perfil.get(permission__name = "Cambiar refrenciador en pólizas")
            checked = 'Activo' if c.checked else 'Inactivo'
            cmabiar_referenciador.append(checked)
        except:
            cmabiar_referenciador.append('')

        try:
            c = permisos_perfil.get(permission__name = "Pagar y prorrogar")
            checked = 'Activo' if c.checked else 'Inactivo'
            pagar_prorrogar.append(checked)
        except:
            pagar_prorrogar.append('')

        try:
            c = permisos_perfil.get(permission__name = "Gráfica renovaciones")
            checked = 'Activo' if c.checked else 'Inactivo'
            grafica_renovaciones.append(checked)
        except:
            grafica_renovaciones.append('')

        try:
            c = permisos_perfil.get(permission__name = "Filtrado gráfica cobranza")
            checked = 'Activo' if c.checked else 'Inactivo'
            filtrado_grafica_cobranza.append(checked)
        except:
            filtrado_grafica_cobranza.append('')

        try:
            c = permisos_perfil.get(permission__name = "Registrar endosos")
            checked = 'Activo' if c.checked else 'Inactivo'
            registrar_endosos.append(checked)
        except:
            registrar_endosos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Administrar OTs")
            checked = 'Activo' if c.checked else 'Inactivo'
            administrar_ots.append(checked)
        except:
            administrar_ots.append('')

        try:
            c = permisos_perfil.get(permission__name = "Desconciliación de recibos")
            checked = 'Activo' if c.checked else 'Inactivo'
            desconciliar_recibos.append(checked)
        except:
            desconciliar_recibos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Desliquidar recibos")
            checked = 'Activo' if c.checked else 'Inactivo'
            desliquidar_recibos.append(checked)
        except:
            desliquidar_recibos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Liquidar recibos")
            checked = 'Activo' if c.checked else 'Inactivo'
            liquidar_recibos.append(checked)
        except:
            liquidar_recibos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Reporte renovaciones")
            checked = 'Activo' if c.checked else 'Inactivo'
            reporte_renovaciones.append(checked)
        except:
            reporte_renovaciones.append('')

        try:
            c = permisos_perfil.get(permission__name = "Eliminar OTs")
            checked = 'Activo' if c.checked else 'Inactivo'
            eliminar_ots.append(checked)
        except:
            eliminar_ots.append('')

        try:
            c = permisos_perfil.get(permission__name = "Administrar pólizas")
            checked = 'Activo' if c.checked else 'Inactivo'
            administrar_polizas.append(checked)
        except:
            administrar_polizas.append('')

        try:
            c = permisos_perfil.get(permission__name = "Administrar referenciadores")
            checked = 'Activo' if c.checked else 'Inactivo'
            administrar_referenciadores.append(checked)
        except:
            administrar_referenciadores.append('')

        try:
            c = permisos_perfil.get(permission__name = "Reporte Siniestros")
            checked = 'Activo' if c.checked else 'Inactivo'
            reporte_siniestros.append(checked)
        except:
            reporte_siniestros.append('')

        try:
            c = permisos_perfil.get(permission__name = "Eliminar pólizas")
            checked = 'Activo' if c.checked else 'Inactivo'
            eliminar_polizas.append(checked)
        except:
            eliminar_polizas.append('')

        try:
            c = permisos_perfil.get(permission__name = "Ver contratantes y grupos")
            checked = 'Activo' if c.checked else 'Inactivo'
            contratantes_grupos.append(checked)
        except:
            contratantes_grupos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Rehabilitar pólizas")
            checked = 'Activo' if c.checked else 'Inactivo'
            rehabilirar_polizas.append(checked)
        except:
            rehabilirar_polizas.append('')

        try:
            c = permisos_perfil.get(permission__name = "Ver cobranza")
            checked = 'Activo' if c.checked else 'Inactivo'
            ver_cobranza.append(checked)
        except:
            ver_cobranza.append('')

        try:
            c = permisos_perfil.get(permission__name = "Gráfica cobranza")
            checked = 'Activo' if c.checked else 'Inactivo'
            grafica_cobranza.append(checked)
        except:
            grafica_cobranza.append('')

        try:
            c = permisos_perfil.get(permission__name = "Administrar archivos sensibles")
            checked = 'Activo' if c.checked else 'Inactivo'
            administrar_archivos_sensibles.append(checked)
        except:
            administrar_archivos_sensibles.append('')

        try:
            c = permisos_perfil.get(permission__name = "Reporte Endosos")
            checked = 'Activo' if c.checked else 'Inactivo'
            reporte_endosos.append(checked)
        except:
            reporte_endosos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Administrar contratantes y grupos")
            checked = 'Activo' if c.checked else 'Inactivo'
            admin_contratantes_grupos.append(checked)
        except:
            admin_contratantes_grupos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Eliminar endosos")
            checked = 'Activo' if c.checked else 'Inactivo'
            eliminar_endosos.append(checked)
        except:
            eliminar_endosos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Comisiones")
            checked = 'Activo' if c.checked else 'Inactivo'
            comisiones.append(checked)
        except:
            comisiones.append('')

        try:
            c = permisos_perfil.get(permission__name = "Eliminar fianzas")
            checked = 'Activo' if c.checked else 'Inactivo'
            eliminar_fianzas.append(checked)
        except:
            eliminar_fianzas.append('')

        try:
            c = permisos_perfil.get(permission__name = "Pagar a referenciadores")
            checked = 'Activo' if c.checked else 'Inactivo'
            pagar_referenciadores.append(checked)
        except:
            pagar_referenciadores.append('')

        try:
            c = permisos_perfil.get(permission__name = "Cancelar OTs")
            checked = 'Activo' if c.checked else 'Inactivo'
            cancelar_ots.append(checked)
        except:
            cancelar_ots.append('')

        try:
            c = permisos_perfil.get(permission__name = "Gráfica siniestros")
            checked = 'Activo' if c.checked else 'Inactivo'
            grafica_siniestros.append(checked)
        except:
            grafica_siniestros.append('')

        try:
            c = permisos_perfil.get(permission__name = "Crear paquete")
            checked = 'Activo' if c.checked else 'Inactivo'
            crear_paquete.append(checked)
        except:
            crear_paquete.append('')

        try:
            c = permisos_perfil.get(permission__name = "Formatos")
            checked = 'Activo' if c.checked else 'Inactivo'
            formatos.append(checked)
        except:
            formatos.append('')

        try:
            c = permisos_perfil.get(permission__name = "KBI's")
            checked = 'Activo' if c.checked else 'Inactivo'
            kbis.append(checked)
        except:
            kbis.append('')

        try:
            c = permisos_perfil.get(permission__name = "Ver fianzas")
            checked = 'Activo' if c.checked else 'Inactivo'
            ver_fianzas.append(checked)
        except:
            ver_fianzas.append('')

        try:
            c = permisos_perfil.get(permission__name = "Administrar fianzas")
            checked = 'Activo' if c.checked else 'Inactivo'
            admin_fianzas.append(checked)
        except:
            admin_fianzas.append('')

        try:
            c = permisos_perfil.get(permission__name = "Cancelar pólizas")
            checked = 'Activo' if c.checked else 'Inactivo'
            cancelar_polizas.append(checked)
        except:
            cancelar_polizas.append('')

        try:
            c = permisos_perfil.get(permission__name = "Agenda")
            checked = 'Activo' if c.checked else 'Inactivo'
            agenda.append(checked)
        except:
            agenda.append('')

        try:
            c = permisos_perfil.get(permission__name = "Gráfica OTs")
            checked = 'Activo' if c.checked else 'Inactivo'
            grafica_ots.append(checked)
        except:
            grafica_ots.append('')

        try:
            c = permisos_perfil.get(permission__name = "Cancelar fianzas")
            checked = 'Activo' if c.checked else 'Inactivo'
            cancelar_fianzas.append(checked)
        except:
            cancelar_fianzas.append('')

        try:
            c = permisos_perfil.get(permission__name = "Correos")
            checked = 'Activo' if c.checked else 'Inactivo'
            correos.append(checked)
        except:
            correos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Administrar siniestros")
            checked = 'Activo' if c.checked else 'Inactivo'
            admin_siniestros.append(checked)
        except:
            admin_siniestros.append('')

        try:
            c = permisos_perfil.get(permission__name = "Eliminar grupos")
            checked = 'Activo' if c.checked else 'Inactivo'
            eliminar_grupos.append(checked)
        except:
            eliminar_grupos.append('')

        try:
            c = permisos_perfil.get(permission__name = "Referenciador no obligatorio")
            checked = 'Activo' if c.checked else 'Inactivo'
            referenciador_no_obligatorio.append(checked)
        except:
            referenciador_no_obligatorio.append('')



    df = pd.DataFrame({
        'Nombre': perfiles.values_list('name', flat=True),  
        'Perfil activo': ['Activo' if item else 'Inactivo' for item in perfiles.values_list('is_active', flat=True)],  
        "Campañas" : campangnas,
        "Reporte pólizas" : reporte_polizas,
        "Ver pólizas" : ver_polizas,
        "Ver OTs" : ver_ots,
        "Conciliar recibos" : conciliar_recibos,
        "Mensajeria" : mensajeria,
        "Proyecto de fianza" : proyecto_fianza,
        "Despagar recibos" : despagar_recibos,
        "Administrar notificaciones" : administrar_notificaciones,
        "Eliminar recibos" : eliminar_recibos,
        "Ver correo electrónico de asegurados" : correo_asegurados,
        "Reporte fianzas" : reporte_fianzas,
        "Reporte cobranza" : reporte_cobranza,
        "Cambiar refrenciador en pólizas" : cmabiar_referenciador,
        "Pagar y prorrogar" : pagar_prorrogar,
        "Gráfica renovaciones" : grafica_renovaciones,
        "Filtrado gráfica cobranza" : filtrado_grafica_cobranza,
        "Registrar endosos" : registrar_endosos,
        "Administrar OTs" : administrar_ots,
        "Desconciliación de recibos" : desconciliar_recibos,
        "Desliquidar recibos" : desliquidar_recibos,
        "Liquidar recibos" : liquidar_recibos,
        "Reporte renovaciones" : reporte_renovaciones,
        "Eliminar OTs" : eliminar_ots,
        "Administrar pólizas" : administrar_polizas,
        "Administrar referenciadores" : administrar_referenciadores,
        "Reporte Siniestros" : reporte_siniestros,
        "Eliminar pólizas" : eliminar_polizas,
        "Ver contratantes y grupos" : contratantes_grupos,
        "Rehabilitar pólizas" : rehabilirar_polizas,
        "Ver cobranza" : ver_cobranza,
        "Gráfica cobranza" : grafica_cobranza,
        "Administrar archivos sensibles" : administrar_archivos_sensibles,
        "Reporte Endosos" : reporte_endosos,
        "Administrar contratantes y grupos" : admin_contratantes_grupos,
        "Eliminar endosos" : eliminar_endosos,
        "Comisiones" : comisiones,
        "Eliminar fianzas" : eliminar_fianzas,
        "Pagar a referenciadores" : pagar_referenciadores,
        "Cancelar OTs" : cancelar_ots,
        "Gráfica siniestros" : grafica_siniestros,
        "Crear paquete" : crear_paquete,
        "Formatos" : formatos,
        "KBI" : kbis,
        "Ver fianzas" : ver_fianzas,
        "Administrar fianzas" : admin_fianzas,
        "Cancelar pólizas" : cancelar_polizas,
        "Agenda" : agenda,
        "Gráfica OTs" : grafica_ots,
        "Cancelar fianzas" : cancelar_fianzas,
        "Correos" : correos,
        "Administrar siniestros" : admin_siniestros,
        "Eliminar grupos" : eliminar_grupos,
        "Referenciador no obligatorio" : referenciador_no_obligatorio,
    })

    column_order = [
        'Nombre',
        'Perfil activo',
        "Campañas",
        "Reporte pólizas",
        "Ver pólizas",
        "Ver OTs",
        "Conciliar recibos",
        "Mensajeria",
        "Proyecto de fianza",
        "Despagar recibos",
        "Administrar notificaciones",
        "Eliminar recibos",
        "Ver correo electrónico de asegurados",
        "Reporte fianzas",
        "Reporte cobranza",
        "Cambiar refrenciador en pólizas",
        "Pagar y prorrogar",
        "Gráfica renovaciones",
        "Filtrado gráfica cobranza",
        "Registrar endosos",
        "Administrar OTs",
        "Desconciliación de recibos",
        "Desliquidar recibos",
        "Liquidar recibos",
        "Reporte renovaciones",
        "Eliminar OTs",
        "Administrar pólizas",
        "Administrar referenciadores",
        "Reporte Siniestros",
        "Eliminar pólizas",
        "Ver contratantes y grupos",
        "Rehabilitar pólizas",
        "Ver cobranza",
        "Gráfica cobranza",
        "Administrar archivos sensibles",
        "Reporte Endosos",
        "Administrar contratantes y grupos",
        "Eliminar endosos",
        "Comisiones",
        "Eliminar fianzas",
        "Pagar a referenciadores",
        "Cancelar OTs",
        "Gráfica siniestros",
        "Crear paquete",
        "Formatos",
        "KBI",
        "Ver fianzas",
        "Administrar fianzas",
        "Cancelar pólizas",
        "Agenda",
        "Gráfica OTs",
        "Cancelar fianzas",
        "Correos",
        "Administrar siniestros",
        "Eliminar grupos",
        "Referenciador no obligatorio",
    ]

    # aux_bd = []
    # for bd in df['Fecha de nacimiento']:
    #     if bd != '':
    #         aux_bd.append(pd.to_datetime(bd, errors='ignore', format='%D/%B/%Y').dt.date)
    #     else:
    #         aux_bd.append('')
    
    # df['Fecha de nacimiento'] = aux_bd

    import os
    try:
        os.remove('reporte_perfiles_cas.xlsx')
    except:
        pass
    writer = pd.ExcelWriter('reporte_perfiles_cas.xlsx', engine='xlsxwriter')
    # Convert the dataframe to an XlsxWriter Excel object.
    df[column_order].to_excel(writer, sheet_name='Sheet1', index=False)
    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    with open('reporte_perfiles_cas.xlsx',"rb") as f:
        response = HttpResponse(f,content_type='application/msword')
        response['Content-Disposition'] = 'attachment; filename=reporte_perfiles_cas.xlsx'
        os.remove('reporte_perfiles_cas.xlsx')
        return response
    


import json
import pandas as pd
@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def reporte_perfiles_restringidos(request):
    org_id =  request.GET.get('org',None)
    org = Organization.objects.get(id = org_id)
    

    org_name =  request.GET.get('org',None)
    data = request.data
    if org_name:
        org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
    claves =  get_perfiles_usuario_restringido(request.user.id, org_name)

    contratante_contratante = []
    contratante_grupo = []
    contratante_celula = []
    contratante_referenciador = []
    contratante_sucursal = []
    poliza_poliza = []
    poliza_grupo = []
    poliza_celula = []
    poliza_referenciador = []
    poliza_sucursal = []
    poliza_agrupacion = []
    poliza_clave_agente = []
    poliza_subramo = []
    poliza_aseguradora = []
    poliza_estatus = []
    
    for clave in claves:
        aux_contratante_contratante = []
        for item in clave['contratante_contratante']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_contratante_contratante.append(item['item_text'])
        aux_contratante_contratante = ', '.join(aux_contratante_contratante)
        contratante_contratante.append(aux_contratante_contratante)

        aux_contratante_grupo = []
        for item in clave['contratante_grupo']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_contratante_grupo.append(item['item_text'])
        aux_contratante_grupo = ', '.join(aux_contratante_grupo)
        contratante_grupo.append(aux_contratante_grupo)

        aux_contratante_celula = []
        for item in clave['contratante_celula']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_contratante_celula.append(item['item_text'])
        aux_contratante_celula = ', '.join(aux_contratante_celula)
        contratante_celula.append(aux_contratante_celula)

        aux_contratante_referenciador = []
        for item in clave['contratante_referenciador']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_contratante_referenciador.append(item['item_text'])
        aux_contratante_referenciador = ', '.join(aux_contratante_referenciador)
        contratante_referenciador.append(aux_contratante_referenciador)

        aux_contratante_sucursal = []
        for item in clave['contratante_sucursal']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_contratante_sucursal.append(item['item_text'])
        aux_contratante_sucursal = ', '.join(aux_contratante_sucursal)
        contratante_sucursal.append(aux_contratante_sucursal)

        aux_poliza_poliza = []
        for item in clave['poliza_poliza']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_poliza_poliza.append(item['item_text'])
        aux_poliza_poliza = ', '.join(aux_poliza_poliza)
        poliza_poliza.append(aux_poliza_poliza)

        aux_poliza_grupo = []
        for item in clave['poliza_grupo']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_poliza_grupo.append(item['item_text'])
        aux_poliza_grupo = ', '.join(aux_poliza_grupo)
        poliza_grupo.append(aux_poliza_grupo)

        aux_poliza_celula = []
        for item in clave['poliza_celula']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_poliza_celula.append(item['item_text'])
        aux_poliza_celula = ', '.join(aux_poliza_celula)
        poliza_celula.append(aux_poliza_celula)


        aux_poliza_referenciador = []
        for item in clave['poliza_referenciador']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_poliza_referenciador.append(item['item_text'])
        aux_poliza_referenciador = ', '.join(aux_poliza_referenciador)
        poliza_referenciador.append(aux_poliza_referenciador)

        
        
        aux_poliza_sucursal = []
        for item in clave['poliza_sucursal']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_poliza_sucursal.append(item['item_text'])
        aux_poliza_sucursal = ', '.join(aux_poliza_sucursal)
        poliza_sucursal.append(aux_poliza_sucursal)

        aux_poliza_agrupacion = []
        for item in clave['poliza_agrupacion']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_poliza_agrupacion.append(item['item_text'])
        aux_poliza_agrupacion = ', '.join(aux_poliza_agrupacion)
        poliza_agrupacion.append(aux_poliza_agrupacion)

        aux_poliza_clave_agente = []
        for item in clave['poliza_clave_agente']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_poliza_clave_agente.append(item['item_text'])
        aux_poliza_clave_agente = ', '.join(aux_poliza_clave_agente)
        poliza_clave_agente.append(aux_poliza_clave_agente)

        aux_poliza_subramo = []
        for item in clave['poliza_subramo']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_poliza_subramo.append(item['item_text'])
        aux_poliza_subramo = ', '.join(aux_poliza_subramo)
        poliza_subramo.append(aux_poliza_subramo)

        aux_poliza_aseguradora = []
        for item in clave['poliza_aseguradora']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_poliza_aseguradora.append(item['item_text'])
        aux_poliza_aseguradora = ', '.join(aux_poliza_aseguradora)
        poliza_aseguradora.append(aux_poliza_aseguradora)

        aux_poliza_estatus = []
        for item in clave['poliza_estatus']:
            item = json.loads(str(json.loads(item)).replace('\'','"'))
            aux_poliza_estatus.append(item['item_text'])
        aux_poliza_estatus = ', '.join(aux_poliza_estatus)
        poliza_estatus.append(aux_poliza_estatus)

    

    df = pd.DataFrame({
        'Nombre': [ item['nombre'] for item in claves],  
        'Activo': ['Activo' if item else 'Inactivo' for item in claves],  
        "[Contratante] Por contratante": contratante_contratante,
        "[Contratante] Por grupo": contratante_grupo,
        "[Contratante] Por celula": contratante_celula,
        "[Contratante] Por referenciador": contratante_referenciador,
        "[Contratante] Por sucursal": contratante_sucursal,
        "[Póliza] Por póliza": poliza_poliza,
        "[Póliza] Por grupo": poliza_grupo,
        "[Póliza] Por celula": poliza_celula,
        "[Póliza] Por referenciador": poliza_referenciador,
        "[Póliza] Por sucursal": poliza_sucursal,
        "[Póliza] Por agrupacion": poliza_agrupacion,
        "[Póliza] Por clave_agente": poliza_clave_agente,
        "[Póliza] Por subramo": poliza_subramo,
        "[Póliza] Por aseguradora": poliza_aseguradora,
        "[Póliza] Por estatus": poliza_estatus
    })

    column_order = [
        'Nombre',
        'Activo',
        "[Contratante] Por contratante",
        "[Contratante] Por grupo",
        "[Contratante] Por celula",
        "[Contratante] Por referenciador",
        "[Contratante] Por sucursal",
        "[Póliza] Por póliza",
        "[Póliza] Por grupo",
        "[Póliza] Por celula",
        "[Póliza] Por referenciador",
        "[Póliza] Por sucursal",
        "[Póliza] Por agrupacion",
        "[Póliza] Por clave_agente",
        "[Póliza] Por subramo",
        "[Póliza] Por aseguradora",
        "[Póliza] Por estatus"
    ]

    # aux_bd = []
    # for bd in df['Fecha de nacimiento']:
    #     if bd != '':
    #         aux_bd.append(pd.to_datetime(bd, errors='ignore', format='%D/%B/%Y').dt.date)
    #     else:
    #         aux_bd.append('')
    
    # df['Fecha de nacimiento'] = aux_bd

    import os
    try:
        os.remove('reporte_perfiles_restringidos_cas.xlsx')
    except:
        pass
    writer = pd.ExcelWriter('reporte_perfiles_restringidos_cas.xlsx', engine='xlsxwriter')
    # Convert the dataframe to an XlsxWriter Excel object.
    df[column_order].to_excel(writer, sheet_name='Sheet1', index=False)
    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    with open('reporte_perfiles_restringidos_cas.xlsx',"rb") as f:
        response = HttpResponse(f,content_type='application/msword')
        response['Content-Disposition'] = 'attachment; filename=reporte_perfiles_restringidos_cas.xlsx'
        os.remove('reporte_perfiles_restringidos_cas.xlsx')
        return response
    



@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def search_user(request):
    name = request.GET.get('name', 0)
    compose_name = name.split(' ')
    org = Organization.objects.get(pk = request.GET.get('org',None))
    users = UserInfo.objects.filter(org = org).values_list('user__id', flat = True)
    first_name = User.objects.filter(first_name__icontains = name.lower(), id__in = list(users))
    last_name = User.objects.filter(last_name__icontains = name.lower(), id__in = list(users))
    username = User.objects.filter(username__icontains = name.lower(), id__in = list(users))
    
    queryset = first_name | last_name | username
    
    if len(compose_name) > 1:
        from django.db.models import Value as V
        from django.db.models.functions import Concat 
        compose_users = User.objects.filter(id__in = list(users)).annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(full_name__icontains=name)
        queryset = queryset | compose_users
    
    serializer  = UserSerializer(queryset, context = {'request':request}, many = True)
    return Response(serializer.data)

class users_org(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsOrgMember)   

    def get_queryset(self):
        orgname = self.request.GET.get('orgname')
        if orgname and int(orgname) != 0:
            org = Organization.objects.get(pk = orgname)
            users = UserInfo.objects.filter(org = org).values_list('user__id', flat = True)    
        else:
            org = Organization.objects.all()
            users = UserInfo.objects.filter(org__in = org).values_list('user__id', flat = True)    

        queryset = User.objects.filter(id__in = list(users))
        if queryset.exists():
            return queryset.order_by('-id')
        else:
            return []

class users_app_created(viewsets.ModelViewSet):
    serializer_class = UserAppInfoSerializer
    permission_classes = (IsAuthenticated, IsOrgMember)   

    def get_queryset(self):
        orgname = Organization.objects.get(id = self.request.GET.get('org')).urlname
        identificador = self.request.GET.get('identifier')
        since = self.request.GET.get('since')
        until = self.request.GET.get('until')
        users = UserInfo.objects.filter(name_org = orgname)
        query = Q()
        created = list()
        identifier = list()
        if since or until:
            try:
                f = "%d/%m/%Y %H:%M:%S"
                since = datetime.strptime(since , f)
                until = datetime.strptime(until , f)
            except:
                f = "%m/%d/%Y %H:%M:%S"
                since = datetime.strptime(since , f)
                until = datetime.strptime(until , f)
            dates = [Q(created_at__gte=since),Q(created_at__lte = until)]
            users = users.filter(reduce(operator.and_, dates))

        if identificador:
            users = users.filter(name_org = orgname,identifier__icontains = identificador)

        queryset = User.objects.filter(id__in = list(users.values_list('user__id', flat = True)))

        if queryset:
            return queryset.order_by('-id')
        else:
            return []

@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def report_users_app(request):
    orgname = request.data['orgname']
    orgname = Organization.objects.get(id = request.GET.get('org')).urlname
    identificador = request.data['identifier']
    since = request.data['since']
    until = request.data['until']
    users = UserInfo.objects.filter(name_org = orgname)
    query = Q()
    if since or until:
        try:
            f = "%d/%m/%Y %H:%M:%S"
            since = datetime.strptime(since , f)
            until = datetime.strptime(until , f)
        except:
            f = "%m/%d/%Y %H:%M:%S"
            since = datetime.strptime(since , f)
            until = datetime.strptime(until , f)
        dates = [Q(created_at__gte=since),Q(created_at__lte = until)]
        users = users.filter(reduce(operator.and_, dates))

    if identificador:
        users = users.filter(name_org = orgname,identifier__icontains = identificador)

    user_filter = User.objects.filter(id__in = list(users.values_list('user__id', flat = True)))


    queryset = User.objects.filter(id__in = list(users.values_list('user__id', flat = True)))
    users_ids = queryset.values_list('id',flat=True)
    phones = []
    generos = []
    nombres = []
    org_names = []
    identifiers = []
    rfcs = []
    roles = []
    perfill_restringido = []
    for uid in users_ids:
        user_info = UserInfo.objects.filter(user__id = uid)
        if user_info.exists():
            user_info = user_info.first()
            phones.append(user_info.phone)
            org_names.append(user_info.name_org)
            nombres.append(user_info.user.first_name +' '+str(user_info.user.last_name))
            identifiers.append(user_info.identifier)
        else:
            phones.append('')
            phones.append('')
            nombres.append('')
            identifiers.append('')


    df = pd.DataFrame({
        'Identificador': identifiers,  
        'Nombre': nombres,  
        'Nombre de usuario': queryset.values_list('username', flat=True),
        'ID': queryset.values_list('id', flat=True),
        'Correo': queryset.values_list('email', flat=True),
        'Org': org_names,  
        'Activo': queryset.values_list('is_active', flat=True) ,  
    })

    import os
    try:
        os.remove('reporte_de_usuarios_cas_app.xlsx')
    except:
        pass
    writer = pd.ExcelWriter('reporte_de_usuarios_cas_app.xlsx', engine='xlsxwriter')
    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    with open('reporte_de_usuarios_cas_app.xlsx',"rb") as f:
        response = HttpResponse(f,content_type='application/msword')
        response['Content-Disposition'] = 'attachment; filename=reporte_de_usuarios_cas_app.xlsx'
        return response


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def desactivar_usuario_app(request):    
    name = request.data['username']
    password = request.data['password']
    if name and password:
        user = authenticate(
            username=name,
            password=password
        )
        if user:
            user.is_active =False
            user.save()
            userinfo = UserInfo.objects.get(user = user)
            if userinfo:
                userinfo.is_active=False
                userinfo.save()   
            serializer  = UserSerializer(user, context = {'request':request}, many = False)
            return JsonResponse({'status':'200', 'data': 'Usuario desactivado'})
        else:        
            return JsonResponse({'status':'400', 'data': 'Debe agregar el username y contraseña correcta'})
    else:        
        return JsonResponse({'status':'400', 'data': 'Debe agregar el username y contraseña correcta'})
# valdiar si el email no existe en cualqueir otro registro
@api_view(['POST'])
@permission_classes((AllowAny, ))
def exist_email_saam_lite(request):
    user_id = request.data['user_id']
    if not user_id:
        return Response(User.objects.filter(email = request.data['email']).exists())
    else:
        return Response(User.objects.exclude(id = user_id).filter(email = request.data['email']).exists())
    
@api_view(['GET'])
@permission_classes((AllowAny, ))
def exist_username_lite(self, username):
    return Response(User.objects.filter(username = username).exists())


# crear el PERFIL para saam LITE
class ProfileSaamLiteViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = (AllowAny, )
    pagination_class = None
    
    def get_queryset(self):
        if int(self.request.GET.get('type_profile',0)) in [0,4]:            
            if int(self.request.GET.get('type_profile',0)) == 4:
                return Profile.objects.filter(
                    org = Organization.objects.get(pk=self.request.GET.get('org')),
                    type_profile = 2 if int(self.request.GET.get('type_profile',0)) == 4 else 1
                ).order_by('-id')
            else:
                return Profile.objects.filter(
                    org = Organization.objects.get(pk=self.request.GET.get('org'))
                ).order_by('-id')
        else:
            if int(self.request.GET.get('type_profile',0)) == 4:
                return Profile.objects.filter(
                    org = Organization.objects.get(pk=self.request.GET.get('org')),
                    type_profile = 2 if int(self.request.GET.get('type_profile',0)) == 4 else 1
                ).order_by('-id')
            else:               
                return Profile.objects.filter(
                    org = Organization.objects.get(pk=self.request.GET.get('org')),
                    type_profile = 2 if int(self.request.GET.get('type_profile',0)) == 2 else 1
                ).order_by('-id')

    def perform_create(self, serializer):
        # if not self.request.user.is_superuser and self.request.user.userinfo.role not in [0,1]:
        #     raise PermissionDenied(get_error('permission_denied'))

        # if self.request.user.is_staff and not self.request.user.is_superuser:
        #     obj = serializer.save(org = self.request.user.userinfo.org)
        # el
        if self.request.GET.get('org', 0) != 0:
            obj = serializer.save(org = Organization.objects.get(pk = int(self.request.GET.get('org'))))   
        else:
            raise ValidationError(get_error('org_does_not_included')) 
# CREAR USUARIO DESDE SAAM - LITE
class UserSaamLiteViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = (AllowAny, )
    
    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                # if not self.request.user.is_superuser and self.request.user.userinfo.role not in [0,1]:
                #     raise PermissionDenied(get_error('permission_denied'))
               
                # verificar el numero de usuarios de acuerdo al plan que tienen el cliente
                # if self.request.GET.get('org') and self.request.user.is_superuser:
                if self.request.GET.get('org'):
                    org = Organization.objects.get(id = self.request.GET.get('org'))
                elif self.request.GET.get('org'):
                    org = self.request.user.userinfo.org
                else: 
                    org = ''
                # if org and org.billiable:
                #     token_jwt = get_jwt(self.request.user.id, None, None)
                #     headers = {
                #         'Content-Type': 'application/json' ,
                #         'Authorization': 'Bearer %s' % token_jwt
                #     }

                #     if org.billiable: 
                #         r = requests.get(settings.PAYMENT_API_IP + 'planes/suscripciones-cliente/'+ org.urlname, headers = headers)
                #         if r.status_code == 200:
                #             r = r.json()
                #         else:
                #             r = {
                #                 'plan': {
                #                     'users_number':2
                #                 }
                #             }

                #         numero_usuarios_creados = len(UserInfo.objects.filter(org = org))
                #         numero_usuarios_plan = 0
                #         for plan in r:
                #             if 'status' in plan and plan['status'] == 'active':
                #                 if 'plan' in plan:
                #                     numero_usuarios_plan = plan['plan']['users_number']
                #         print(numero_usuarios_plan, numero_usuarios_creados)
                #         if numero_usuarios_creados >= numero_usuarios_plan:
                #             raise APIException(get_error('max_user_number_reached'))
                # crear el usuario
                obj = serializer.save()
                password =self.request.data['password']
                obj.set_password(password)
                obj.save()
        except IntegrityError as e:
            raise APIException(e)
        except Exception as e:
            raise APIException(e)


    def get_queryset(self):
        if self.request.user.is_superuser:
            org = self.request.GET.get('org',0)
            if org != 0:
                return User.objects.filter(is_active = True, userinfo__org=org).order_by('-id')
            return User.objects.filter(is_active = True, is_superuser = True).order_by('-id')
        else:
            if UserInfo.objects.filter(user=self.request.user).exists():
                return User.objects.filter(is_active = True, userinfo__org=self.request.user.userinfo.org).order_by('-id')
            else:
                return []


    def partial_update(self, request, pk=None):
        queryset = User.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        # if not self.request.user.is_superuser and self.request.user.userinfo.role not in [0,1]:
        #     if cf.id != self.request.user.id:
        #         raise PermissionDenied(get_error('permission_denied'))
        serializer = UserSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_instance = User.objects.get(id = cf.id)
        
        if 'password' in request.data and request.data['password'] and len(request.data['password']) > 0:
            cf.set_password(request.data['password'])
            cf.save()
        # if not request.user.is_superuser:
        if 'profile' in request.data:
            profile = Profile.objects.get(pk = request.data['profile'])
            profile_to_empty = Profile.objects.filter(application = profile.application, user_info = cf.userinfo)
            for p in profile_to_empty:
                p.user_info.remove(cf.userinfo)
            profile.user_info.add(cf.userinfo)
        if 'userinfo' in request.data and request.data['userinfo']['id']:
            # nc = True
            # if 'notificarContabilidad' in request.data['userinfo']:
            #     nc = request.data['userinfo'].pop('notificarContabilidad')
            UserInfo.objects.filter(pk = request.data['userinfo']['id']).update(**request.data['userinfo'])
            request.data['userinfo']['notificarContabilidad'] = False
            request.data['userinfo']
        if not user_instance.is_active:
            UserInfo.objects.filter(user = user_instance).update(manage_profile=False)
            print('Sin acceso')
        return Response(serializer.data)
# obtener usuarios conperfil operativo
@api_view(['GET'])
def usersoperativos(request, org):
    org=Organization.objects.filter(urlname=org)
    if org:
        org=org[0]
    else:
        return Response({'data':'sin datos, no hay org'})
    # Filtra según org si lo necesitas
    ui = UserInfo.objects.filter(manage_profile=1,org=org,is_active=True)
    users = User.objects.filter(id__in=list(ui.values_list('user__id', flat=True)),is_active=True)
    serializer = UserSerializer(users, context={'request': request}, many=True)
    return Response(serializer.data)