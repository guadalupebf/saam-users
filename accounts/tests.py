from django.contrib.auth.models import User
from django.urls import reverse
from django.core.management import call_command 

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status

from organizations.models import Organization
from core.models import Application

from .models import UserInfo, Profile

import json




class UserTestCase(APITestCase):
    
    def setUp(self):

        self.data = {
            "username": "user-test2",
            "first_name": "test",
            "last_name": "last",
            "email": "test@required2.com",
            "is_staff": True,
            "is_superuser": True,
            "password": "TestPassword",
            "phone": "5555555555",
            "birthdate": "1992-06-24",
            "gender": 1,
            "rfc": "PECJ920624"
        }
        self.user = User.objects.create(username='user', email= 'test@test.com', is_staff=True, is_superuser=True)
        self.user.set_password('123')
        self.user.save()

        self.org = Organization.objects.create(urlname  = 'test', name='Test')

        self.token = Token.objects.create(user = self.user).key
        self.api_authentication()

    def api_authentication(self):
        self.client.credentials(HTTP_AUTHORIZATION = "Token "+ self.token)

    # create user
    def test_create_user(self):
        response = self.client.post(reverse("user-list"),self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    # create tuw users with same email
    def test_duplicate_email(self):
        self.data['email'] = 'test@test.com'
        response = self.client.post(reverse("user-list"),self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # create user without email
    def test_null_email(self):
        self.data['email'] = ''
        response = self.client.post(reverse("user-list"),self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    #Create user info 
    def test_create_user_info(self):
        users = self.client.get(reverse("user-list"))
        orgs = self.client.get(reverse("organization-list"))
        data_user_info =         {
            "role": 1,
            "activation_number": 1,
            "phone": "5555555555",
            "birthdate": "1992-06-24",
            "gender": 1,
            "rfc": "PECJ920624",
            "user": users.json()['results'][0]['url'],
            "org": orgs.json()['results'][0]['url']
        }
        self.data['email'] = 'test@test.com'

        response = self.client.post(reverse("userinfo-list"), data_user_info)
        self.assertEqual(users.status_code, status.HTTP_200_OK)
        self.assertEqual(orgs.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # Create user infor whitout  org
    def test_create_user_info_org_null(self):
        users = self.client.get(reverse("user-list"))
        
        data_user_info =         {
            "role": 1,
            "activation_number": 1,
            "phone": "5555555555",
            "birthdate": "1992-06-24",
            "gender": 1,
            "rfc": "PECJ920624",
            "user": users.json()['results'][0]['url'],

        }
        self.data['email'] = 'test@test.com'

        response = self.client.post(reverse("userinfo-list"), data_user_info)
        self.assertEqual(users.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Create user infor whitout  user
    def test_create_user_info_user_null(self):
        orgs = self.client.get(reverse("organization-list"))
        data_user_info =         {
            "role": 1,
            "activation_number": 1,
            "phone": "5555555555",
            "birthdate": "1992-06-24",
            "gender": 1,
            "rfc": "PECJ920624",
            "org": orgs.json()['results'][0]['url']
        }
        self.data['email'] = 'test@test.com'

        response = self.client.post(reverse("userinfo-list"), data_user_info)
        self.assertEqual(orgs.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Crear dos registros en user info que apunten al mismo usuario
    def test_create_users_info_same_user(self):
        users = self.client.get(reverse("user-list"))
        orgs = self.client.get(reverse("organization-list"))
        data_user_info =         {
            "role": 1,
            "activation_number": 1,
            "phone": "5555555555",
            "birthdate": "1992-06-24",
            "gender": 1,
            "rfc": "PECJ920624",
            "user": users.json()['results'][0]['url'],
            "org": orgs.json()['results'][0]['url']
        }
        self.data['email'] = 'test@test.com'

        response = self.client.post(reverse("userinfo-list"), data_user_info)
        response_duplicate_user = self.client.post(reverse("userinfo-list"), data_user_info)
        # Primer registro debe ser correcto
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Segundo registro debe ser erroneo, la recion user a user infor es OnetoOne
        self.assertEqual(response_duplicate_user.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileTestCase(APITestCase):
    
    def setUp(self):

        self.data = {
            "username": "user-test2",
            "first_name": "test",
            "last_name": "last",
            "email": "test@required2.com",
            "is_staff": True,
            "is_superuser": False,
            "password": "TestPassword"
        }
        self.user = User.objects.create(username='user', email= 'test@test.com', is_staff=True, is_superuser=True)
        self.user.set_password('123')
        self.user.save()

        self.org = Organization.objects.create(urlname  = 'test', name='Test')
        self.application = Application.objects.create(name= 'SAAM')
        data_user_info =         {
            "role": 1,
            "activation_number": 1,
            "phone": "5555555555",
            "birthdate": "1992-06-24",
            "gender": 1,
            "rfc": "PECJ920624",
            "user": self.user,
            "org": self.org
        }
    

        self.user_info = UserInfo.objects.create(**data_user_info)

        self.token = Token.objects.create(user = self.user).key
        self.api_authentication()

    def api_authentication(self):
        self.client.credentials(HTTP_AUTHORIZATION = "Token "+ self.token)

    #Crear un perfil relacionado a user info y obtener info necesaria para la creacion del perfil
    def test_cretate_profile(self):
        orgs = self.client.get(reverse("organization-list"))
        apps = self.client.get(reverse("application-list"))
        profile_dict = {
            "descr": "TEST Profile",
            "is_active": True,
            "org": orgs.json()['results'][0]['url'],
            #"application":  apps.json()['results'][0]['url'],
            "application":  apps.json()[0]['url'],
            "user_info": []
        }


        response = self.client.post(reverse("profile-list"), profile_dict)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    #Creacion de perfil sin campos requeridos 
    def test_create_profile_worf(self):
        profile_dict = {
            "descr": "TEST Profile",
            "is_active": True,
            "user_info": []
        }


        response = self.client.post(reverse("profile-list"), profile_dict)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Creacion completa de usuario(User, Userinfo con la asiganacion del perfil)
    def test_create_profile_userinfo(self):
        orgs = self.client.get(reverse("organization-list"))
        # Create User
        data = {
            "username": "user-test2",
            "first_name": "test",
            "last_name": "last",
            "email": "test@required2.com",
            "is_staff": True,
            "is_superuser": False,
            "password": "TestPassword",
            "phone": "5555555555",
            "birthdate": "1992-06-24",
            "gender": 1,
            "rfc": "PECJ920624",
        }
        
        user = self.client.post(reverse("user-list")+'?org={}'.format( orgs.json()['results'][0]['id']),data)
        #  Create user info with related profile
        self.assertEqual(user.status_code, status.HTTP_201_CREATED)

    # Intento de creacion de usuario sin org
    def test_create_userinfo_error_org(self):
        

        # Create User
        data = {
            "username": "user-test2",
            "first_name": "test",
            "last_name": "last",
            "email": "test@required2.com",
            "is_staff": True,
            "is_superuser": False,
            "password": "TestPassword",
            "phone": "5555555555",
            "birthdate": "1992-06-24",
            "gender": 1,
            "rfc": "PECJ920624",
        }
        
        user = self.client.post(reverse("user-list"),data)
        #  Create user info with related profile
   
        self.assertEqual(user.status_code, status.HTTP_400_BAD_REQUEST)


class PermissionTestCase(APITestCase):
    
    def setUp(self):
        call_command('loaddata', 'data/0001_applications.json', verbosity=1)
        call_command('loaddata', 'data/0002_permissions.json', verbosity=1)
        self.org = Organization.objects.create(urlname  = 'test', name='Test')
        app_saam = Application.objects.get(id=1) 
        app_multicotizador = Application.objects.get(id=2) 
        self.profile_saam = Profile.objects.create(descr='Admin_SAAM', is_active=True, org=self.org, application=app_saam) 
        self.profile_multicotizador = Profile.objects.create(descr='Admin_Multicotizador', is_active=True, org=self.org, application=app_multicotizador) 
        
        self.user = User.objects.create(username='user', email= 'test@test.com', is_staff=True, is_superuser=True)
        self.user.set_password('123')
        self.user.save()
        self.token = Token.objects.create(user = self.user).key
        self.api_authentication()

    def api_authentication(self):
        self.client.credentials(HTTP_AUTHORIZATION = "Token "+ self.token)
    
    # Obtener todos los permisos por applicacion
    def test_get_permissions(self):
        permissions_saam = self.client.get(reverse("permission-list")+'?application=SAAM')
        permissions_multicotizador = self.client.get(reverse("permission-list")+'?application=Multicotizador')
        self.assertEqual(permissions_saam.status_code, status.HTTP_200_OK)
        self.assertEqual(permissions_multicotizador.status_code, status.HTTP_200_OK)

    # Assiggnacion de  permisos a  profile
    def test_assig_permission_profile(self):
        permissions_saam = self.client.get(reverse("permission-list")+'?application=SAAM')
        profiles = self.client.get(reverse("profile-list"))
        profile =  None
        for p in profiles.json()['results']:
            if p['descr'] == 'Admin_SAAM':
                profile = p
        next_page =  True
        while(next_page):
            for permission  in permissions_saam.json()['results']:
                permission_dict  = {
                    'checked': True,
                    'is_active': True,
                    'profile': profile['url'],
                    'permission': permission['url']
                }
                result =  self.client.post(reverse('userpermission-list'), permission_dict)
                self.assertEqual(result.status_code, status.HTTP_201_CREATED)
            if permissions_saam.json()['next']:
                permissions_saam = self.client.get(permissions_saam.json()['next'])
            else:
                next_page = False
        permissions_profile =  self.client.get(reverse('userpermission-list')+'?profile=Admin_SAAM')
        self.assertEqual(permissions_profile.status_code, status.HTTP_200_OK)
        self.assertEqual(permissions_profile.json()['count'],permissions_saam.json()['count'])


    # Assiggnacion de  permisos a  profile erroneo
    def test_assig_permission_error_profile(self):
        permissions_saam = self.client.get(reverse("permission-list")+'?application=SAAM')
        profiles = self.client.get(reverse("profile-list"))
        profile =  None
        for p in profiles.json()['results']:
            if p['descr'] == 'Admin_Multicotizador':
                profile = p
        for permission  in permissions_saam.json()['results']:
            permission_dict  = {
                'checked': True,
                'is_active': True,
                'profile': profile['url'],
                'permission': permission['url']
            }
            result =  self.client.post(reverse('userpermission-list'), permission_dict)
            self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)


            
