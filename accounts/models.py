from django.db import models
from django.contrib.auth.models import User
from django.http import Http404

from organizations.models import Organization
from core.models import Application, TimeStampedModel
from custom_storages import ModelPublicoStorage
# Create your models here.
GENDER_CHOICES = ((1, 'Hombre'), (2, 'Mujer'))
TIPE_PROFILE_CHOICES = ((1, 'Operativo'), (2, 'Consulta'))
MANAGE_PROFILE_CHOICES = ((0, 'Sin acceso'),(1, 'Operativo'), (2, 'Consulta'), (3, 'Superusuario'), (4, 'Consulta Restringida'))
ROLE = (
    (0,'Admin'),
    (1,'SubAdmin'),
    (2,'Agente'),
    (3,'Vendedor'),
    (4,'Usuario')
    )

base = 'users/{org}/avatars/{img}'

def file_type(instance, filename):
    return base.format(org=instance.org.urlname, img=filename)

def get_avatar(instance, filename):
    return file_type(instance, filename)


class ModelPermission(models.Model):
    name = models.CharField(max_length=50) 
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name = 'application_models')

    def __str__(self):
        return self.name

class Permission(models.Model):
    model = models.ForeignKey(ModelPermission, on_delete=models.CASCADE, related_name='permission_model')
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    


class UserPermission(TimeStampedModel):
    profile = models.ForeignKey("Profile",  on_delete=models.CASCADE, related_name = 'profile_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    checked =  models.BooleanField(default=True)
    is_active = models.BooleanField(default = True)

    class Meta:
        unique_together = ('profile', 'permission')




class UserInfo(TimeStampedModel):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    org = models.ForeignKey(Organization, on_delete=models.DO_NOTHING, null = True, blank = True)
    avatar = models.ImageField(upload_to=get_avatar, null=True, blank=True,storage=ModelPublicoStorage())
    role = models.IntegerField(default=0,choices=ROLE, null=False)
    activation_number = models.IntegerField(null=True, blank=True)
    phone = models.CharField(max_length = 50, null = True, blank=True)
    birthdate = models.DateField(null = True, blank=True)
    gender = models.IntegerField(default = 1, choices = GENDER_CHOICES)
    manage_profile = models.IntegerField(default = 0, choices = MANAGE_PROFILE_CHOICES)
    rfc = models.CharField(max_length = 20, null = True)
    is_vendedor = models.BooleanField(default=False)
    is_personal = models.BooleanField(default=False)
    is_delivery = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    fcm_token = models.CharField(max_length=500, null = True)
    tutorial = models.BooleanField(default=True)
    another_tasks = models.BooleanField(default=False)
    identifier = models.CharField(max_length=500, null = True)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, null = True, blank = True, related_name = 'user_owner')
    name_org = models.CharField(max_length=500, null = True)
    ultimo_acceso_saam = models.DateTimeField(null = True, blank = True)
    is_user_lite = models.BooleanField(default=False)
    
    def __str__(self):
        return "{}-{}".format(self.user.first_name,self.user.username)


class Profile(TimeStampedModel):
    name = models.CharField(max_length=50, default='Indefinido')
    is_active = models.BooleanField(default=True)
    org = models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    user_info = models.ManyToManyField(UserInfo, blank=True, related_name = 'user_profiles')
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    type_profile = models.IntegerField(default = 1, choices = TIPE_PROFILE_CHOICES) 
    
    class Meta:
        unique_together = ('name', 'org')

    def __str__(self):
        return self.name


#class ProfileApplication(models.Model):
#    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='profile_application')
#    application = models.ForeignKey(Application, on_delete=models.CASCADE)
#    is_active = models.BooleanField()
#
#    class Meta:
#        unique_together = ('profile', 'application')

