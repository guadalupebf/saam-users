 # -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.conf.urls import url
from django.urls import path

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'mcs$', MulticotizadorListViewSet, basename = 'mc-list')

urlpatterns = [
    path(r'', include(router.urls)),
    path('mcs', views.MulticotizadorListViewSet.as_view(), name='mc-list'),
    path('usermc', views.UserMcListViewSet.as_view(), name='mcuser-list'),
    path('services', views.MulticotizadorListServicesViewSet.as_view(), name='mc-service-list'),
    path('exist-schema-name/<str:schema_name>', views.MulticotizadorExistSchemaNameViewSet.as_view(), name='exist-schema-name'),
    path('mcs/<str:pk>', views.MulticotizadorDetailViewSet.as_view(), name='mc-detail'),
    path('credentials/<int:pk>/<str:pk2>', views.MulticotizadorCredentialsViewSet.as_view(), name='mc-credentials'),
    path('coverages/<int:pk>/<int:pk1>/<str:pk2>', views.MulticotizadorPackageCoveragesViewSet.as_view(), name='mc-package-coverages'),
    path('packages', views.MulticotizadorPackagesViewSet.as_view(), name='mc-packages'),
    path('guardar-catalogo-homologacion', views.MulticotizadorSaveCatalogViewSet.as_view(), name='guardar-catalogo-homologacion'),
    path('marcas', views.MulticotizadorMarcasViewSet.as_view(), name='marcas'),
    path('submarcas/<str:marca>', views.MulticotizadorSubMarcasViewSet.as_view(), name='submarcas'),
    path('modelos/<str:marca>/<str:submarca>', views.MulticotizadorModelosViewSet.as_view(), name='modelos'),
    path('versiones/<str:marca>/<str:submarca>/<str:modelo>', views.MulticotizadorVersionesViewSet.as_view(), name='versiones'),
    
    path('marca-catalogo/<str:catalogo>', views.MulticotizadorCatalogoMarcaViewSet.as_view(), name='marca-catalogo'),
    path('submarca-catalogo/<str:catalogo>/<str:marca>', views.MulticotizadorCatalogoSubMarcaViewSet.as_view(), name='submarca-catalogo'),
    path('modelo-catalogo/<str:catalogo>/<str:marca>/<str:submarca>', views.MulticotizadorCatalogoModeloViewSet.as_view(), name='modelo-catalogo'),
    path('version-catalogo/<str:catalogo>/<str:marca>/<str:submarca>/<str:modelo>', views.MulticotizadorCatalogoVersionViewSet.as_view(), name='version-catalogo'),
    
    path('guardar-auto', views.MulticotizadorGuardarCatalogoViewSet.as_view(), name='guardar-auto'),
    path('auto-guardado', views.MulticotizadorAutoGuardadoCatalogoViewSet.as_view(), name='auto-guardado'),
]