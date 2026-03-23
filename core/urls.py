 # -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import path
from django.conf.urls import include

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'formatos', FormatosViewSet, 'formatos')
router.register(r'application', views.ApplicationViewSet, 'application')
router.register(r'demo-request', views.DemoRequestViewSet, 'demorequest')

urlpatterns = [
    path(r'', include(router.urls)),
    path(r'validate-token', views.valid_token, name='valid_token'),
    path(r'test-request', views.test_request, name='test_request'),
    path(r'email-request-exists', views.email_request_exist, name='email_request_exist'),
    path(r'user-info-saam', views.get_user_info, name='get_user_info'),
    path(r'user-info-ms-saam', views.get_user_info_ms, name='get_user_info_ms'),
    path(r'api-logout-saamlite/', views.delete_session_saamlite, name='delete_session_saamlite'),
]