from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError, transaction, DatabaseError
from django.db.models.functions import Concat
from django.db.models import F, Value
from .models import PlantillaCorreo
from .serializers import PlantillaCorreoSerializer

from rest_framework import permissions, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.db.models.functions import Cast
from django.http import JsonResponse
import pandas as pd
import xlrd
from .serializers import (
        OrganizationHyperSerializer, OrganizationApplicationSerializer, 
        OrganizationLogoSerializer, OrganizationLogoMiniSerializer, 
        OrganizationSerializer, OrganizationDetailsHyperSerializer, 
        OrganizationFileHyperSerializer, OrganizationMinSerializer, OrganizationLiteSerializer,
        RecibosHyperSerializer, RecibosDetailsHyperSerializer, RecibosFileHyperSerializer, CarouselDetailsSerializer
    )
from .models import Organization, OrganizationApplication, Recibos, OrganizationFile, RecibosFile, CarouselGeneral
from core.permissions import OnlySuperUserPermission
from core.models import DemoRequest, Application
from core.errors import get_error
from core.permissions import IsOrgMember
from payment.tasks import *
from accounts.models import UserInfo
from accounts.serializers import UserInfoSerializer
# Create your views here.
import time
from django.http import HttpResponse
from functools import reduce
from django.db.models import *
import operator
from operator import and_, or_
from operator import __or__ as OR
from operator import __and__ as AND
from datetime import datetime, timedelta, date, time
from dateutil.relativedelta import relativedelta
from django.http import JsonResponse, Http404
from presigned_url import get_url_file
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.pagination import PageNumberPagination

def file_get_queryset(request, model, owner):
    return model.objects.filter(owner=owner, org_name=request.GET.get('org'))

class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationHyperSerializer
    permission_classes = (IsAuthenticated, OnlySuperUserPermission )

    def get_queryset(self):
        # return Organization.objects.all().order_by('-id')
        try:
            activa = self.request.GET.get('active')
            if activa =='true':
                app_ = Application.objects.filter(name = 'SAAM')
                act = OrganizationApplication.objects.filter(application__in = app_,is_active =True).values_list('organization__urlname',flat=True)
                app_2 = Application.objects.filter(name = 'Multicotizador')
                act2 = OrganizationApplication.objects.filter(application__in = app_2,is_active =True).values_list('organization__urlname',flat=True)
                organizaciones = Organization.objects.filter(Q(urlname__in=act) | Q(urlname__in=act2)).distinct('urlname')
            elif activa =='false':
                app_ = Application.objects.filter(name = 'SAAM')
                act = OrganizationApplication.objects.filter(application__in = app_,is_active =False).values_list('organization__urlname',flat=True)
                app_2 = Application.objects.filter(name = 'Multicotizador')
                act2 = OrganizationApplication.objects.filter(application__in = app_2,is_active =False).values_list('organization__urlname',flat=True)
                # organizaciones = Organization.objects.filter(Q(urlname__in=act) | Q(urlname__in=act2)).distinct('urlname')
                intersection = set(act) & set(act2)
                organizaciones = Organization.objects.filter(urlname__in=intersection).distinct('urlname')
                orgs=[]
            else:
                organizaciones = Organization.objects.all().order_by('-id')
        except Exception as ers:
            organizaciones = Organization.objects.all().order_by('-id')
        # return Organization.objects.all().order_by('urlname')
        return organizaciones

    def create(self, request, *args, **kwargs):
        if 'info_org' in request.data:
            org_info_list = request.data.pop('info_org')
        else:
            org_info_list = []

        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data = request.data, many = isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        for org_info in org_info_list:
            app = Application.objects.get(name=org_info['name'])
            org_app, created = OrganizationApplication.objects.get_or_create(organization=obj, application=app)
            org_app.is_active = org_info['is_active']
            org_app.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        queryset = Organization.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        # Revisamos que no se quiera actualizar un registro con el mismo urlname de una organizacion ya existente
        if 'urlname' in request.data and Organization.objects.filter(urlname = request.data['urlname']).exclude(id = cf.id).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if 'info_org' in request.data:
            org_info_list = request.data.pop('info_org')
            for org_info in org_info_list:
                app = Application.objects.get(name=org_info['name'])
                org_app, created = OrganizationApplication.objects.get_or_create(organization=Organization.objects.get(pk=pk), application=app)
                org_app.is_active = org_info['is_active']
                org_app.save()

        serializer = OrganizationHyperSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class OrganizationMainFileViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationFileHyperSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return OrganizationFile.objects.all()

class OrganizationFileViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    serializer_class = OrganizationFileHyperSerializer

    def perform_create(self, serializer):
        org_=Organization.objects.get(id=self.kwargs['id'])
        serializer.save(owner=org_)

    def get_queryset(self):
        owner = self.kwargs['id']
        return file_get_queryset(self.request, OrganizationFile, owner)

class RecibosMainFileViewSet(viewsets.ModelViewSet):
    serializer_class = RecibosFileHyperSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return RecibosFile.objects.all()

class RecibosFileViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    serializer_class = RecibosFileHyperSerializer

    def perform_create(self, serializer):
        recibo = Recibos.objects.get(id=self.kwargs['id'])
        tipo = self.request.data['tipo']

        if serializer.is_valid():
            serializer.save(owner=recibo)
            if tipo and int(tipo) == 2:
                recibo.status = 25
                recibo.fecha_pago = timezone.now()
                recibo.save()

    def get_queryset(self):
        owner = self.kwargs['id']
        return file_get_queryset(self.request, RecibosFile, owner)


class OrganizationApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationApplicationSerializer
    permission_classes = (IsAuthenticated, )
    def get_queryset(self):
        return OrganizationApplication.objects.all().order_by('-id')


class OrganizationMinViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationMinSerializer
    permission_classes = (permissions.IsAuthenticated, OnlySuperUserPermission )
    pagination_class = None
    
    def get_queryset(self):
        return Organization.objects.all().order_by('urlname')

class OrganizationFullViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationHyperSerializer
    permission_classes = (permissions.IsAuthenticated, OnlySuperUserPermission )
    pagination_class = None

    def get_queryset(self):
        return Organization.objects.all().order_by('urlname')

    def partial_update(self, request, pk=None):
        queryset = Organization.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        # Revisamos que no se quiera actualizar un registro con el mismo urlname de una organizacion ya existente
        if 'urlname' in request.data and Organization.objects.filter(urlname = request.data['urlname']).exclude(id = cf.id).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = OrganizationHyperSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class OrganizationLiteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrganizationLiteSerializer
    permission_classes = (permissions.IsAuthenticated, OnlySuperUserPermission )
    pagination_class = None

    def get_queryset(self):
        return Organization.objects.all().order_by('urlname')


class OrganizationLogoViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationLogoSerializer
    permission_classes = (IsAuthenticated, )
    http_method_names = ['patch']
    def get_queryset(self):
        return Organization.objects.all().order_by('-id')


class OrganizationLogoMiniViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationLogoMiniSerializer
    permission_classes = (IsAuthenticated, )
    http_method_names = ['patch']
    def get_queryset(self):
        return Organization.objects.all().order_by('-id')





@api_view(['GET'])
def exist_organization(self, urlname):
    return Response(Organization.objects.filter(urlname = urlname.lower()).exists())

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_org(request, urlname):
    queryset = Organization.objects.filter(urlname__contains = urlname.lower())
    serializer  = OrganizationHyperSerializer(queryset, context = {'request':request}, many = True)
    return Response(serializer.data)

@api_view(['GET', 'PATCH'])
@permission_classes((IsAuthenticated, IsOrgMember))
def organization_info(request, id):
    if request.method == 'GET':
        serializer = OrganizationHyperSerializer(Organization.objects.get(pk = id),  context = {'request':request}, many = False)
        return Response(serializer.data)
    elif request.method == 'PATCH':
        queryset = Organization.objects.all()
        cf = get_object_or_404(queryset, pk=request.data['id'])
        serializer = OrganizationHyperSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes((IsAuthenticated, IsOrgMember))
def is_org_demo(request, id):
    data = OrganizationApplication.objects.filter(organization__id = id, application__name = 'SAAM')
    if not data.exists():
        try:
            org = Organization.objects.get(id = id)
        except Organization.DoesNotExist:
            return Response(get_error('org_does_not_exist'), status = status.HTTP_400_BAD_REQUEST) 
        app = Application.objects.get(name = 'SAAM', id = 1)
        data = OrganizationApplication.objects.create(
            organization = org,
            application =  app
        )       
    else:
        data = data.first()
    return Response(data.is_demo)
   
