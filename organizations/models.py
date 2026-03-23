from django.db import models
from core.models import Application
from core.models import TimeStampedModel
from decimal import Decimal
import random
from custom_storages import ModelPublicoStorage
# Create your models here.

base = '{org}/logos/{img}'
base_carousel = '{org}/carousel/{img}'
base_files = '{org}/files/{img}'

def file_type(instance, filename):
    return base.format(org=instance.urlname, img=filename)

def get_logo(instance, filename):
    return file_type(instance, filename)
def file_type_recibo(filetype, instance, filename):
    return base_files.format(org=instance.owner.id, type=filetype, img=filename.replace(' ', ''), id=instance.owner.id, file_id = random.randint(1,10001)) 
def file_type_org(filetype, instance, filename):
    return base_files.format(org=instance.owner.urlname, type=filetype, img=filename.replace(' ', ''), id=instance.owner.id, file_id = random.randint(1,10001)) 

def get_organizationfile(instance, filename):
    return file_type_org('organization', instance, filename)

def get_recibosfile(instance, filename):
    return file_type_recibo('recibos', instance, filename)

def fileCarousel(instance, filename):
    return base_carousel.format(org='general', img=filename)

def get_images_carousel(instance, filename):
    return fileCarousel(instance, filename)

STATUS = [ (1,'Pendiente'), (2,'Pagado'), (25,'Pagado por actualizar'), (3,'Cancelado'),(4,'Renovado'),(0,'Eliminado')]
PAYFORM = [ (1,'Contado'), (2,'Anual'), (3,'Semestral'),(4,'Trimestral'),(5,'Bimestral'),(6,'Mensual')]
DOMICILIADA_CHOICES = [(0,'No Domiciliada'), (1,'Domiciliada')]

TIPO_ARCHIVO_CHOICES = [
    (1,'Factura'), 
    (2,'Comprobante de pago'),
    (3,'Complemento'),
    (4,'Otro'),
]

class Organization(TimeStampedModel):
    name = models.CharField(max_length = 100)
    urlname = models.CharField(max_length = 50, unique = True)
    alias = models.CharField(max_length = 50,default = '')
    phone = models.CharField(max_length = 30,null = True)
    email = models.EmailField(null = True)
    logo = models.ImageField(upload_to = get_logo, null = True, blank=True,storage=ModelPublicoStorage())
    logo_mini = models.ImageField(upload_to = get_logo, null = True, blank=True,storage=ModelPublicoStorage())
    address = models.CharField(max_length = 250, null = True, blank = True)
    webpage = models.CharField(max_length = 250, null = True, blank = True)
    billiable = models.BooleanField(default=True)
    cobranza_pendiente = models.BooleanField(default=False)
    crear_usuarios_app = models.BooleanField(default=False)
    observations = models.CharField(max_length = 700, null = True, blank = True)
    phone_mensajeria = models.CharField(max_length = 30,null = True)
    phone_sms = models.CharField(max_length = 30,null = True)
    auth_token =  models.CharField(max_length = 50,null = True)
    account_sid = models.CharField(max_length = 50,null = True)
    messaging_service_sid = models.CharField(max_length = 50,null = True)
    rfc = models.CharField(max_length = 50,null = True)
    razon_social = models.CharField(max_length = 50,null = True)
    gestor_cobranza = models.CharField(max_length = 50,null = True)
    email_gestor = models.CharField(max_length = 50,null = True, blank = True)
    email_gestor1 = models.CharField(max_length = 50,null = True, blank = True)
    email_gestor2 = models.CharField(max_length = 50,null = True, blank = True)
    phone_gestor = models.CharField(max_length = 50,null = True)
    users_payed_op= models.CharField(max_length = 50,null = True)
    users_payed_con= models.CharField(max_length = 50,null = True)
    price_users_op= models.CharField(max_length = 50,null = True)
    price_users_con= models.CharField(max_length = 50,null = True)
    rfc_gestor= models.CharField(max_length = 50,null = True)
    num_client= models.CharField(max_length = 50,null = True)
    users_payed_cr= models.CharField(max_length = 50,null = True)
    price_users_cr= models.CharField(max_length = 50,null = True)
    promedio_mensual = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0"), blank=True, null=True)
    promedio_anual = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0"), blank=True, null=True)
    is_org_demo = models.BooleanField(default=False)
    observations_cobranza = models.CharField(max_length = 700, null = True, blank = True)

    conducto_de_pago = models.IntegerField(choices = DOMICILIADA_CHOICES, default = 0)
    whatsappweb = models.BooleanField(default=True, null=True, blank=True)



    def __str__(self):
        return self.name

