from saam.tasks import guardar_perfil_usuario_restringido_saam, guardar_perfil_usuario_restringidoname_saam
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import serializers

from .models import ModelPermission, Permission, UserPermission, UserInfo, Profile
from .utils import  save_userinfo_saam
from core.errors import get_error
from organizations.models import Organization
from core.utils import Base64ImageField
from organizations.models import Application
from presigned_url import get_url_file
import requests
from django.conf import settings

import datetime

class PermissionSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Permission
        fields = '__all__'
        #exclude = ('model',)

class UserPermissionSerializer(serializers.HyperlinkedModelSerializer):
    permission_name = serializers.SerializerMethodField()
    id = serializers.IntegerField(read_only=True)

    def get_permission_name(self,obj):
        return obj.permission.name

    def create(self, validated_data):
        profile = validated_data['profile']
        permission = validated_data['permission']
        if profile.application == permission.model.application:
            return UserPermission.objects.create(**validated_data)
        else:
            raise serializers.ValidationError(get_error('invalid_permission'))

    class Meta:
        model = UserPermission
        fields = '__all__'

class PermissionTMSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Permission
        exclude = ('model',)


class ModelPermissionSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    permissions= PermissionTMSerializer(source='permission_model', required=False, many=True)
    class Meta:
        model = ModelPermission
        fields = '__all__'
        #exclude = ('url',)



class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    org = serializers.StringRelatedField(read_only=True)
    profile_permissions = UserPermissionSerializer(read_only = True, many = True)

    def create(self, validated_data):
        permissions = self.context.get('request').data.get('permissions')

        profile = Profile.objects.create(**validated_data)

        for model in permissions:
            for permission in model:
                    permission_instance = Permission.objects.get(pk = permission['id'])
                    UserPermission.objects.create(
                        profile = profile, 
                        permission = permission_instance, 
                        checked = permission['checked'])
        return profile


    class Meta:
        model = Profile
        fields = ('id', 'url', 'name', 'is_active', 'org', 
            'application', 'profile_permissions','type_profile')
        #exclude = ('url',)

class ProfileResumeSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Profile
        fields = '__all__'
 
