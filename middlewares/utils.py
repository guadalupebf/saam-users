from django.conf import settings
from rest_framework.authtoken.models import Token
from datetime import datetime, timedelta

def check_token(request):
    success = False 
    try:
        if  not 'Authorization' in request.headers:
            return True
        key = request.headers['Authorization'].replace("Token ", "")
        token = Token.objects.get(key=key)
        now =  datetime.now()
        if (token.created + timedelta(minutes=settings.TOKEN_DURATION)) < now:
            token.delete()
        else:
            success = True 
    except Exception as e:
        print('Exception to verify token =>', str(e))

    return success
