import json
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Organization
from .serializers import OrganizationHyperSerializer



class LoginCasUserTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create(username='user', email= 'test@test.com')
        self.user.set_password('123')
        self.user.save()


    def test_login_usuario(self):
        data= {
            'username': 'user',
            'password': '123'
        }

        response = self.client.post("/api-token-auth-cas/",data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_login_correo(self):        
        data= {
            'username': 'test@test.com',
            'password': '123'
        }

        response = self.client.post("/api-token-auth-cas/",data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_login_correo_bad_password(self):        
        data= {
            'username': 'test@test.com',
            'password': 'asd908'
        }

        response = self.client.post("/api-token-auth-cas/",data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



class OrganizationTestCase(APITestCase):

    list_url = '/organizations/'

    def test_organization_list_authenticated(self):
        response = self.client.get(self.list_url)
        # print('**********>   ', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_organization_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)   


    def test_organization_detail_retrieve_authenticated(self):
        response = self.client.get(self.list_url + str(self.org.id) + '/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.org.id)

    def test_organization_detail_retrieve_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url + '1/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)   


    def test_organization_create_authenticated(self):
        data= {
            'name': 'testcase',
            'urlname': 'testcase',
            'alias': 'testcase',
            'phone': '4444444444',
            'email': 'sometest@test.com',
            'address': 'Av de las Fuentes sin numero 345'
        }

        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['urlname'], data['urlname'])


    def test_organization_create_existent_authenticated(self):
        data= {
            'name': 'testcase',
            'urlname': 'test',
            'alias': 'testcase',
            'phone': '4444444444',
            'email': 'sometest@test.com',
            'address': 'Av de las Fuentes sin numero 345'
        }

        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    def test_organization_create_unauthenticated(self):
        self.client.force_authenticate(user=None)
        data= {
            'name': 'testcase',
            'urlname': 'testcase',
            'alias': 'testcase',
            'phone': '4444444444',
            'email': 'sometest@test.com',
            'address': 'Av de las Fuentes sin numero 345'
        }

        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_organization_update_authenticated(self):
        data= {
            'name': 'testcase',
            'alias': 'testcase',
            'phone': '1111111111',
            'email': 'sometest@test.com',
            'address': 'Av de las Fuentes sin numero 345'
        }

        response = self.client.patch(self.list_url + str(self.org.id) + '/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], data['email'])




    def test_organization_update_unauthenticated(self):
        self.client.force_authenticate(user=None)
        data= {
            'name': 'testcase',
            'alias': 'testcase',
            'phone': '1111111111',
            'email': 'sometest@test.com',
            'address': 'Av de las Fuentes sin numero 345'
        }

        response = self.client.patch(self.list_url + str(self.org.id) + '/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        


    def test_organization_update_same_urlname_authenticated(self):
        orgtest = Organization.objects.create(urlname  = 'orgtest', name='OrgTest')
        data= {
            'urlname': 'test'
        }

        response = self.client.patch(self.list_url + str(orgtest.id) + '/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)




    def setUp(self):
        self.user = User.objects.create(username='user', email= 'test@test.com')
        self.user.set_password('123')
        self.user.save()

        self.org = Organization.objects.create(urlname  = 'test', name='Test')

        self.token = Token.objects.create(user = self.user).key
        self.api_authentication()

    def api_authentication(self):
        self.client.credentials(HTTP_AUTHORIZATION = "Token "+ self.token)
