 # -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from core.views import LoginCas, LoginSaam, LoginMC

urlpatterns = [
    path('', include('accounts.urls')),
    path('', include('core.urls')),
    path('', include('organizations.urls')),
    path('', include('services.urls')),
    path('saam/', include('saam.urls')),
    path('', include('apps.urls')),
    path('mc/', include('multicotizador.urls')),
    path('pagos/', include('payment.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
    path('api-token-auth-cas/', LoginCas.as_view()),
    path('api-token-auth-saam/', LoginSaam.as_view()),
    path('us-login-multicotizador', LoginMC.as_view()),
]
