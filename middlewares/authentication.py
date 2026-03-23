from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, JsonResponse
from core.errors import get_error
from .utils import check_token



class verifyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        success = check_token(request)
        if not success:
            return JsonResponse({'error': get_error('invalid_token')}, status=status.HTTP_401_UNAUTHORIZED)
