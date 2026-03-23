 # -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import path
from django.conf.urls import include

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'application', views.ApplicationViewSet, 'application')
urlpatterns = [
    path(r'', include(router.urls)),
    path(r'activate-user/<str:bs64>/', views.activate_app_user, name='activate_app_user'),
    path(r'activate-user/kalifa/<str:bs64>/', views.activate_app_user_kalifa, name='activate_app_user'),
    path(r'restart-password-user/', views.restart_password_app_user, name='restart_password_app_user'),
    path(r'send-new-password/', views.send_new_password, name='send_new_password'),
    path(r'forgot-password', views.send_new_password, name='send_new_password'),
    path(r'resend-activation-email', views.resend_activation_email, name='resend_activation_email'),
    path(r'cas-create-user', views.create_user, name='create_user'),
    path(r'app-us-login', views.app_us_login, name='app_us_login'),
    path(r'desactivar_user_app', views.desactivate_user_app, name='desactivate_user_app'),
    path(r'us-login-bibis', views.login_bibis, name='login_bibis'),
    path(r'app-us-login_portal', views.app_us_login_portal, name='app_us_login_portal'),
    path(r'cas-create-users-app/', views.create_users_app, name='create_users_app'),
    path(r'create_user_app_cas/', views.create_user_app, name='create_user_app')
]