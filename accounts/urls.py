 # -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.conf.urls import url

from rest_framework.routers import DefaultRouter
from .views import ( ModelPermissionViewSet, UserInfoViewSet,  
					PermissionViewSet, UserViewSet, exist_email, has_users,
					exist_username, UserPermissionViewSet, 
					ProfileViewSet, get_permissions, exist_profile_name, 
					UserInfoAvatarViewSet, aseguradoras,aseguradorasperfil,
					ramos, report_users, reporte_perfiles, reporte_perfiles_restringidos, subramos, claves_general, clave_saam, VendorView,
                    UsuarioView, get_user_picture, search_user, users_org, comisiones_general,report_users_app,
                    crear_comision, UserInactiveViewSet, users_app_created,desactivar_usuario_app, exist_email_saam_lite, UserSaamLiteViewSet, ProfileSaamLiteViewSet,
                    exist_username_lite, exist_first_and_lastname,usersoperativos
					)


router = DefaultRouter()
# router.register(r'formatos', FormatosViewSet, 'formatos')
router.register(r'model-permission', ModelPermissionViewSet, 'modelpermission')
router.register(r'permissions', PermissionViewSet, 'permission')
router.register(r'user-permissions', UserPermissionViewSet, 'userpermission')
router.register(r'user-info', UserInfoViewSet, 'userinfo')
router.register(r'user-avatar-info', UserInfoAvatarViewSet, 'userinfo')
router.register(r'profiles', ProfileViewSet, 'profile')
router.register(r'users', UserViewSet, 'user')
router.register(r'users-inactive', UserInactiveViewSet, 'user-inactive')
router.register(r'vendor', VendorView, 'vendor')
router.register(r'usuarios', UsuarioView, 'usuarios')
router.register(r'users-by-org', users_org, 'users_org')
router.register(r'users-app-created', users_app_created, 'users_app_created')
# creación de la cuenta para usar SAAMLITE
router.register(r'profiles-saam-lite', ProfileSaamLiteViewSet, 'profile-saam-lite')
router.register(r'users-saam-lite', UserSaamLiteViewSet, 'user-saam-lite')


#router.register(r'profile-application', ProfileApplicationViewSet, 'profileapplication')
    
urlpatterns = [
    path(r'', include(router.urls)),
    path(r'get-permissions/', get_permissions, name='get_permissions'),
    path(r'get-user-picture/<slug:username>', get_user_picture, name='get_user_picture'),
    url(r'^claves-general-saam/$', claves_general, name = 'claves'),
    url(r'^comisiones-saam/(?P<clave_id>[-\w]+)$', comisiones_general, name = 'claves'),
    url(r'^comision-saam$', crear_comision, name = 'comision'),
    url(r'^has-users', has_users, name = 'has_users'),
    url(
        r'^exist-nameuser/(?P<first_name>[-\w]+)/'
        r'(?P<last_name>[-\w]+)'
        r'(?:/(?P<user_id>(?:\d+|null)))?/$',
        exist_first_and_lastname,
        name='exist_first_and_lastname'
    ),
    url(r'^exist-email$', exist_email, name = 'exist_email'),
    url(r'^exist-username/(?P<username>[-\w]+)$', exist_username, name = 'exist_username'),
    url(r'^exist-profile-name$', exist_profile_name, name = 'exist_profile_name'),
    url(r'^aseguradoras-saam$', aseguradoras, name = 'aseguradoras'),
    url(r'^aseguradoras-saam-perfil$', aseguradorasperfil, name = 'aseguradorasperfil'),
    url(r'^ramos-saam/(?P<aseguradora_id>[-\w]+)$', ramos, name = 'ramos'),
    url(r'^subramos-saam/(?P<aseguradora_id>[-\w]+)/(?P<ramo_id>[-\w]+)$', subramos, name = 'subramos'),
    url(r'^report-users-by-org/$', report_users, name = 'report_users'),
    url(r'^reporte-perfiles/$', reporte_perfiles, name = 'report_users'),
    url(r'^reporte-perfiles-restringidos/$', reporte_perfiles_restringidos, name = 'report_users'),
    url(r'^clave-saam$', clave_saam, name = 'clave_saam'),
    url(r'^search-user$', search_user, name = 'search_user'),
    url(r'^report-users-app/$', report_users_app, name = 'report_users_app'),
    url(r'^desactivar-usuario-app/$', desactivar_usuario_app, name = 'desactivar_usuario_app'),
    # url(r'^users-by-org/$', users_org, name = 'users_org'),
    url(r'^exist-email-lite/$', exist_email_saam_lite, name = 'exist_email_saam_lite'),
    url(r'^exist-username-lite/(?P<username>[-\w]+)$', exist_username_lite, name = 'exist_username_lite'),   
    # url(r'get-usersemails/<org>', usersoperativos, name='usersoperativoscas'),
    path('get-usersemails/<str:org>/', usersoperativos, name='usersoperativoscas'),
    # url(r'^get-usersemails/(?P<org>[\w-]+)/$', usersoperativos, name='usersoperativoscas'),

]