class OrganizationApplication(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name = 'info_org')
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    is_demo = models.BooleanField(default = False)
    date_demo = models.DateTimeField(null = True, blank = True)

class OrganizationFile(TimeStampedModel):
    owner = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name = 'file_info_org', null = True)
    arch = models.FileField(upload_to = get_organizationfile, max_length=500)
    nombre = models.CharField(max_length = 500)
    sensible = models.BooleanField(default = False)

class Recibos(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name = 'informacion_org',blank=True)
    recibo_numero = models.IntegerField(blank=True, null=True)
    monto = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0"), blank=True, null=True)
    monto_total = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0"), blank=True, null=True)
    status = models.IntegerField(blank=True, null=True, default=1, choices = STATUS, db_index=True)
    forma_pago = models.IntegerField(blank=True, null=True, default=1, choices = PAYFORM, db_index=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    fecha_pago = models.DateField(null=True, blank=True)
    vencimiento = models.DateField(null=True, blank=True)    
    fecha_renovacion = models.DateField(null=True, blank=True)
    org_name = models.CharField(max_length=50, null=True)
    isActive= models.BooleanField(default=True, db_index=True)
    # only if recibo is extra
    isextra = models.BooleanField(default = False)
    description = models.TextField(blank=True, null=True)
    numero_factura = models.CharField(max_length=100, null=True)
    observations = models.TextField(blank=True, null=True)

class RecibosFile(TimeStampedModel):
    owner = models.ForeignKey(Recibos, on_delete=models.CASCADE, related_name = 'file_info_recibos', null = True)
    arch = models.FileField(upload_to = get_recibosfile, max_length=500)
    nombre = models.CharField(max_length = 500)
    sensible = models.BooleanField(default = False)
    tipo = models.IntegerField(choices = TIPO_ARCHIVO_CHOICES, default = 4)
    

class CarouselGeneral(TimeStampedModel):
    imagen = models.ImageField(upload_to = get_images_carousel, null = True, blank=True,storage=ModelPublicoStorage())
    nombre = models.CharField(max_length = 500, null = True, blank=True)
    description = models.CharField(max_length = 500, null = True, blank=True)
    visible = models.BooleanField(default = True)
    
    

# PlantillaCorreo model
class PlantillaCorreo(TimeStampedModel):
    nombre = models.CharField(max_length=150)
    html = models.TextField()
    subject = models.CharField(max_length=500)

    def __str__(self):
        return self.nombre
    


# CorreoRecibo model
class CorreoRecibo(TimeStampedModel):
    recibo = models.ForeignKey(Recibos, on_delete=models.CASCADE, related_name='correos')
    subject = models.CharField(max_length=500)
    message = models.TextField()
    destinatarios = models.TextField(help_text="Lista de correos separados por coma")
    plantilla = models.ForeignKey(PlantillaCorreo, on_delete=models.SET_NULL, null=True, blank=True)
    enviado = models.BooleanField(default=False)
    facturaSeleccionada = models.BooleanField(default=False)
    comprobanteSeleccionado = models.BooleanField(default=False)
    complementoSeleccionado = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)
    archivos_enviados = models.TextField(null=True, blank=True)

    