@api_view(['POST'])
def create_org_demo(request):
    pk = request.data['pk']
    try:
        pre = DemoRequest.objects.get(pk = pk)
    except DemoRequest.DoesNotExist:
        return Response(get_error('prerrequisite_does_not_exist'), status = status.HTTP_404_NOT_FOUND) 
    except Exception as e:
        return Response(str(e), status = status.HTTP_500_INTERNAL_SERVER_ERROR) 
    if pre.status != 'PENDIENTE':
        return Response(get_error('prerrequisite_does_not_valid'), status = status.HTTP_400_BAD_REQUEST)

    app = Application.objects.get(name = 'SAAM', id = 1)


    try:
        with transaction.atomic():
            org = Organization(
                name = request.data['org'],
                urlname = request.data['org'].lower(),
                alias = request.data['org'],
                phone = request.data['phone']
            )
            org.save()


            org_application = OrganizationApplication(
                organization = org,
                application =  app,
                is_active = True,
                is_demo = True,
                date_demo = timezone.now()
            )

            org_application.save()
            name = pre.name.split(' ')
            last_name = " ".join(name[1:])  if len(name) >= 2 else ''
            username = pre.email.split('@')[0]

            user = User(
                username = username,
                first_name = name[0],
                last_name = last_name,
                email = pre.email,
                is_staff = True,
                is_superuser = False,
                is_active = True
            )
            user.save()
            user.set_password(request.data['password'])
            user.save()

            from accounts.models import UserInfo, Profile
            ui = UserInfo(
                user = user,
                org = org,
                phone = request.data['phone']
            )
            ui.save()

            token = Token.objects.create(user=user)
            token.save()

            app = Application.objects.get(name = 'SAAM')
            profile, profile_created = Profile.objects.get_or_create( 
                name = 'Default',
                org = org,
                application = app,
            )
            permissions = [[{"name":"Gráfica OTs","id":1,"checked":True},{"name":"Gráfica cobranza","id":2,"checked":True},{"name":"Gráfica renovaciones","id":3,"checked":True},{"name":"Gráfica siniestros","id":4,"checked":True},{"name":"KBI's","id":5,"checked":True},{"name":"Filtrado gráfica cobranza","id":6,"checked":True}],[{"name":"Administrar contratantes y grupos","id":7,"checked":True},{"name":"Ver contratantes y grupos","id":8,"checked":True},{"name":"Eliminar grupos","id":9,"checked":True}],[{"name":"Administrar OTs","id":10,"checked":True},{"name":"Ver OTs","id":11,"checked":True},{"name":"Eliminar OTs","id":12,"checked":True},{"name":"Cancelar OTs","id":13,"checked":True}],[{"name":"Administrar pólizas","id":14,"checked":True},{"name":"Ver pólizas","id":15,"checked":True},{"name":"Eliminar pólizas","id":16,"checked":True},{"name":"Cancelar pólizas","id":17,"checked":True}],[{"name":"Administrar fianzas","id":18,"checked":True},{"name":"Ver fianzas","id":19,"checked":True},{"name":"Eliminar fianzas","id":20,"checked":True},{"name":"Cancelar fianzas","id":21,"checked":True}],[{"name":"Reporte cobranza","id":22,"checked":True},{"name":"Reporte renovaciones","id":23,"checked":True},{"name":"Reporte pólizas","id":24,"checked":True},{"name":"Reporte Endosos","id":25,"checked":True},{"name":"Reporte Siniestros","id":26,"checked":True},{"name":"Reporte fianzas","id":27,"checked":True}],[{"name":"Ver cobranza","id":28,"checked":True},{"name":"Liquidar recibos","id":29,"checked":True},{"name":"Conciliar recibos","id":30,"checked":True},{"name":"Desliquidar recibos","id":31,"checked":True},{"name":"Desconciliación de recibos","id":32,"checked":True},{"name":"Pagar y prorrogar","id":33,"checked":True},{"name":"Despagar recibos","id":34,"checked":True},{"name":"Eliminar recibos","id":35,"checked":True}],[{"name":"Registrar endosos","id":36,"checked":True},{"name":"Eliminar endosos","id":37,"checked":True}],[{"name":"Administrar siniestros","id":38,"checked":True}],[{"name":"Administrar referenciadores","id":39,"checked":True},{"name":"Pagar a referenciadores","id":40,"checked":True},{"name":"Cambiar refrenciador en pólizas","id":41,"checked":True}],[{"name":"Formatos","id":42,"checked":True}],[{"name":"Correos","id":43,"checked":True}],[{"name":"Campañas","id":44,"checked":True}],[{"name":"Mensajeria","id":45,"checked":True}],[{"name":"Agenda","id":46,"checked":True}],[{"name":"Crear paquete","id":47,"checked":True}],[{"name":"Comisiones","id":48,"checked":True}],[{"name":"Administrar archivos sensibles","id":49,"checked":True}]]
            from accounts.models import Permission, UserPermission
            for model in permissions:
                for permission in model:
                        permission_instance = Permission.objects.get(pk = permission['id'])
                        UserPermission.objects.create(
                            profile = profile, 
                            permission = permission_instance, 
                            checked = permission['checked'])

            ui.user_profiles.add(profile)

               
            pre.status = 'ACTIVADO'
            pre.save()

    

    except IntegrityError as e:
        print(e)
        return Response(get_error('integrity_error'), status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    except DatabaseError as e:
        print(e)
        return Response(get_error('database_error'), status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    payload = {
        'name' : org.name,
        'phone' : request.data['phone'],
        'email' : pre.email,
        'plan' : None,
        'organizacion': org.urlname
    }

    token_jwt = get_jwt(user.id, None, payload)
    headers = {
        'Content-Type': 'application/json' ,
        'Authorization': 'Bearer %s' % token_jwt
    }
    r = requests.post(settings.PAYMENT_API_IP + 'clientes/clientes/', json.dumps(payload), headers = headers)


    return Response({
        'accepted':True, 
        'Token': token.key,
        'org': {
            'alias':org.alias, 
            'urlname':org.urlname, 
            'billiable': True,
            'id':org.id, 
            'is_demo' : org_application.is_demo,
        }, 
        'user':{
            'first_name' : user.first_name,
            'last_name' : user.last_name,
            'email' : user.email,
            'is_superuser' : user.is_superuser,
            'is_staff' : user.is_staff,
            'id':user.id
        },
        'userinfo': UserInfoSerializer(ui, context = {'request': request}, many = False).data
    }, status = status.HTTP_201_CREATED)
    # return Response()
    
@api_view(['GET'])
def get_org_info(request, org):
    try:
        org_info = Organization.objects.get(urlname=org)
        app = OrganizationApplication.objects.filter(organization = org_info, application__name = 'SAAM')
        result = {
            'data':{
                'org': {
                    'name': org_info.name, 
                    'alias': org_info.alias, 
                    'urlname': org_info.urlname, 
                    'address': org_info.address, 
                    'phone': org_info.phone, 
                    'phone_mensajeria': org_info.phone_mensajeria, 
                    'phone_sms': org_info.phone_sms, 
                    'auth_token':org_info.auth_token,
                    'account_sid': org_info.account_sid,
                    'messaging_service_sid': org_info.messaging_service_sid,
                    'email': org_info.email, 
                    'webpage': org_info.webpage, 
                    #'logo': org_info.logo.url,
                    'logo': org_info.logo.name,
                    'logo_mini':org_info.logo_mini.name if org_info and org_info.logo_mini else '',
                    'banner': '',
                    'isActive':app[0].is_active if app else False
                    }
                },
                'active':{'val':app[0].is_active if app else False}
            }
    except Exception as e:
        res = {
            'data':{
                'org': {}}}
        print('Exception to get org =>', str(e))
        return Response(res, status=status.HTTP_200_OK)

    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_image_org(request, org=None):
    result=''
    try:
        org = Organization.objects.get(urlname=org)
        try:
            logo = get_url_file(org.logo)
            # logo = org.logo
        except Exception as e:
            logo = org.logo.name
        result = {
                    'logo': logo,
            }
    except Exception as e:
        print('Exception to get  image org =>', str(e))
    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_image_user(request, usname=None):
    try:
        usrname= UserInfo.objects.get(user__username=usname)
        result = {
            # 'logo': settings.MEDIA_URL+str(usrname.avatar) if usrname.avatar else '',
            'logo': get_url_file(usrname.avatar)
            # 'logo': usrname.avatar
        }
    except Exception as e:
        result = {'logo':''}
        print('Exception to get  image user =>', str(e))
    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_email_admin(request):
    try:
        data= {}
        status_code = status.HTTP_200_OK
        emails = UserInfo.objects.filter(org__urlname=request.GET.get('org_id'), role=0, user__is_active = True).annotate(email=F('user__email'), nombre=Concat(F('user__first_name'),Value(' '), F('user__last_name'))).values('email', 'nombre')
        data = {'data':emails}
    except Exception as e:
        data = {'error':str(e)}
        status_code = status.HTTP_400_BAD_REQUEST
    return Response(data, status=status_code)

class OrganizationDataViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationDetailsHyperSerializer
    permission_classes = (permissions.IsAuthenticated, OnlySuperUserPermission )
    pagination_class = None

    def get_queryset(self):
        try:
            activa = self.request.GET.get('activa')
            if activa =='true':
                app_ = Application.objects.filter(name = 'SAAM')
                act = OrganizationApplication.objects.filter(application__in = app_,is_active =True).values_list('organization__urlname',flat=True)
                organizaciones = Organization.objects.filter(urlname__in=act)
            elif activa =='false':
                app_ = Application.objects.filter(name = 'SAAM')
                act = OrganizationApplication.objects.filter(application__in = app_,is_active =False).values_list('organization__urlname',flat=True)
                organizaciones = Organization.objects.filter(urlname__in=act)
            else:
                organizaciones = Organization.objects.all().order_by('urlname')
        except Exception as ers:
            print('------------',ers)
            organizaciones = Organization.objects.all().order_by('urlname')
        # return Organization.objects.all().order_by('urlname')
        return organizaciones


import json
import pandas as pd
@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def report_orgs_data(request):
    # try:
    #     cadena = request.GET.get('cadena')
    # except:
    #     cadena = ''
    try:
        activa = request.GET.get('activa')
        if activa =='true':
            app_ = Application.objects.filter(name = 'SAAM')
            act = OrganizationApplication.objects.filter(application__in = app_,is_active =True).values_list('organization__urlname',flat=True)
            organizaciones = Organization.objects.filter(urlname__in=act)
        elif activa =='false':
            app_ = Application.objects.filter(name = 'SAAM')
            act = OrganizationApplication.objects.filter(application__in = app_,is_active =False).values_list('organization__urlname',flat=True)
            organizaciones = Organization.objects.filter(urlname__in=act)
        else:
            organizaciones = Organization.objects.all().order_by('urlname')
    except Exception as ers:
        print('------------',ers)
        organizaciones = Organization.objects.all().order_by('urlname')
    # if cadena:
    #     words = cadena.split()      
    #     c_filters = [Q(gestor_cobranza__icontains = q) for q in words]
    #     print('cednaaaa',len(organizaciones),cadena)
    #     organizaciones = organizaciones.filter(reduce(and_, c_filters) | Q(urlname__icontains = cadena.lower()))
    #     print('cednaaaa',len(organizaciones),cadena)
    queryset = organizaciones
    # queryset = Organization.objects.all().order_by('urlname')
    organizacioneslista = []
    org_activa=[]
    usuarios = []
    operativos = []
    consulta = []
    superuser = []
    sinacceso = []
    pagadosop = []
    pagadoscon = []
    pricecon = []
    priceop = []
    razon = []
    razont = []
    razone = []
    orgname = []
    numcliente = []
    rfc_gestor=[]
    domiciliado=[]
    recibosvigentes=[]
    u_cr = []
    u_pagados_cr = []
    price_cr = []
    promedio_anual = []
    promedio_mensual = []
    isdemo = []
    comentariocobranza = []
    min_hmeses = datetime.combine(datetime.today(), time.max)          
 
    for org in queryset:
        recibos = Recibos.objects.filter(organization__id= org.id, fecha_inicio__gt=min_hmeses).exclude(status__in=[3,0])
        if recibos:
            recibosvigentes.append('Si')
        else:
            recibosvigentes.append('No')
        numcliente.append(org.num_client)
        domiciliado.append(org.get_conducto_de_pago_display())
        rfc_gestor.append(org.rfc_gestor)
        pagadoscon.append(org.users_payed_con)
        pagadosop.append(org.users_payed_op)
        u_pagados_cr.append(org.users_payed_cr)
        priceop.append(org.price_users_op)
        pricecon.append(org.price_users_con)
        price_cr.append(org.price_users_cr)
        orgname.append(org.name)
        razon.append(org.gestor_cobranza)
        comentariocobranza.append(org.observations_cobranza if org.observations_cobranza else '')
        razont.append(org.phone_gestor)
        razone.append(org.email_gestor)
        organizacioneslista.append(org.urlname)
        promedio_anual.append(org.promedio_anual)
        promedio_mensual.append(org.promedio_mensual)
        usuarios.append(len(UserInfo.objects.filter(org = org,is_active=True).exclude(manage_profile=3)))
        sinacceso.append(len(UserInfo.objects.filter(org = org,is_active=True,manage_profile=0)))
        operativos.append(len(UserInfo.objects.filter(org = org,is_active=True,manage_profile=1)))
        consulta.append(len(UserInfo.objects.filter(org = org,is_active=True,manage_profile=2)))
        superuser.append(len(UserInfo.objects.filter(org = org,is_active=True,manage_profile=3)))
        u_cr.append(len(UserInfo.objects.filter(org = org,is_active=True,manage_profile=4)))
        app_ = Application.objects.filter(name = 'SAAM')
        app = OrganizationApplication.objects.filter(organization = org, application__in = app_)
        if org.is_org_demo:
            isdemo.append('Si')
        else:
            isdemo.append('No')
        if app.exists():
            app = app.first()
            if app.is_active:
                org_activa.append('Activa')
            else:
                org_activa.append('InActiva')
        else:
            org_activa.append('')
    # token_jwt = get_jwt(request.user.id, urlname)
    # payload = {
    #     "Authorization": "Bearer %s" % token_jwt,
    #     'usernames': list(usernames)
    # }
    # headers = {
    #     'Content-Type': 'application/json' ,
    #     'Authorization': 'Bearer %s' % token_jwt
    # }

    # r = requests.post(settings.SAAM_API_IP + 'perfil-usuario-restringido-array-cas/', json.dumps(payload), headers = headers)
    # if(r.status_code == 200):
    #     perfill_restringido = r.json()
    

    df = pd.DataFrame({
        'URL org': organizacioneslista ,  
        'Nombre Organización': orgname ,  
        'SAAM': org_activa ,  
        'Usuarios': usuarios,
        'Usuarios Operativos': operativos ,
        'Usuarios Operativos Pagados': pagadosop ,
        'Precio Operativos': priceop ,
        'Usuarios Consulta': consulta ,
        'Usuarios Consulta Pagados': pagadoscon ,
        'Precio Consulta': pricecon ,
        'Usuarios SuperUsuarios': superuser ,    
        'Usuarios Sin Acceso': sinacceso ,     
        'Usuarios C.Restringida': u_cr ,
        'Usuarios C.Restringida Pagados': u_pagados_cr ,
        'Precio C.Restringida': price_cr ,
        'Razón Social': razon ,     
        'Teléfono': razont ,     
        'Correo Electrónico': razone ,     
        'Número de Cliente': numcliente ,     
        'RFC Razón Social': rfc_gestor ,     
        'Domiciliado': domiciliado ,     
        'Recibos Vigentes': recibosvigentes ,     
        'Promedio(Anual)': promedio_anual ,      
        'Promedio(Mensual)': promedio_mensual,      
        'Demo': isdemo  ,    
        'Comentario Cobranza': comentariocobranza      
    })

    column_order = [
        'URL org',
        'Nombre Organización',
        'Razón Social' ,     
        'Número de Cliente',     
        'RFC Razón Social',     
        'SAAM',
        'Usuarios',
        'Usuarios Operativos',
        'Usuarios Operativos Pagados',
        'Precio Operativos',
        'Usuarios Consulta',
        'Usuarios Consulta Pagados',
        'Precio Consulta',
        'Usuarios C.Restringida',
        'Usuarios C.Restringida Pagados',
        'Precio C.Restringida',
        'Usuarios SuperUsuarios',
        'Usuarios Sin Acceso',    
        'Teléfono' ,     
        'Correo Electrónico'  ,
        'Domiciliado' , 
        'Recibos Vigentes' , 
        'Promedio(Anual)' , 
        'Promedio(Mensual)' ,      
        'Demo',
        'Comentario Cobranza'         
    ]
    import os
    try:
        os.remove('reporte_de_orgs_data_cas.xlsx')
    except:
        pass
    writer = pd.ExcelWriter('reporte_de_orgs_data_cas.xlsx', engine='xlsxwriter')
    # Convert the dataframe to an XlsxWriter Excel object.
    df[column_order].to_excel(writer, sheet_name='Sheet1', index=False)
    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    with open('reporte_de_orgs_data_cas.xlsx',"rb") as f:
        response = HttpResponse(f,content_type='application/msword')
        response['Content-Disposition'] = 'attachment; filename=reporte_de_orgs_data_cas.xlsx'
        os.remove('reporte_de_orgs_data_cas.xlsx')
        return response

@api_view(['GET'])
def get_org_info_all(request):
    try:
        app_ = Application.objects.filter(name = 'SAAM')
        app = OrganizationApplication.objects.filter(application__in = app_).values_list('organization__urlname',flat=True)
        org = Organization.objects.filter(urlname__in=app)
        result=[]
        for r in org:
            result.append(r.urlname)
    except Exception as e:
        print('Exception to get org =>', str(e))

    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_data_receit_stadistic(request):
    result = []
    orgserializer = None
    organizaciones_sin_recibos = []

    try:
        # Optimize the initial query with select_related or prefetch_related
        recibos = Recibos.objects.filter(isActive=True).exclude(status=0).select_related('organization').order_by('organization__id')

        date_now = datetime.now()
        mes3 = date_now + relativedelta(months=3)

        max_3meses = datetime.combine(mes3, time.max)
        min_hmeses = datetime.combine(date_now, time.max)

        since = min_hmeses
        until = max_3meses

        date_filters = [
            Q(fecha_inicio__gt=since),
            Q(fecha_inicio__lte=until)
        ]

        recibos_a_vencer = recibos.filter(status=1).filter(reduce(operator.and_, date_filters))
        recibos_pagados = recibos.filter(status__in=[2,25]).exclude(pk__in=recibos_a_vencer.values_list('pk', flat=True))
        recibos_vencidos = recibos.filter(fecha_inicio__lte=date_now.date(), status=1)\
                                  .exclude(pk__in=recibos_pagados.values_list('pk', flat=True))\
                                  .exclude(pk__in=recibos_a_vencer.values_list('pk', flat=True))

        todos = recibos_a_vencer | recibos_pagados | recibos_vencidos

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(todos.order_by('status'), 10)  # Show 10 items per page

        try:
            todos_page = paginator.page(page)
        except PageNotAnInteger:
            todos_page = paginator.page(1)
        except EmptyPage:
            todos_page = paginator.page(paginator.num_pages)

        todos_ser = RecibosDetailsHyperSerializer(todos_page, context={'request': request}, many=True)

        # Organizations without receipts
        app_ = Application.objects.filter(name='SAAM')
        apporgactive = OrganizationApplication.objects.filter(is_active=True, application__in=app_).values_list('organization', flat=True)
        t = Recibos.objects.filter(fecha_fin__gte=date_now.date()).exclude(status=0).distinct('organization__id').values_list('organization', flat=True)
        organizaciones_sin_recibos = Organization.objects.filter(id__in=apporgactive).exclude(id__in=t)

        orgserializer = OrganizationHyperSerializer(organizaciones_sin_recibos, context={'request': request}, many=True)

        return JsonResponse({
            'data_av': {}, 'total_av': len(recibos_a_vencer),
            'data_p': {}, 'total_p': len(recibos_pagados),
            'data_v': {}, 'total_v': len(recibos_vencidos),
            'todos': todos_ser.data, 'total': paginator.count,
            'num_pages': paginator.num_pages, 'current_page': todos_page.number,
            'organizaciones': orgserializer.data if orgserializer else [], 'total_orgs': len(organizaciones_sin_recibos)
        })

    except Exception as e:
        print('Exception to get receipts statistic =>', str(e))
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_receipt_avencer(request):
    result = []
    orgserializer=None
    organizaciones_sin_recibos=[]
    try:
        recibos = Recibos.objects.filter(isActive=True).exclude(status=0).select_related('organization').order_by('organization__id')

        date_now = datetime.now()
        mes3 = date_now + relativedelta(months=3)

        max_3meses = datetime.combine(mes3, time.max)
        min_hmeses = datetime.combine(date_now, time.max)

        since = min_hmeses
        until = max_3meses

        date_filters = [
            Q(fecha_inicio__gt=since),
            Q(fecha_inicio__lte=until)
        ]

        recibos_a_vencer = recibos.filter(status=1).filter(reduce(operator.and_, date_filters))      
        # Apply pagination
        page = request.GET.get('page', 1)  # Get the page number from request
        paginator = Paginator(recibos_a_vencer, 10)  # Show 10 items per page

        try:
            recibos_a_vencer_page = paginator.page(page)
        except PageNotAnInteger:
            recibos_a_vencer_page = paginator.page(1)
        except EmptyPage:
            recibos_a_vencer_page = paginator.page(paginator.num_pages)

        ser_recibos_a_vencer = RecibosDetailsHyperSerializer(recibos_a_vencer_page, context={'request': request}, many=True)
        return JsonResponse(
            {
                'data_av': ser_recibos_a_vencer.data,
                'total_av': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': recibos_a_vencer_page.number
            }
        )
    except Exception as e:
        print('Exception to get receipts statdicstc =>', str(e))

    return Response(result, status=status.HTTP_200_OK)
@api_view(['GET'])
def get_receipt_pagados(request):
    result = []
    orgserializer=None
    organizaciones_sin_recibos=[]
    try:
        recibos = Recibos.objects.filter(isActive=True).exclude(status=0).select_related('organization').order_by('organization__id')

        date_now = datetime.now()
        mes3 = date_now + relativedelta(months=3)

        max_3meses = datetime.combine(mes3, time.max)
        min_hmeses = datetime.combine(date_now, time.max)

        since = min_hmeses
        until = max_3meses

        date_filters = [
            Q(fecha_inicio__gt=since),
            Q(fecha_inicio__lte=until)
        ]

        recibos_a_vencer = recibos.filter(status=1).filter(reduce(operator.and_, date_filters))
        recibos_pagados = recibos.filter(status__in=[2,25]).exclude(pk__in=recibos_a_vencer.values_list('pk', flat=True))
        # Apply pagination
        page = request.GET.get('page', 1)  # Get the page number from request
        paginator = Paginator(recibos_pagados, 10)  # Show 10 items per page

        try:
            recibos_pagados_page = paginator.page(page)
        except PageNotAnInteger:
            recibos_pagados_page = paginator.page(1)
        except EmptyPage:
            recibos_pagados_page = paginator.page(paginator.num_pages)

        ser_recibos_pagados = RecibosDetailsHyperSerializer(recibos_pagados_page, context={'request': request}, many=True)
        return JsonResponse(
            {
                'data_p': ser_recibos_pagados.data,
                'total_p': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': recibos_pagados_page.number
            }
        )
    except Exception as e:
        print('Exception to get receipts statdicstc =>', str(e))

    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_receipt_vencidos(request):
    result = []
    try:
        recibos = Recibos.objects.filter(isActive=True).exclude(status=0).select_related('organization').order_by('organization__id')

        date_now = datetime.now()
        mes3 = date_now + relativedelta(months=3)

        max_3meses = datetime.combine(mes3, time.max)
        min_hmeses = datetime.combine(date_now, time.max)

        since = min_hmeses
        until = max_3meses

        date_filters = [
            Q(fecha_inicio__gt=since),
            Q(fecha_inicio__lte=until)
        ]

        recibos_a_vencer = recibos.filter(status=1).filter(reduce(operator.and_, date_filters))
        recibos_pagados = recibos.filter(status=2).exclude(pk__in=recibos_a_vencer.values_list('pk', flat=True))
        recibos_vencidos = recibos.filter(fecha_inicio__lte=date_now.date(), status=1)\
                                  .exclude(pk__in=recibos_pagados.values_list('pk', flat=True))\
                                  .exclude(pk__in=recibos_a_vencer.values_list('pk', flat=True))
        # Apply pagination
        page = request.GET.get('page', 1)  # Get the page number from request
        paginator = Paginator(recibos_vencidos, 10)  # Show 10 items per page

        try:
            recibos_vencidos_page = paginator.page(page)
        except PageNotAnInteger:
            recibos_vencidos_page = paginator.page(1)
        except EmptyPage:
            recibos_vencidos_page = paginator.page(paginator.num_pages)

        ser_recibos_vencidos = RecibosDetailsHyperSerializer(recibos_vencidos_page, context={'request': request}, many=True)

        return JsonResponse(
            {
                'data_v': ser_recibos_vencidos.data,
                'total_v': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': recibos_vencidos_page.number
            }
        )
    except Exception as e:
        print('Exception to get receipts statdicstc =>', str(e))

    return Response(result, status=status.HTTP_200_OK)
# Actualizar recibos subsecuentes
@api_view(['POST'])
def update_receipts_subsec(request):
    result = []
    try:
        referencia_actual =request.data['id']
        org =request.data['org']
        recibo = Recibos.objects.get(id= referencia_actual)
        recibos_subs = Recibos.objects.filter(organization__id= org, status=1,isActive=True)
        try:
            fecha_recibo= recibo.fecha_inicio
            recibos_to_upd = recibos_subs.filter(fecha_inicio__gt=fecha_recibo).update(monto=recibo.monto,monto_total=recibo.monto_total)
            # ---------
            return JsonResponse(
                {'data':len(recibos_subs.filter(fecha_inicio__gt=fecha_recibo))}
            )
        except Exception as err:
            now = datetime.now()
            print('upd ssc error',now,err)
    except Exception as e:
        print('Exception upd subsc Recs =>', str(e))

    return Response(result, status=status.HTTP_200_OK)

class RecibosViewSet(viewsets.ModelViewSet):
    serializer_class = RecibosHyperSerializer
    permission_classes = (IsAuthenticated, OnlySuperUserPermission)
    def get_queryset(self):
        org_id = int(self.request.GET.get('org', 0))
        if org_id:
            today = datetime.today().date()
            recibos_qs = Recibos.objects.filter(organization__id=org_id).order_by('fecha_inicio')
            # --- search filter ---
            search = self.request.GET.get('search')
            if search:
                recibos_qs = recibos_qs.filter(organization__name__icontains=search)
            # ---------------------
            try:
                recibo_actual = recibos_qs.filter(fecha_inicio__lte=today, fecha_fin__gte=today)[0]
            except Recibos.DoesNotExist:
                return Recibos.objects.none()

            recibos = list(
                recibos_qs.filter(fecha_inicio__lt=recibo_actual.fecha_inicio).order_by('-fecha_inicio')[:3]
            )
            recibos.reverse()  # para que los anteriores estén en orden cronológico

            recibos.append(recibo_actual)

            siguientes = list(
                recibos_qs.filter(fecha_inicio__gt=recibo_actual.fecha_inicio).order_by('fecha_inicio')[:3]
            )
            recibos.extend(siguientes)

            return Recibos.objects.filter(id__in=[r.id for r in recibos]).order_by('fecha_inicio')
        try:
            recibos_qs = Recibos.objects.all().order_by('-id')
            # --- search filter ---
            search = self.request.GET.get('search')
            if search:
                recibos_qs = recibos_qs.filter(organization__name__icontains=search)
            # ---------------------
            recibos = recibos_qs
        except Exception as ers:
            recibos = Recibos.objects.all().order_by('-id')
        return recibos
    def perform_create(self, serializer):
        org_=Organization.objects.get(pk = self.request.data['organization'])
        # parsed_date = datetime.strptime(self.request, "%Y-%m-%d")
        # new_date = parsed_date + timedelta(days=1)
        orgdata=OrganizationHyperSerializer(org_, context={'request': self.request}, many=False)
        obj = serializer.save(
            organization= org_,
            org_name =orgdata.data['urlname']
        )

    def partial_update(self, request, pk=None):
        queryset = Recibos.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        serializer = RecibosHyperSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# Filtro por org Recibos CAS 
@api_view(['GET'])
@permission_classes((IsAuthenticated, OnlySuperUserPermission))
def RecibosByOrg(request):
    # serializer_class = RecibosDetailsHyperSerializer
    recibos = None
    try:
        org = request.GET.get('orgname')
        try:
            organization=Organization.objects.get(urlname = org)
        except:
            organization=Organization.objects.get(id = org)
        recibos = Recibos.objects.filter(organization=organization).order_by('recibo_numero')
        serializer  = RecibosDetailsHyperSerializer(recibos.order_by('status'), context = {'request':request}, many = True)
        return JsonResponse(
            {'total':len(recibos.order_by('fecha_inicio')), 'data':serializer.data}
        )
    except Exception as ers:
        print('eeee',ers)
        if request.GET.get('org'):
            organization=Organization.objects.get(pk = request.GET.get('org'))
            print('org def',organization)
            recibos = Recibos.objects.filter(organization=organization,isActive=True).order_by('fecha_inicio')
            serializer  = RecibosDetailsHyperSerializer(recibos.order_by('fecha_inicio'), context = {'request':request}, many = True)
            return JsonResponse(
                {'total':len(recibos.order_by('fecha_inicio')), 'data':serializer.data}
            )
        else:
            return JsonResponse({'data':[],'error':str(ers)},status=400)

class RecibosTodosDataViewSet(viewsets.ModelViewSet):
    serializer_class = RecibosDetailsHyperSerializer
    permission_classes = (permissions.IsAuthenticated, OnlySuperUserPermission )
    pagination_class = None

    def get_queryset(self):
        try:
            recibos = Recibos.objects.filter(isActive=True).exclude(status=0).order_by('id')
        except Exception as ers:
            recibos = Recibos.objects.filter(isActive=True).exclude(status=0).order_by('id')
        return 
# file


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cargar_excel_pagos(request):
    if request.method == 'POST' and 'archivo' in request.FILES:
        archivo = request.FILES['archivo']
        
        try:
            # Abrir el archivo Excel
            book = xlrd.open_workbook(file_contents=archivo.read())
            sheet_ok = book.sheet_by_index(0)

            # Inicializar una lista para almacenar los resultados
            resultados = []

            for r in range(1, sheet_ok.nrows):
                rid = int(sheet_ok.cell_value(rowx=r, colx=0))
                fechaok = None

                try:
                    # Procesar la fecha si es aplicable
                    fechaok_tuple = xlrd.xldate_as_tuple(sheet_ok.cell_value(rowx=r, colx=1), book.datemode)
                    if fechaok_tuple:
                        nuevaok = str(fechaok_tuple[0])+'-'+str(fechaok_tuple[1])+'-'+str(fechaok_tuple[2])
                        fechaok = nuevaok

                except Exception as f:
                    print('Error al procesar la fecha:', f)
 
                if request.data.get('accion') == "aplicar":
                    try:
                        rec = Recibos.objects.get(id=rid)
                        if rec.status == 1:
                            rec.status = 2
                            if fechaok:
                                rec.fecha_pago = fechaok
                            rec.save()
                        else:
                            resultados.append({
                                'id': rid,
                                'status': 'Estatus no aplicable'
                            })
                    except Recibos.DoesNotExist:
                        pass
                    except Exception as er:
                        print('Error al actualizar el registro:', er)
                        return Response({'error': 'Error al actualizar el registro {}'.format(rid), 'detalle': str(er)}, status=500)


                elif request.data.get('accion') == "validar":
                    # Solo consultar el estatus
                    try:
                        rec = Recibos.objects.get(id=rid)
                        estatus = rec.status
                        fecha_pago = rec.fecha_pago
                        resultados.append({
                            'id': rid,
                            'estatus': estatus,
                            'fecha':fecha_pago
                        })
                    except Recibos.DoesNotExist:
                        resultados.append({
                            'id': rid,
                            'estatus': 'Registro inexistente',
                            'fecha': '-'
                        })
                    except Exception as er:
                        print('Error al consultar el registro:', er)
                        return Response({'error': 'Error al consultar el registro {}'.format(rid), 'detalle': str(er)}, status=500)

                    

            if request.data.get('accion') == "validar":
                resultados_ordenados = sorted(resultados, key=lambda x: x['id'])
                return Response({'resultados': resultados_ordenados}, status=200)

            # Si la acción fue "aplicar", devolver una respuesta exitosa
            return Response({'resultados': resultados, 'message': 'Archivo procesado correctamente'}, status=200)
        
        except Exception as e:
            return Response({'error': 'Error al procesar el archivo {}', 'detalle': str(er)}, status=500)

    return Response({'error': 'Archivo no válido'}, status=400)


# Fitro dash Recibos CAS 
@api_view(['POST'])
@permission_classes((IsAuthenticated, OnlySuperUserPermission))
def filterRecibosDash(request):
    try:
        # Retrieve filters from request
        org = request.data.get('organizacion', '')
        fechainicial = request.data.get('fechainicial', '')
        fechafin = request.data.get('fechafin', '')
        estatus = request.data.get('status', '')

        # Initial filtering for active receipts
        recibos = Recibos.objects.filter(isActive=True).exclude(status=0)

        # Apply additional filters based on provided criteria
        if org:
            recibos = recibos.filter(organization__id=org)
        if fechainicial and fechafin:
            recibos = recibos.filter(fecha_inicio__gte=fechainicial, fecha_inicio__lte=fechafin)
        if estatus and estatus != '0':
            recibos = recibos.filter(status=estatus)

        # Order by status
        recibos = recibos.order_by('status')

        # Pagination
        page = request.data.get('page', 1)
        page_size = request.data.get('page_size', 10)
        paginator = Paginator(recibos, page_size)
        paginated_recibos = paginator.get_page(page)

        # Serialization
        serializer = RecibosDetailsHyperSerializer(paginated_recibos, context={'request': request}, many=True)

        return JsonResponse({
            'total': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': paginated_recibos.number,
            'data': serializer.data
        })

    except Exception as e:
        print('Exception occurred =>', str(e))
        return JsonResponse({'error': 'An error occurred while processing your request'}, status=500)


# Reporte Recibos Dash CAS
@api_view(['POST'])
@permission_classes((IsAuthenticated, OnlySuperUserPermission))
def reportFilterRecibosDash(request):
    consulta=False
    try:
        consulta = request.data.get('consulta', False)
        # org = request.data.get('organizacion', '')
        # fechainicial = request.data.get('fechainicial', '')
        # fechafin = request.data.get('fechafin', '')
        # estatus = request.data.get('status', '')
        # recibos = Recibos.objects.filter(isActive=True).exclude(status=0)
        # if org:
        #     recibos = recibos.filter(organization__id=org)
        
        # if fechainicial and fechafin:
        #     recibos = recibos.filter(fecha_inicio__gte=fechainicial, fecha_inicio__lte=fechafin)
        
        # if estatus and estatus != '0':
        #     recibos = recibos.filter(status=estatus)

        # recibos = recibos.order_by('status')
        # Retrieve filters from request
        org = request.data.get('organizacion', '')
        fechainicial = request.data.get('fechainicial', '')
        fechafin = request.data.get('fechafin', '')
        estatus = request.data.get('status', '')

        # Initial filtering for active receipts
        recibos = Recibos.objects.filter(isActive=True).exclude(status=0)

        # Apply additional filters based on provided criteria
        if org:
            recibos = recibos.filter(organization__id=org)
        if fechainicial and fechafin:
            recibos = recibos.filter(fecha_inicio__gte=fechainicial, fecha_inicio__lte=fechafin)
        if estatus and estatus != '0':
            recibos = recibos.filter(status=estatus)

        # Order by status
        recibos = recibos.order_by('status')
        recibos_2 = recibos.order_by('status')
        try:
            date_now = datetime.now()
            mes3 = date_now + relativedelta(months=3)
            since = datetime.combine(date_now, time.max)
            until = datetime.combine(mes3, time.max)

            # Filters "a vencer", "pagados", and "vencidos"
            if not fechainicial and not fechafin:
                date_filters2 = Q(fecha_inicio__gte=since) & Q(fecha_inicio__lte=until)

                recibos_a_vencer = recibos.filter(status=1).filter(date_filters2)
                recibos_pagados = recibos.filter(status__in=[2,25]).exclude(pk__in=recibos_a_vencer.values_list('pk', flat=True))
                recibos_vencidos = recibos.filter(
                    Q(fecha_inicio__lte=date_now.date()) & Q(status=1)
                ).exclude(pk__in=recibos_pagados.values_list('pk', flat=True)) \
                .exclude(pk__in=recibos_a_vencer.values_list('pk', flat=True))

                recibos = recibos_a_vencer | recibos_pagados | recibos_vencidos

        except Exception as err:
            print("Error updating report: ",datetime.now(),err)

    except Exception as err:
        print("General error:",err)
    queryset = recibos
    recibon = []
    calsificado=[]
    orga=[]
    statuslist = []
    monto = []
    montototal = []
    formapago = []
    fechai = []
    fechaf = []
    fechav = []
    org_activa = []   
    fechap = []   
    razons = []   
    razont = []   
    razone = []   
    concepto = []   
    numcliente = []
    rfc_gestor=[]
    domiciliado=[]
    numeros_factura = []
    idr=[]
    cobranzaPendiente = []
    orgActiva = []
    promedioMensual = []
    promedioAnual = []
    # Nuevas listas para archivos asociados
    factura_ok = []
    comprobante_ok = []
    complemento_ok = []
    comentarioorg = []
    comentariorecibo = []

    if consulta:
        for rec in queryset:
            recibon.append(rec.recibo_numero)
            comentariorecibo.append(rec.observations if rec.observations else '')
            if rec.isextra:
                concepto.append(rec.description)
            else:
                concepto.append('')
            numeros_factura.append(rec.numero_factura)
            numcliente.append(rec.organization.num_client)
            promedioMensual.append(rec.organization.promedio_mensual)
            promedioAnual.append(rec.organization.promedio_anual)
            domiciliado.append(rec.organization.get_conducto_de_pago_display())
            rfc_gestor.append(rec.organization.rfc_gestor)
            orga.append(rec.organization.urlname if rec.organization else '')
            razons.append(rec.organization.gestor_cobranza if rec.organization else '')
            razont.append(rec.organization.phone_gestor if rec.organization else '')
            razone.append(rec.organization.email_gestor if rec.organization else '')
            comentarioorg.append(rec.organization.observations_cobranza if rec.organization else '')
            fechap.append(rec.fecha_pago)
            statuslist.append(rec.get_status_display())
            formapago.append(rec.get_forma_pago_display())
            monto.append('$ ' + '{:,.2f}'.format(rec.monto))
            montototal.append('$ ' + '{:,.2f}'.format(rec.monto_total))
            fechai.append(rec.fecha_inicio)
            idr.append(rec.id)
            fechaf.append(rec.fecha_fin)
            fechav.append(rec.vencimiento)
            if rec.organization.cobranza_pendiente:
                cobranzaPendiente.append('Activado')
            else:
                cobranzaPendiente.append('Desactivada')
            app_ = Application.objects.filter(name = 'SAAM')
            app = OrganizationApplication.objects.filter(organization__id = rec.organization.id, application__in = app_)
            if app.exists():
                app = app.first()
                if app.is_active:
                    org_activa.append('Activa')
                    orgActiva.append('')
                else:
                    org_activa.append('InActiva')
                    orgActiva.append('Su Organización ha sido desactivada por Falta de Pago, comuniquese a finanzas@miurabox.com')
            else:
                org_activa.append('')
                orgActiva.append('')
            calsificado.append('')
            # Archivos asociados
            factura_ok.append('Sí' if RecibosFile.objects.filter(owner=rec, tipo=1).exists() else 'No')
            comprobante_ok.append('Sí' if RecibosFile.objects.filter(owner=rec, tipo=2).exists() else 'No')
            complemento_ok.append('Sí' if RecibosFile.objects.filter(owner=rec, tipo=3).exists() else 'No')
    else: 
        for recav in recibos_a_vencer:
            comentariorecibo.append(recav.observations if recav.observations else '')
            recibon.append(recav.recibo_numero)
            if recav.isextra:
                concepto.append(recav.description)
            else:
                concepto.append('')
            numcliente.append(recav.organization.num_client)
            promedioMensual.append(recav.organization.promedio_mensual)
            promedioAnual.append(recav.organization.promedio_anual)
            domiciliado.append(recav.organization.get_conducto_de_pago_display())
            rfc_gestor.append(recav.organization.rfc_gestor)
            orga.append(recav.organization.urlname if recav.organization else '')
            razons.append(recav.organization.gestor_cobranza if recav.organization else '')
            comentarioorg.append(recav.organization.observations_cobranza if recav.organization else '')
            razont.append(recav.organization.phone_gestor if recav.organization else '')
            razone.append(recav.organization.email_gestor if recav.organization else '')
            fechap.append(recav.fecha_pago)
            statuslist.append(recav.get_status_display())
            formapago.append(recav.get_forma_pago_display())
            monto.append('$ ' + '{:,.2f}'.format(recav.monto))
            montototal.append('$ ' + '{:,.2f}'.format(recav.monto_total))
            fechai.append(recav.fecha_inicio)
            fechaf.append(recav.fecha_fin)
            idr.append(recav.id)
            fechav.append(recav.vencimiento)
            app_ = Application.objects.filter(name = 'SAAM')
            app = OrganizationApplication.objects.filter(organization__id = recav.organization.id, application__in = app_)
            if app.exists():
                app = app.first()
                if app.is_active:
                    org_activa.append('Activa')
                else:
                    org_activa.append('InActiva')
            else:
                org_activa.append('')
            calsificado.append('A vencer (3 meses aprox.)')
            factura_ok.append('Sí' if RecibosFile.objects.filter(owner=recav, tipo=1).exists() else 'No')
            comprobante_ok.append('Sí' if RecibosFile.objects.filter(owner=recav, tipo=2).exists() else 'No')
            complemento_ok.append('Sí' if RecibosFile.objects.filter(owner=recav, tipo=3).exists() else 'No')
        for recp in recibos_pagados:
            recibon.append(recp.recibo_numero)
            comentariorecibo.append(recp.observations if recp.observations else '')
            if recp.isextra:
                concepto.append(recp.description)
            else:
                concepto.append('')
            numcliente.append(recp.organization.num_client)
            promedioMensual.append(recp.organization.promedio_mensual)
            promedioAnual.append(recp.organization.promedio_anual)
            domiciliado.append(recp.organization.get_conducto_de_pago_display())
            rfc_gestor.append(recp.organization.rfc_gestor)
            orga.append(recp.organization.urlname if recp.organization else '')
            razons.append(recp.organization.gestor_cobranza if recp.organization else '')
            comentarioorg.append(recp.organization.observations_cobranza if recp.organization else '')
            razont.append(recp.organization.phone_gestor if recp.organization else '')
            razone.append(recp.organization.email_gestor if recp.organization else '')
            fechap.append(recp.fecha_pago)
            statuslist.append(recp.get_status_display())
            formapago.append(recp.get_forma_pago_display())
            monto.append('$ ' + '{:,.2f}'.format(recp.monto))
            montototal.append('$ ' + '{:,.2f}'.format(recp.monto_total))
            fechai.append(recp.fecha_inicio)
            fechaf.append(recp.fecha_fin)
            idr.append(recp.id)
            fechav.append(recp.vencimiento)
            app_ = Application.objects.filter(name = 'SAAM')
            app = OrganizationApplication.objects.filter(organization__id = recp.organization.id, application__in = app_)
            if app.exists():
                app = app.first()
                if app.is_active:
                    org_activa.append('Activa')
                else:
                    org_activa.append('InActiva')
            else:
                org_activa.append('')
            calsificado.append('Pagados')
            factura_ok.append('Sí' if RecibosFile.objects.filter(owner=recp, tipo=1).exists() else 'No')
            comprobante_ok.append('Sí' if RecibosFile.objects.filter(owner=recp, tipo=2).exists() else 'No')
            complemento_ok.append('Sí' if RecibosFile.objects.filter(owner=recp, tipo=3).exists() else 'No')
        for recv in recibos_vencidos:
            comentariorecibo.append(recv.observations if recv.observations else '')
            recibon.append(recv.recibo_numero)
            if recv.isextra:
                concepto.append(recv.description)
            else:
                concepto.append('')
            numcliente.append(recv.organization.num_client)
            promedioMensual.append(recv.organization.promedio_mensual)
            promedioAnual.append(recv.organization.promedio_anual)
            domiciliado.append(recv.organization.get_conducto_de_pago_display())
            rfc_gestor.append(recv.organization.rfc_gestor)
            orga.append(recv.organization.urlname if recv.organization else '')
            razons.append(recv.organization.gestor_cobranza if recv.organization else '')
            comentarioorg.append(recv.organization.observations_cobranza if recv.organization else '')
            razont.append(recv.organization.phone_gestor if recv.organization else '')
            razone.append(recv.organization.email_gestor if recv.organization else '')
            fechap.append(recv.fecha_pago)
            statuslist.append(recv.get_status_display())
            formapago.append(recv.get_forma_pago_display())
            monto.append('$ ' + '{:,.2f}'.format(recv.monto))
            montototal.append('$ ' + '{:,.2f}'.format(recv.monto_total))
            fechai.append(recv.fecha_inicio)
            fechaf.append(recv.fecha_fin)
            fechav.append(recv.vencimiento)
            idr.append(recv.id)
            app_ = Application.objects.filter(name = 'SAAM')
            app = OrganizationApplication.objects.filter(organization__id = recv.organization.id, application__in = app_)
            if app.exists():
                app = app.first()
                if app.is_active:
                    org_activa.append('Activa')
                else:
                    org_activa.append('InActiva')
            else:
                org_activa.append('')
            calsificado.append('Vencidos')
            factura_ok.append('Sí' if RecibosFile.objects.filter(owner=recv, tipo=1).exists() else 'No')
            comprobante_ok.append('Sí' if RecibosFile.objects.filter(owner=recv, tipo=2).exists() else 'No')
            complemento_ok.append('Sí' if RecibosFile.objects.filter(owner=recv, tipo=3).exists() else 'No')

    if consulta:
        df = pd.DataFrame({
            'Organización': orga ,  
            'SAAM': org_activa ,  
            'Información': orgActiva ,  
            'Cobranza': cobranzaPendiente ,  
            'Concepto': concepto,
            'Serie Recibo': recibon,
            'Estado Recibo': statuslist,
            'Monto': monto ,
            'Monto Total': montototal ,    
            'Fecha Inicio': fechai ,     
            'Fecha Fin': fechaf ,     
            'Fecha Vencimiento': fechav ,       
            'Fecha Pago': fechap ,
            'Forma Pago': formapago ,
            'Razón Social': razons ,
            'Teléfono': razont ,
            'Correo Electrónico': razone ,   
            'Número de Cliente': numcliente ,     
            'RFC Razón Social': rfc_gestor ,     
            'Domiciliado': domiciliado , 
            'Promedio ORG(Anual)': promedioAnual , 
            'Promedio ORG(Mensual)': promedioMensual , 
            'Número Factura': numeros_factura,
            'ID': idr ,
            'Factura': factura_ok,
            'Comprobante': comprobante_ok,
            'Complemento': complemento_ok,
            'Comentario Cobranza Organización':comentarioorg,
            'Comentario Cobranza Recibo':comentariorecibo,
        })

        column_order = [
            'Organización',
            'Razón Social' ,   
            'Información',  
            'Cobranza',    
            'Número de Cliente',     
            'RFC Razón Social',  
            'SAAM',
            'Concepto',
            'Serie Recibo',
            'Estado Recibo',
            'Monto',
            'Monto Total',
            'Fecha Inicio',
            'Fecha Fin',
            'Fecha Vencimiento',
            'Fecha Pago',
            'Forma Pago',
            'Teléfono',
            'Correo Electrónico', 
            'Domiciliado'  ,
            'Promedio ORG(Anual)', 
            'Promedio ORG(Mensual)' ,
            'Número Factura',
            'ID',
            'Factura',
            'Comprobante',
            'Complemento',
            'Comentario Cobranza Organización',
            'Comentario Cobranza Recibo',
        ]
    else:
        df = pd.DataFrame({
            'Organización': orga ,  
            'SAAM': org_activa ,  
            'Concepto': concepto,
            'Serie Recibo': recibon,
            'Estado Recibo': statuslist,
            'Forma Pago': formapago ,
            'Monto': monto ,
            'Monto Total': montototal ,    
            'Fecha Inicio': fechai ,     
            'Fecha Fin': fechaf ,     
            'Fecha Vencimiento': fechav ,     
            'Fecha Pago': fechap ,
            'Estado General': calsificado ,        
            'Forma Pago': formapago ,
            'Razón Social': razons ,
            'Teléfono': razont ,
            'Correo Electrónico': razone , 
            'Número de Cliente': numcliente ,     
            'RFC Razón Social': rfc_gestor ,     
            'Domiciliado': domiciliado , 
            'Promedio ORG(Anual)': promedioAnual , 
            'Promedio ORG(Mensual)': promedioMensual , 
            'ID': idr ,
            'Factura': factura_ok,
            'Comprobante': comprobante_ok,
            'Complemento': complemento_ok,
            'Comentario Cobranza Organización':comentarioorg,
            'Comentario Cobranza Recibo':comentariorecibo,
        })

        column_order = [
            'Organización',
            'Razón Social' ,     
            'Número de Cliente',     
            'RFC Razón Social',  
            'SAAM',
            'Concepto',
            'Serie Recibo',
            'Estado Recibo',
            'Forma Pago',
            'Monto',
            'Monto Total',
            'Fecha Inicio',
            'Fecha Fin',
            'Fecha Vencimiento',
            'Fecha Pago',
            'Estado General',
            'Teléfono',
            'Correo Electrónico',
            'Domiciliado',
            'Promedio ORG(Anual)', 
            'Promedio ORG(Mensual)', 
            'ID',
            'Factura',
            'Comprobante',
            'Complemento',
            'Comentario Cobranza Organización',
            'Comentario Cobranza Recibo',
        ]
    import os
    try:
        os.remove('reporte_de_recibosdash_cas.xlsx')
    except:
        pass
    writer = pd.ExcelWriter('reporte_de_recibosdash_cas.xlsx', engine='xlsxwriter')
    # Convert the dataframe to an XlsxWriter Excel object.
    df[column_order].to_excel(writer, sheet_name='Sheet1', index=False)
    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    with open('reporte_de_recibosdash_cas.xlsx',"rb") as f:
        response = HttpResponse(f,content_type='application/msword')
        response['Content-Disposition'] = 'attachment; filename=reporte_de_recibosdash_cas.xlsx'
        os.remove('reporte_de_recibosdash_cas.xlsx')
        return response

# Filtro por org Recibos CAS 
@api_view(['GET'])
@permission_classes((IsAuthenticated, OnlySuperUserPermission))
def RecibosARenovarByOrg(request):
    recibos = None
    try:        
        # *****************
        date_now = datetime.now()
        dentro_de_anio_y_semana = date_now + relativedelta(years=1, weeks=1)
        dentro_de_un_mes = date_now + relativedelta(months=1)
        mes3 = date_now + relativedelta(months=3)
        date_3 = [Q(fecha_inicio__month__lte=mes3.month, fecha_inicio__day__lte=mes3.day, 
            fecha_inicio__year__lte=mes3.year),Q(fecha_inicio__month__gte=date_now.month, 
            fecha_inicio__day__gte=date_now.day, 
            fecha_inicio__year__gte=date_now.year)]
        max_3meses = datetime.combine(mes3, time.max) 
        min_hmeses = datetime.combine(date_now, time.max)
        f = "%Y-%m-%d"        
        since = datetime.strptime(str(min_hmeses.date()) , f)
        until = datetime.strptime(str(max_3meses.date()), f)
        date_filters = [Q(fecha_inicio__gt=since),Q(fecha_inicio__lte = until)]      
        # -----------------
        app_ = Application.objects.filter(name = 'SAAM')
        organizationsList = OrganizationApplication.objects.filter(application__in = app_, 
            is_active=True).values_list('organization', flat=True)
        # ---------------------------
        date_filters3 = [Q(fecha_fin__gte=since),Q(fecha_fin__lte = until)]
        apporgactive = organizationsList
        t = Recibos.objects.filter(fecha_fin__gte = mes3.date()).exclude(status=0).distinct('organization__id').values_list('organization',flat=True)
        orgren = Organization.objects.filter(id__in=apporgactive).exclude(id__in=t)
        orgrenserializer = OrganizationHyperSerializer(orgren, context = {'request':request}, many = True)
        return JsonResponse(
        {'data':orgrenserializer.data if orgrenserializer else [],
        'organizaciones':len(orgren)})
           
        # ++++++++++++++++++
    except Exception as ers:
        print('eeee',ers)
    return JsonResponse({'data':[],'error':''},status=400)

# buscador control de usuarios organizaciones por nombre(urlname) o razón social
@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_organizations_name_gestor(request):
    cadena = request.GET.get('cadena')
    words = cadena.split()      
    c_filters = [Q(gestor_cobranza__icontains = q) for q in words]
    queryset = Organization.objects.filter(reduce(and_, c_filters) | Q(urlname__icontains = cadena.lower()))
    serializer  = OrganizationDetailsHyperSerializer(queryset, context = {'request':request}, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_organizactions_control(request):
    try:
        activa = request.GET.get('activa')
        if activa =='true':
            app_ = Application.objects.filter(name = 'SAAM')
            act = OrganizationApplication.objects.filter(application__in = app_,is_active =True).values_list('organization__urlname',flat=True)
            organizaciones = Organization.objects.filter(urlname__in=act)
        elif activa =='false':
            app_ = Application.objects.filter(name = 'SAAM')
            act = OrganizationApplication.objects.filter(application__in = app_,is_active =False).values_list('organization__urlname',flat=True)
            organizaciones = Organization.objects.filter(urlname__in=act)
        else:
            organizaciones = Organization.objects.all().order_by('urlname')
    except Exception as ers:
        print('------------',ers)
        organizaciones = Organization.objects.all().order_by('urlname')    
    serializer  = OrganizationDetailsHyperSerializer(organizaciones, context = {'request':request}, many = True)
    data = {}

    users_1 = len(UserInfo.objects.filter(org__id__in = organizaciones.values_list('id'),is_active=True,manage_profile=1))

    users_2 = len(UserInfo.objects.filter(org__id__in = organizaciones.values_list('id'),is_active=True,manage_profile=2))

    users_3 = len(UserInfo.objects.filter(org__id__in = organizaciones.values_list('id'),is_active=True,manage_profile=4))
    mensual = organizaciones.aggregate(Sum('promedio_mensual'))
    anual = organizaciones.aggregate(Sum('promedio_anual'))
    users_payed_op = organizaciones.annotate(as_float=Cast('users_payed_op', FloatField())).aggregate(Sum('as_float'))
    users_payed_con = organizaciones.annotate(as_float=Cast('users_payed_con', FloatField())).aggregate(Sum('as_float'))
    users_payed_cr = organizaciones.annotate(as_float=Cast('users_payed_cr', FloatField())).aggregate(Sum('as_float'))
                                 
    existen_sin_promedio = False
    organizaciones_demos = organizaciones.filter((Q(promedio_mensual = 0) |Q(promedio_anual = 0)),is_org_demo = False).exists()
    if organizaciones_demos:
        existen_sin_promedio = True
    data['data'] = serializer.data
    data['sumas'] = {'mensual':mensual,'anual':anual,'existen_sin_promedio':existen_sin_promedio,'users_payed_op':users_payed_op,
                     'users_payed_con':users_payed_con,'users_payed_cr':users_payed_cr,'operativos':users_1,'consulta':users_2,'crestringida':users_3}
    return Response(data)

# *************
class CarouselViewSet(viewsets.ModelViewSet):
    serializer_class = CarouselDetailsSerializer
    permission_classes = (IsAuthenticated, OnlySuperUserPermission )

    def get_queryset(self):
        try:
            itemsCarousel = CarouselGeneral.objects.filter(visible =True).order_by('-id')
        except Exception as ers:
            itemsCarousel = CarouselGeneral.objects.filter(visible =True).order_by('-id')

        return itemsCarousel

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        queryset = CarouselGeneral.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        serializer = CarouselDetailsSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
@api_view(['GET'])
def get_carousel_items(request, org):
    try:        
        try:
            itemsCarousel = CarouselGeneral.objects.filter(visible =True).order_by('-id')
        except Exception as ers:
            itemsCarousel = CarouselGeneral.objects.filter(visible =True).order_by('-id')
        serializer = CarouselDetailsSerializer(itemsCarousel,context = {'request':request}, many = True)
        result = {
            'data':serializer.data
            }
    except Exception as e:
        res = {
            'data':{}}
        print('Exception to get carousel =>', str(e))
        return Response(res, status=status.HTTP_400_BAD_REQUEST)
    return Response(result, status=status.HTTP_200_OK)
#  SAAM LITE
# crear organización saam lite
class OrganizationSaamLiteViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationHyperSerializer
    permission_classes = (AllowAny, )
    def get_queryset(self):
        try:
            activa = self.request.GET.get('active')
            if activa =='true':
                app_ = Application.objects.filter(name = 'SAAM')
                act = OrganizationApplication.objects.filter(application__in = app_,is_active =True).values_list('organization__urlname',flat=True)
                organizaciones = Organization.objects.filter(Q(urlname__in=act)).distinct('urlname')
            elif activa =='false':
                app_ = Application.objects.filter(name = 'SAAM')
                act = OrganizationApplication.objects.filter(application__in = app_,is_active =False).values_list('organization__urlname',flat=True)
                intersection = set(act) 
                organizaciones = Organization.objects.filter(urlname__in=intersection).distinct('urlname')
                orgs=[]
            else:
                organizaciones = Organization.objects.all().order_by('-id')
        except Exception as ers:
            organizaciones = Organization.objects.all().order_by('-id')
        return organizaciones

    def create(self, request, *args, **kwargs):
        if 'info_org' in request.data:
            org_info_list = request.data.pop('info_org')
        else:
            org_info_list = []

        # if not request.user.is_superuser:
        #     return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data = request.data, many = isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        for org_info in org_info_list:
            app = Application.objects.get(name=org_info['name'])
            org_app, created = OrganizationApplication.objects.get_or_create(organization=obj, application=app)
            org_app.is_active = org_info['is_active']
            org_app.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        queryset = Organization.objects.all()
        cf = get_object_or_404(queryset, pk=pk)
        # Revisamos que no se quiera actualizar un registro con el mismo urlname de una organizacion ya existente
        if 'urlname' in request.data and Organization.objects.filter(urlname = request.data['urlname']).exclude(id = cf.id).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if 'info_org' in request.data:
            org_info_list = request.data.pop('info_org')
            for org_info in org_info_list:
                app = Application.objects.get(name=org_info['name'])
                org_app, created = OrganizationApplication.objects.get_or_create(organization=Organization.objects.get(pk=pk), application=app)
                org_app.is_active = org_info['is_active']
                org_app.save()

        serializer = OrganizationHyperSerializer(cf, context={'request': request}, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# Vista para exponer PlantillaCorreo
class PlantillaCorreoViewSet(viewsets.ModelViewSet):
    queryset = PlantillaCorreo.objects.all().order_by('-id')
    serializer_class = PlantillaCorreoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    
    

# Vista para exponer CorreoRecibo
from .models import CorreoRecibo
from .serializers import CorreoReciboSerializer

import re, random, base64


class CorreoReciboViewSet(viewsets.ModelViewSet):
    serializer_class = CorreoReciboSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        queryset = CorreoRecibo.objects.all().order_by('-id')
        recibo_id = self.request.query_params.get('recibo_id')
        print(recibo_id)
        if recibo_id:
            queryset = queryset.filter(recibo__id=recibo_id)
        return queryset

    def perform_create(self, serializer):
        correo = serializer.save()
        0
        try:
            asunto = correo.subject
            mensaje = correo.message
            mensaje = mensaje.replace('nombre_cliente',str(correo.recibo.organization.gestor_cobranza) if correo.recibo.organization.gestor_cobranza else ''   )
            mensaje = mensaje.replace('nombre_organizacion',str(correo.recibo.organization.name) if correo.recibo.organization.name else '' )
            mensaje = mensaje.replace('monto_total', "$ %s MXN"%(correo.recibo.monto_total) if correo.recibo.monto_total else '' )
            mensaje = mensaje.replace('fecha_limite_de_pago', str(correo.recibo.vencimiento) if correo.recibo.vencimiento else '' )
            
            destinatarios = [email.strip() for email in correo.destinatarios.split(',') if email.strip()]
            recibo = correo.recibo

            # Filtrar archivos según los tipos seleccionados
            tipos = []
            if correo.facturaSeleccionada:
                tipos.append(1)
            if correo.comprobanteSeleccionado:
                tipos.append(2)
            if correo.complementoSeleccionado:
                tipos.append(3)

            archivos = RecibosFile.objects.filter(owner=recibo, tipo__in=tipos)
            attachments = []

            from django.core.mail import EmailMessage
            from django.core.mail import get_connection
            import mimetypes
            
            connection = get_connection(
                host='smtp.gmail.com',
                port=587,
                username='finanzas@miurabox.com',
                password='tmwj tagt iqnp vetj',
                use_tls=True
            )

            # extraer imagenes dentro del html content
            result = re.sub('\?[^"]+', '', mensaje)
            text = result
            img_pattern = r'<img.*?src="data:image/(.*?);base64,(.*?)".*?>'
            images = re.findall(img_pattern, text)
            # print('imagesimages',images)
            if images:
                for i, (img_type, img_data) in enumerate(images):
                    rnd =random.randint(1,10001)
                    img_name = 'image_'+str(i+1)+'_'+str(rnd)+'.'+str(img_type) 
                    s3_url = upload_to_s3_img(img_data, img_name, img_type,img_name,correo.recibo.organization.urlname)
                    search_str = 'data:image/' + img_type + ';base64,' + img_data
                    img_tag = s3_url + '" style="text-align:center;'
                    mensaje = mensaje.replace(search_str, img_tag)

            email = EmailMessage(
                subject=asunto,
                body=mensaje,
                from_email='Miurabox Finanzas <finanzas@miurabox.com>',
                to=destinatarios,
                connection=connection
            )
        

            for archivo in archivos:
                if archivo.arch:
                    archivo_nombre = archivo.arch.name.split('/')[-1]
                    mime_type, _ = mimetypes.guess_type(archivo_nombre)
                    mime_type = mime_type or 'application/octet-stream'
                    email.attach(archivo_nombre, archivo.arch.read(), mime_type)
            # Guardar los nombres de los archivos enviados como una cadena separada por comas
            correo.archivos_enviados = ", ".join([archivo.arch.name.split('/')[-1] for archivo in archivos])
            correo.message = mensaje
            email.content_subtype = "html"
            email.send()

            correo.enviado = True
            correo.save()
        except Exception as e:
            correo.error = str(e)
            correo.save()
            print("Error al enviar correo:", str(e))

# método para subir a amazon y hacerla pública la imagen del correo
def upload_to_s3_img(image_data, image_name, image_type,filename,org_name):
    import boto3    
    from boto3.s3.transfer import S3Transfer
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_STORAGE_BUCKET_NAME = "miurabox-public"
    AWS_ACCESS_KEY_ID = 'xxxxxxx'
    AWS_SECRET_ACCESS_KEY = 'xxx'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    MEDIA_URL = "https://%s/" % (AWS_S3_CUSTOM_DOMAIN)
    JWT_SECRET_KEY = 'CaS2.xxxxx'
    JWT_ALGORITHM = 'HS256'
    image_data_bytes = base64.b64decode(image_data)
    # Upload image to S3
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        BUCKET_FILE_NAME = "correocobranza/%s/%s"%(org_name,filename)
        s3.put_object(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=BUCKET_FILE_NAME,
            Body=image_data_bytes,
            ContentType='image/'+str(image_type),
            ACL='public-read' 
        )
        url = 'https://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/' + BUCKET_FILE_NAME

        return url
    except FileNotFoundError:
        return "The file was not found"
    except NoCredentialsError:
        return "Credentials not available"