class UserInfoSerializer2(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_profiles = ProfileResumeSerializer(read_only = True, many = True)
    drole = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    orgname = serializers.SerializerMethodField()
    
    def get_drole(self,obj):
        return obj.get_role_display()

    def get_profile(self, ui):
        name = ''
        app=  Application.objects.get(name='SAAM')
        profile=  Profile.objects.filter(user_info=ui, application=app)
        if profile.exists():
            name = profile[0].name
        return name 

    def get_orgname(self, ui):
        name = ''
        try:
            orgname=  Organization.objects.get(urlname = ui.org)
        except:
            orgname = ''
        if orgname:
            name = orgname.urlname
        return name 
    
    avatar = serializers.SerializerMethodField()
    def get_avatar(self,obj):
        folder = settings.MEDIAFILES_LOCATION
        if obj.avatar:
            return get_url_file(obj.avatar)   
        else:
            return ''
    
    class Meta:
        model = UserInfo
        fields = '__all__'
        #exclude = ('user',)
class UserInfoSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_profiles = ProfileResumeSerializer(read_only = True, many = True)
    drole = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    orgname = serializers.SerializerMethodField()
    
    def get_drole(self,obj):
        return obj.get_role_display()

    def get_profile(self, ui):
        name = ''
        app=  Application.objects.get(name='SAAM')
        profile=  Profile.objects.filter(user_info=ui, application=app)
        if profile.exists():
            name = profile[0].name
        return name 

    def get_orgname(self, ui):
        name = ''
        try:
            orgname=  Organization.objects.get(urlname = ui.org)
        except:
            orgname = ''
        if orgname:
            name = orgname.urlname
        return name 
    
        
    class Meta:
        model = UserInfo
        fields = '__all__'
        #exclude = ('user',)
    def to_representation(self, instance):
        serializer = UserInfoSerializer2(instance = instance, context={'request':self.context.get("request")}, many =False)
        return serializer.data
    
class UserInfoAvatarSerializer2(serializers.HyperlinkedModelSerializer):
    avatar = serializers.SerializerMethodField()
    def get_avatar(self,obj):
        folder = settings.MEDIAFILES_LOCATION
        if obj.avatar:
            return get_url_file(obj.avatar)   
        else:
            return ''
    
    class Meta:
        model = UserInfo
        fields = ( 'avatar',  )
        #exclude = ('user',)
class UserInfoAvatarSerializer(serializers.HyperlinkedModelSerializer):
    avatar = Base64ImageField(
     max_length=None, use_url=True, 
    )
    class Meta:
        model = UserInfo
        fields = ( 'avatar',  )
        #exclude = ('user',)
    def to_representation(self, instance):
        serializer = UserInfoAvatarSerializer2(instance = instance, context={'request':self.context.get("request")}, many =False)
        return serializer.data


def send_email_user_created(user, ui, mp):
    mps = {
        0: 'Sin acceso',
        1: 'Operativo',
        2: 'Consulta',
        3: 'Superusuario'
    }
    requests.post(settings.MAIL_SERVICE+'mails/new-user-admin/', {
        # "email" : 'alan.eesquivel@grupogpi.mx',
        "email" : user.email,
        "acceso" : mps[int(mp)],
        "org" : ui.org.urlname,
        "name": "%s %s"%(user.first_name, user.last_name),
        "phone": ui.phone,
        "html": 'new_user_email.html',
        "username" : user.username,
        "subject": "Nueva alta de usuario"
    })
def send_email_user_created_lite(user, ui, mp):
    mps = {
        0: 'Sin acceso',
        1: 'Operativo',
        2: 'Consulta',
        3: 'Superusuario'
    }
    url_personalizada=ui.org.urlname+'.mbxservicios.com'
    requests.post(settings.MAIL_SERVICE+'mails/new-user-lite/', {
        "email" : user.email,
        "acceso" : mps[int(mp)],
        "org" : ui.org.urlname,
        "name": "%s %s"%(user.first_name, user.last_name),
        "phone": ui.phone,
        "url_personalizada":url_personalizada,
        "html": 'new_user_lite_email.html',
        "username" : user.username,
        "subject": "Nueva alta de usuario"
    })

class UserSerializer(serializers.HyperlinkedModelSerializer):
    role = serializers.SerializerMethodField()
    email = serializers.CharField(required=True)
    userinfo = UserInfoSerializer(many=False, read_only = True)
    password = serializers.CharField(write_only=True, required=False, allow_null=True)
    password_confirm = serializers.CharField(write_only=True, required=False, allow_null=True)
    perfilRestringido = serializers.SerializerMethodField()
    nameperfilrestringido = serializers.SerializerMethodField()
    def get_perfilRestringido(self, obj):
        if obj.is_staff:
            try:
                r = guardar_perfil_usuario_restringido_saam(
                    self.context.get('request').user.id,
                    UserInfo.objects.get(user = obj).org.urlname,
                    obj.username
                )
                return r
            except Exception as e:
                print(e)
                return 0
        else:
            return 0

    def get_nameperfilrestringido(self, obj):
        if obj.is_staff:
            try:
                print('--obj',obj)               
                r = guardar_perfil_usuario_restringidoname_saam(obj.id, obj.userinfo.org)
                return r
            except Exception as e:
                print(e)
                return 0
        else:
            return 0
    def get_role(self, user):
        try:
            role = user.userinfo.role
        except:
            role = 1
        return  role

    def update(self, instance, validated_data):
        if 'password' in validated_data and validated_data['password']:
            if validated_data['password'] == validated_data['password_confirm']:
                instance.set_password(validated_data['password']) 
            else:
                raise serializers.ValidationError(get_error('not_match_password'))
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.is_staff = validated_data.get('is_staff', instance.is_staff)
        instance.is_superuser = validated_data.get('is_superuser', instance.is_superuser)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        if instance.userinfo.org:
            saved_user_saam = save_userinfo_saam(
                org= instance.userinfo.org.urlname, 
                username= instance.username, 
                firstname= instance.first_name, 
                lastname= instance.last_name, 
                email= instance.email,
                perfilRestringido = self.context.get('request').data.get('perfilRestringido')
            )

            if 'userinfo' in self.context['request'].data:
                if UserInfo.objects.filter(user=instance).exists():
                    data = self.context['request'].data
                    user_info = data['userinfo']
                    userinfo = instance.userinfo
                    userinfo.rfc = user_info.get('rfc', userinfo.rfc)
                    if userinfo.org.urlname != 'pruebas' and userinfo.manage_profile == 0 and user_info.get('notificarContabilidad', False) and int(user_info.get('manage_profile',0)) not in  [0,3]:
                        send_email_user_created(instance, userinfo, user_info.get('manage_profile',0))
                    userinfo.manage_profile = user_info.get('manage_profile', userinfo.manage_profile)
                    userinfo.birthdate = user_info.get('birthdate', userinfo.birthdate)
                    userinfo.phone = user_info.get('phone', userinfo.phone)
                    userinfo.gender = user_info.get('gender', userinfo.gender)
                    if 'rol' in data:
                        userinfo.role =  data['rol']
                    userinfo.save()
            return instance
        else: #user app    
            if 'userinfo' in self.context['request'].data:
                if UserInfo.objects.filter(user=instance).exists():
                    data = self.context['request'].data
                    user_info = data['userinfo']
                    userinfo = instance.userinfo
                    userinfo.rfc = user_info.get('rfc', userinfo.rfc)
                    userinfo.identifier = user_info.get('identifier', userinfo.identifier)
                    if 'rol' in data:
                        userinfo.role =  data['rol']
                    userinfo.save()
            return instance

    def create(self, validated_data):
        password_confirmation = validated_data.pop('password_confirm')
        if not validated_data['password'] == password_confirmation:
            raise serializers.ValidationError(get_error('not_match_password'))
        validated_data['username'] = validated_data['username'].lower() 
        validated_data['email'] = validated_data['email'].lower()  
        request = self.context.get('request')
        org_associated = request.data.get('org') if request else None
        if 'is_superuser' in validated_data and  not validated_data['is_superuser']:
            userinfo = self.context.get('request').data.get('userinfo')
            birthdate = userinfo.get('birthdate')
            gender = userinfo.get('gender')
            phone = userinfo.get('phone')
            rfc = userinfo.get('rfc')
            role = userinfo.get('role')
            org = self.context.get('request').GET.get('org',0)
            another_tasks = userinfo.get('another_tasks', False)
            manage_profile = userinfo.get('manage_profile', 0)
            notificarContabilidad = userinfo.get('notificarContabilidad', 0)
            try:
                notificarEmail=userinfo.get('notificarEmail',False)
            except:
                notificarEmail=False
            # is user saamlite only
            is_user_lite = userinfo.get('is_user_lite', False)


            if not birthdate and not gender and not phone and not rfc:
                raise serializers.ValidationError(get_error('user_info_is_missing'))

            try:
                birthdate = datetime.datetime.strptime(birthdate , "%Y-%m-%d").date()
            except:
                raise serializers.ValidationError(get_error('bad_format_date'))


        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError(get_error('already_exist_mail'))
        

        if not self.context.get('request').user.is_superuser:
            if org_associated:
                org=org  = Organization.objects.get(id = int(org_associated))
            else:
                org = self.context.get('request').user.userinfo.org
        else:
            try:
                if 'is_superuser' in validated_data and  not validated_data['is_superuser']:
                    org  = Organization.objects.get(id = int(org))
            except:
                raise serializers.ValidationError(get_error('org_does_not_exist'))        

        try:
            with transaction.atomic():
                user = User.objects.create(**validated_data)
                if not user.is_superuser :
                    userinfo = UserInfo.objects.create(
                        user = user,
                        org = org,
                        birthdate = birthdate,
                        gender = gender,
                        phone = phone,
                        rfc = rfc, 
                        role = role,
                        another_tasks = another_tasks,
                        manage_profile = manage_profile,
                        is_user_lite=is_user_lite
                    )

                    if  userinfo.org.urlname != 'pruebas' and int(userinfo.manage_profile) in [1,2] and user.is_active and notificarContabilidad:
                        send_email_user_created(user, userinfo, int(userinfo.manage_profile))
                    if notificarEmail and is_user_lite:
                        send_email_user_created_lite(user, userinfo, int(userinfo.manage_profile))
                    # try:
                    #     send_email_user_created(user, userinfo)
                    # except:
                    #     pass
                    if 'profile' in self.context.get('request').data:
                        profile = Profile.objects.get(pk = self.context.get('request').data['profile'])
                        profile_to_empty = Profile.objects.filter(application = profile.application, user_info = userinfo)
                        for p in profile_to_empty:
                            p.user_info.remove(userinfo)
                        profile.user_info.add(userinfo)
                    
                    # guardar usuario en saam una vez creado en CAS
                    saved_user_saam = save_userinfo_saam(
                        org=org.urlname, 
                        username=validated_data['username'], 
                        firstname=validated_data['first_name'], 
                        lastname=validated_data['last_name'], 
                        email=validated_data['email'],
                        perfilRestringido = self.context.get('request').data.get('perfilRestringido'),
                        saam_exists=False,
                        saam_pair=[]
                    )
                    if not saved_user_saam:
                        raise serializers.ValidationError(get_error('error_saved_info_saam'))

                # raise serializers.ValidationError(get_error('profile_notfound'))
                return user
        except Exception as e:
            print(e)
            raise serializers.ValidationError(get_error('database_error'))

    class Meta:
        model = User
        fields = ('url','id', 'username', 'first_name', 'last_name', 
                  'email', 'is_staff', 'is_superuser', 'userinfo',
                  'password', 'password_confirm', 'is_active', 'role', 'perfilRestringido','nameperfilrestringido'
                  )
        
class VendorUserInfoSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
        
    class Meta:
        model = UserInfo
        fields = ('url','id', 'is_vendedor', 'is_active', 'user')



class VendorSerializer(serializers.HyperlinkedModelSerializer):
    userinfo = VendorUserInfoSerializer(many=False, read_only = True)
    # password = serializers.CharField(write_only=True)


    class Meta:
        model = User
        fields = ('url','id', 'username', 'first_name', 'last_name', 'userinfo')

class UserAppInfoSerializer(serializers.HyperlinkedModelSerializer):
    role = serializers.SerializerMethodField()
    email = serializers.CharField(required=True)
    userinfo = UserInfoSerializer(many=False, read_only = True)
    password = serializers.CharField(write_only=True, required=False, allow_null=True)
    password_confirm = serializers.CharField(write_only=True, required=False, allow_null=True)
    perfilRestringido = serializers.SerializerMethodField()
    nameperfilrestringido = serializers.SerializerMethodField()
    def get_perfilRestringido(self, obj):
        if obj.is_staff:
            try:
                r = guardar_perfil_usuario_restringido_saam(
                    self.context.get('request').user.id,
                    UserInfo.objects.get(user = obj).org.urlname,
                    obj.username
                )
                return r
            except Exception as e:
                print(e)
                return 0
        else:
            return 0

    def get_nameperfilrestringido(self, obj):
        if obj.is_staff:
            try:             
                r = guardar_perfil_usuario_restringidoname_saam(obj.id, obj.userinfo.org)
                return r
            except Exception as e:
                print(e)
                return 0
        else:
            return 0
    def get_role(self, user):
        try:
            role = user.userinfo.role
        except:
            role = 1
        return  role
    class Meta:
        model = User
        fields = ('url','id', 'username', 'first_name', 'last_name', 
                  'email', 'is_staff', 'is_superuser', 'userinfo',
                  'password', 'password_confirm', 'is_active', 'role', 'perfilRestringido','nameperfilrestringido'
                  )