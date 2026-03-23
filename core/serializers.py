from rest_framework import serializers
from .models import Application, DemoRequest

from accounts.serializers import ModelPermissionSerializer

class ApplicationSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    application_models = ModelPermissionSerializer(read_only = True, many = True)
    class Meta:
        model = Application
        fields = '__all__'
        #exclude = ('model',)


class DemoRequestSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DemoRequest
        fields = ('email', 'name', 'status')