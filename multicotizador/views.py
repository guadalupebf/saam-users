from django.shortcuts import render
from django.http import Http404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import requests
from django.conf import settings

from accounts.tasks import get_jwt
from organizations.models import Organization

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from core.errors import get_error
from core.permissions import IsOrgMember
import json

# Create your views here.



class MulticotizadorListViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]


    @classmethod
    def get_extra_actions(cls):
        return []

    def get(self, request, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        r = requests.post(settings.MC_API_IP + 'get-schemas', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)

    def post(self, request, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, request.data)
        payload = request.data
        payload['Authorization'] =  'Bearer %s'%jwt
        r = requests.post(settings.MC_API_IP + 'create-tenant', payload)
        return Response(r.text, status = r.status_code)

    # def post(self, request, format=None):
    #     serializer = SnippetSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def put(self, request, pk, format=None):
    #     snippet = self.get_object(pk)
    #     serializer = SnippetSerializer(snippet, data=request.data, partial = True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request, pk, format=None):
    #     snippet = self.get_object(pk)
    #     snippet.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)

class UserMcListViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]


    def get(self, request, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        r = requests.get(settings.MC_API_IP+'usermc/'+'?org='+org_name, headers={'Authorization': 'Bearer %s'%jwt})
        data = {}
        if r.status_code==200:
            data = r.json()
        return Response(data, status = r.status_code)

    def post(self, request, format=None):

        mult = request.data
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
    

        data = {
            'username': mult.get('username'),
            'schema': mult.get('schema_desc'),
            'caratula': mult.get('caratula'),
            'org':org_name
        }

        headers = {'Authorization': 'Bearer %s'%jwt}
        result = requests.post(settings.MC_API_IP + 'usermc/', data = data ,headers = headers)
        print(result.json())
        data = {}
        if result.status_code==201:
            data = result.json()
        return Response(data, status = result.status_code)

    def delete(self, request, pk=None, format=None):
        print("Delete") 
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        headers = {'Authorization': 'Bearer %s'%jwt}
        result = requests.delete(settings.MC_API_IP + 'usermc/'+request.GET.get('pk')+'?org='+org_name, headers = headers)
        return Response(status = result.status_code)


class MulticotizadorDetailViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]


    def get(self, request, pk= None, format=None):
        org_name = None
        if not pk:
            return Response(get_error('bad_request'), status = 400)
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, {'name': pk})
        r = requests.post(settings.MC_API_IP + 'get-multicotizador', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)


    def put(self, request, pk= None, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        payload = request.data
        payload['multicotizador'] =  pk
        payload['Authorization'] =  'Bearer %s'%jwt
        r = requests.post(settings.MC_API_IP + 'save-general-info/', payload)
        return Response(r.text, status = r.status_code)



class MulticotizadorExistSchemaNameViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, schema_name = None, format=None):
        if not schema_name:
            return Response(get_error('bad_request'), status = 400)
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        r = requests.post(settings.MC_API_IP + 'exist-schema-name/'+ schema_name, {'Authorization': 'Bearer %s'%jwt, 'name': '0'})
        return Response(r.text, status = r.status_code)


class MulticotizadorListServicesViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        r = requests.post(settings.MC_API_IP + 'services/?ramo=4', {'Authorization': 'Bearer %s'%jwt, 'name': '0'})
        return Response(r.text, status = r.status_code)

    
class MulticotizadorCredentialsViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, pk= None, pk2= None, format=None):
        org_name = None
        if not pk or not pk2:
            return Response(get_error('bad_request'), status = 400)
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        r = requests.post(settings.MC_API_IP + 'get-credentials', {'Authorization': 'Bearer %s'%jwt, 'service': pk, 'multicotizador': pk2})
        return Response(r.text, status = r.status_code)



    def put(self, request, pk= None, pk2 = None, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        payload = request.data
        payload['service'] =  pk,
        payload['multicotizador'] =  pk2
        payload['Authorization'] =  'Bearer %s'%jwt
        r = requests.post(settings.MC_API_IP + 'save-credentials/', payload)
        print(r.text)
        return Response(r.text, status = r.status_code)




class MulticotizadorPackagesViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        r = requests.post(settings.MC_API_IP + 'packages/', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)


class MulticotizadorMarcasViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        r = requests.post(settings.MC_API_IP + 'cas/marcas', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)


class MulticotizadorCatalogoMarcaViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, catalogo=None,  format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, {'catalogo': catalogo})
        r = requests.post(settings.MC_API_IP + 'cas/marca-catalogo', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)



class MulticotizadorSubMarcasViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, marca = None ,format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, {'marca':marca})
        r = requests.post(settings.MC_API_IP + 'cas/submarcas', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)


class MulticotizadorCatalogoSubMarcaViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, catalogo=None, marca=None,  format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, {'catalogo': catalogo, 'marca':marca})
        r = requests.post(settings.MC_API_IP + 'cas/submarca-catalogo', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)




class MulticotizadorModelosViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, marca=None, submarca=None, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, {'marca':marca, 'submarca':submarca})
        r = requests.post(settings.MC_API_IP + 'cas/modelos', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)


class MulticotizadorCatalogoModeloViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, catalogo=None, marca=None, submarca=None,  format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, {'catalogo': catalogo, 'marca':marca, 'submarca':submarca})
        r = requests.post(settings.MC_API_IP + 'cas/modelo-catalogo', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)



class MulticotizadorVersionesViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, marca=None, submarca=None, modelo=None, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, {'marca':marca, 'submarca':submarca, 'modelo':modelo})
        r = requests.post(settings.MC_API_IP + 'cas/versiones', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)


class MulticotizadorGuardarCatalogoViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def post(self, request, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, request.data)
        r = requests.post(settings.MC_API_IP + 'cas/guardar-auto', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)

class MulticotizadorAutoGuardadoCatalogoViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def post(self, request, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, request.data)
        r = requests.post(settings.MC_API_IP + 'cas/auto-guardado', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)


class MulticotizadorCatalogoVersionViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def get(self, request, catalogo=None, marca=None, submarca=None, modelo=None,  format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, {'catalogo': catalogo, 'marca':marca, 'submarca':submarca, 'modelo':modelo})
        r = requests.post(settings.MC_API_IP + 'cas/version-catalogo', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)


class MulticotizadorSaveCatalogViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]

    def post(self, request, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name, request.data)
        r = requests.post(settings.MC_API_IP + 'save-catalog/', {'Authorization': 'Bearer %s'%jwt})
        return Response(r.text, status = r.status_code)



class MulticotizadorPackageCoveragesViewSet(APIView):
    permission_classes = [IsAuthenticated,  IsOrgMember]


    def get(self, request, pk= None, pk1 = None, pk2 = None, format=None):
        org_name = None
        if not pk:
            return Response(get_error('bad_request'), status = 400)
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        payload =  {
            'service': pk1,
            'multicotizador': pk2,
            'package': pk,
            'Authorization': 'Bearer %s'%jwt
        }
        r = requests.post(settings.MC_API_IP + 'get-coverages/', payload)
        return Response(r.text, status = r.status_code)


    def post(self, request, pk= None, pk1 = None, pk2 = None, format=None):
        org_name = None
        if request.GET.get('org',None):
            org_name = Organization.objects.get(pk = request.GET.get('org',None)).urlname
        jwt = get_jwt(request.user.id, org_name)
        print(request.data)
        payload =  {
            'service': pk1,
            'multicotizador': pk2,
            'package': json.dumps(request.data),
            'Authorization': 'Bearer %s'%jwt
        }
        r = requests.post(settings.MC_API_IP + 'save-package/', payload)
        print(r.text)
        return Response(r.text, status = r.status_code)
