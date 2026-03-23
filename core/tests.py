from django.test import TestCase
from rest_framework.test import APITestCase
from .models import *
from django.urls import reverse
from rest_framework import status
import json


# Create your tests here.


class DemoPruebaTestCase(APITestCase):
    
    def setUp(self):
        self.data = {
            "email": "asd@asd.com",
            "name": "demotest"
        }

        DemoRequest.objects.create(
            name = "demotest",
            email = "asd@asd.com"
        )

    # create user
    def test_create_demo_request_with_data_already_exist(self):
        response = self.client.post(reverse("test_request"),self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_create_demo_request(self):
        self.data["email"] = "asdf@ads.com"
        response = self.client.post(reverse("test_request"),self.data)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)


    def test_verify_email_request_with_data_already_exist(self):
        response = self.client.post(reverse("email_request_exist"), data = self.data )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, True)


    def test_verify_email_request_with_data_new(self):
        self.data["email"] = "asdf@ads.com"
        response = self.client.post(reverse("email_request_exist"), data = self.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, False)
    
    