# -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.conf.urls import url
from rest_framework.routers import DefaultRouter
from .views import (
		OrganizationViewSet,OrganizationApplicationViewSet, exist_organization, 
		create_org_demo, organization_info, get_org, 
		OrganizationLogoViewSet, OrganizationLogoMiniViewSet,  OrganizationMinViewSet, 
		is_org_demo, get_org_info, get_image_org, OrganizationFullViewSet, OrganizationLiteViewSet, get_email_admin,get_image_user, 
        OrganizationDataViewSet, OrganizationFileViewSet,OrganizationMainFileViewSet, report_orgs_data, get_org_info_all, RecibosViewSet, 
        RecibosByOrg, RecibosTodosDataViewSet, get_data_receit_stadistic, update_receipts_subsec, filterRecibosDash, 
        reportFilterRecibosDash, RecibosARenovarByOrg, get_organizations_name_gestor, RecibosMainFileViewSet, RecibosFileViewSet,
        get_organizactions_control,get_receipt_avencer,get_receipt_pagados,get_receipt_vencidos,
        cargar_excel_pagos,CarouselViewSet,get_carousel_items,
        PlantillaCorreoViewSet, CorreoReciboViewSet, OrganizationSaamLiteViewSet
	)

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, 'organization')
router.register(r'organization-application', OrganizationApplicationViewSet , 'organizationapplication')
router.register(r'organizations-full', OrganizationFullViewSet, 'organization-full') ## Se creó de esta manera debido a que ocupaba la misma llamada pero diferente serializador
router.register(r'organizations-min', OrganizationMinViewSet, 'organization-full') ## Se creó de esta manera debido a que ocupaba la misma llamada pero diferente serializador
router.register(r'organizations-lite', OrganizationLiteViewSet, 'organization-lite') ## devuelve solo id, name y urlname
router.register(r'organization-logo', OrganizationLogoViewSet, 'organization-logo')
router.register(r'organization-logo-mini', OrganizationLogoMiniViewSet, 'organization-logo-mini')
router.register(r'organization-data', OrganizationDataViewSet, 'organization-data-details')
router.register(r'recibos', RecibosViewSet, 'recibos')
# router.register(r'recibos-org',RecibosDataViewSet,'recibos-data')
router.register(r'recibos-todos', RecibosTodosDataViewSet, 'recibos-todos-details')
router.register(r'organization-file', OrganizationMainFileViewSet, 'organizationfile')
router.register(r'recibos-file', RecibosMainFileViewSet, 'recibosfile')
router.register(r'organization/(?P<id>\d+)/archivos', OrganizationFileViewSet, 'organization-archivos')
router.register(r'recibos/(?P<id>\d+)/archivos', RecibosFileViewSet, 'recibos-archivos')
router.register(r'carousel-general', CarouselViewSet, 'carouselgeneral')
router.register(r'plantillas-correo', PlantillaCorreoViewSet, 'plantillacorreo')
router.register(r'correos-recibo', CorreoReciboViewSet, 'correorecibo')
# CREAR ORGS SAAM LITE *
router.register(r'organizations-saam-lite', OrganizationSaamLiteViewSet, 'organization-saam-lite')

urlpatterns = [
    path(r'', include(router.urls)),
    path(r'get-org-info/<org>', get_org_info, name='get_org_info'),
    path(r'get-carousel-items/<org>', get_carousel_items, name='get_carousel_items'),
    path(r'get-image-or/<slug:org>', get_image_org, name='get_image_org'),    
    path(r'get-image-user/<usname>', get_image_user, name='get_image_user'),    
    path(r'get-emails/', get_email_admin, name='get_email_admin'),    
    url(r'^exist-organization/(?P<urlname>[-\w]+)$', exist_organization, name = 'exist_organization'),
    url(r'^individual-organization/(?P<urlname>[-\w]+)$', get_org, name = 'get_org'),
    url(r'^organization-info/(?P<id>[-\w]+)$', organization_info, name = 'exist_organization'),
    url(r'^is-org-demo/(?P<id>[-\w]+)$', is_org_demo, name = 'is_org_demo'),
    url(r'^create-org-demo', create_org_demo, name = 'create_org_demo'),
    url(r'^report-orgs-data/$', report_orgs_data, name = 'report_orgs_data'),
    path(r'organizations-all/', get_org_info_all, name='get_org_info_all'),
    path(r'recibos-stadistic/', get_data_receit_stadistic, name='get_data_receit_stadistic'),
    path(r'recibos-avencer/', get_receipt_avencer, name='get_receipt_avencer'),
    path(r'recibos-pagados/', get_receipt_pagados, name='get_receipt_pagados'),
    path(r'recibos-vencidos/', get_receipt_vencidos, name='get_receipt_vencidos'),
    path(r'recibos-upd-subsecuentes/', update_receipts_subsec, name='update_receipts_subsec'),
    path(r'filters-recibosDash/', filterRecibosDash, name='filterRecibosDash'),
    path(r'recibos_layout/', cargar_excel_pagos, name='cargar_excel_pagos'),
    path(r'report-receiptsdash/', reportFilterRecibosDash, name='reportFilterRecibosDash'),
    path(r'recibos-org/', RecibosByOrg, name='RecibosByOrg'),
    path(r'recibos-a-renovar/', RecibosARenovarByOrg, name='RecibosARenovarByOrg'),
    url(r'^control-organization-buscador/$', get_organizations_name_gestor, name = 'get_org'),
    url(r'^control-organizations/$', get_organizactions_control, name = 'get_orgs'),
]
