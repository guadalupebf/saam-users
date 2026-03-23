from datetime import datetime, timedelta
from .models import PlantillaCorreo
from rest_framework import serializers

from accounts.models import UserInfo, Profile
from core.utils import Base64ImageField
from core.models import Application
from core.errors  import get_error
from .models import Organization, OrganizationApplication, Recibos, OrganizationFile, RecibosFile, CarouselGeneral
from .utils import save_orginfo_saam
from presigned_url import get_url_file, get_presigned_url
from django.conf import settings
from django.utils import timezone
folder = settings.MEDIAFILES_LOCATION

class OrganizationApplicationSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    
    def get_name(self, obj):
        return obj.application.name

    def get_id(self, obj):
        return obj.application.id
    class Meta:
        model = OrganizationApplication
        #fields = '__all__'
        #fields = ('is_active',)
        exclude = ('url',) 

class OrganizationFileHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OrganizationFile
        fields = ('url', 'id', 'owner', 'arch', 'nombre', 'sensible')
    def to_representation(self, instance):
        serializer = OrganizationFileHyperSerializer2(instance = instance, context={'request':self.context.get("request")}, many =False)
        return serializer.data    
class OrganizationFileHyperSerializer2(serializers.HyperlinkedModelSerializer):
    arch = serializers.SerializerMethodField()
    def get_arch(self,obj):
        
        return get_presigned_url(folder+"/{url}".format(url=obj.arch), 28800)     
    class Meta:    
        model = OrganizationFile
        fields = ('url', 'id', 'owner', 'arch', 'nombre', 'sensible')
class RecibosFileHyperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RecibosFile
        fields = ('url', 'id', 'owner', 'arch', 'nombre', 'sensible', 'tipo')
    def to_representation(self, instance):
        serializer = RecibosFileHyperSerializer2(instance = instance, context={'request':self.context.get("request")}, many =False)
        return serializer.data    
class RecibosFileHyperSerializer2(serializers.HyperlinkedModelSerializer):
    arch = serializers.SerializerMethodField()
    def get_arch(self,obj):
        
        return get_presigned_url(folder+"/{url}".format(url=obj.arch), 28800)     
    class Meta:    
        model = RecibosFile
        fields = ('url', 'id', 'owner', 'arch', 'nombre', 'sensible', 'tipo')
class RecibosInfoSerializer(serializers.HyperlinkedModelSerializer):
    forma_pago_display = serializers.SerializerMethodField()    
    pago = serializers.SerializerMethodField(read_only  = True)
    recibosFile = serializers.SerializerMethodField(read_only=True)  
    # -----
    def get_recibosFile(self, obj):
        orgf=RecibosFile.objects.filter(owner = obj)
        serializer = RecibosFileHyperSerializer(instance = orgf, context={'request':self.context.get("request")}, many = True)
        return serializer.data
    def get_forma_pago_display(self, obj):
        fpago= obj.forma_pago
        if obj.forma_pago ==1:
            fpago = 5
        if obj.forma_pago ==2:
            fpago = 1
        if obj.forma_pago ==3:
            fpago = 2
        if obj.forma_pago ==4:
            fpago = 4
        if obj.forma_pago ==5:
            fpago = 6
        if obj.forma_pago ==6:
            fpago = 12
        return fpago if fpago else obj.fpago
    def get_pago(self, obj):
        return obj.get_forma_pago_display()   
    status_vista = serializers.SerializerMethodField(read_only  = True)
    def get_status_vista(self, obj):
        return obj.get_status_display()
    class Meta:
        model = Recibos
        fields = (
                'id','recibo_numero','monto','monto_total','status','forma_pago','fecha_inicio',
                'fecha_fin','vencimiento','fecha_renovacion','description','org_name',
                'isActive','isextra','pago','status_vista','url','forma_pago_display','fecha_pago','recibosFile',
                'numero_factura','observations')

class RecibosDetailsHyperSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    informacion_org = serializers.SerializerMethodField()  
    forma_pago = serializers.SerializerMethodField()    
    forma_pago_display = serializers.SerializerMethodField()    
    pago = serializers.SerializerMethodField(read_only  = True)    
    recibosFile = serializers.SerializerMethodField()  
    correos_enviados = serializers.SerializerMethodField()  
    # -----
    def get_correos_enviados(self,obj):
        return CorreoRecibo.objects.filter(recibo= obj, enviado = True).count()
        
    def get_recibosFile(self, obj):
        orgf=RecibosFile.objects.filter(owner = obj)
        serializer = RecibosFileHyperSerializer(instance = orgf, context={'request':self.context.get("request")}, many = True)
        return serializer.data
    def get_informacion_org(self,obj):
        try:
            org_ = Organization.objects.get(pk=obj.organization.id)
            ser = OrganizationHyperSerializer(instance = org_, context={'request':self.context.get("request")}, many = False)
            return ser.data
        except Exception as e:
            print('error org',e)
            return {}
    def get_forma_pago(self, obj):
        if obj:
            fpago= obj.forma_pago
            if obj.forma_pago ==1:
                fpago = 5
            if obj.forma_pago ==2:
                fpago = 1
            if obj.forma_pago ==3:
                fpago = 2
            if obj.forma_pago ==4:
                fpago = 4
            if obj.forma_pago ==5:
                fpago = 6
            if obj.forma_pago ==6:
                fpago = 12
            return fpago if fpago else obj.forma_pago
        else:
            return ''
    def get_forma_pago_display(self, obj):
        if obj:
            fpago= obj.forma_pago
            if obj.forma_pago ==1:
                fpago = 5
            if obj.forma_pago ==2:
                fpago = 1
            if obj.forma_pago ==3:
                fpago = 2
            if obj.forma_pago ==4:
                fpago = 4
            if obj.forma_pago ==5:
                fpago = 6
            if obj.forma_pago ==6:
                fpago = 12
            return fpago if fpago else obj.forma_pago
        return ''
    def get_pago(self, obj):
        return obj.get_forma_pago_display()   
    status_vista = serializers.SerializerMethodField(read_only  = True)
    def get_status_vista(self, obj):
        return obj.get_status_display()
    class Meta:
        model = Recibos
        ordering = ('fecha_inicio', )
        fields = (
                'id','recibo_numero','monto','monto_total','status','forma_pago','fecha_inicio',
                'fecha_fin','vencimiento','fecha_renovacion','description','org_name','recibosFile',
                'isActive','isextra','informacion_org','pago','status_vista','url','forma_pago_display',
                'fecha_pago', 'correos_enviados', 'numero_factura','observations'
            )
class OrganizationHyperSerializer2(serializers.HyperlinkedModelSerializer):
        id = serializers.IntegerField(read_only=True)
        usuarios = serializers.SerializerMethodField()
        perfiles = serializers.SerializerMethodField()
        info_org = OrganizationApplicationSerializer(many=True, required=False)
        org_files = serializers.SerializerMethodField()    
        recibos_org = serializers.SerializerMethodField(read_only=True,required=False)    
        # RecibosDetailsHyperSerializer(many=True, required=False)
        last_receipt = serializers.SerializerMethodField(read_only=True,required=False)    
        # RecibosDetailsHyperSerializer(many=True, required=False)
        def get_last_receipt(self, obj):
            rec = (
                Recibos.objects
                .filter(organization=obj, isActive=True)
                .exclude(status=0)
                .exclude(fecha_fin__isnull=True)
                .order_by('-fecha_fin')  # máximo fecha_fin; en empate, mayor id
                .first()
            )

            if not rec:
                return None
            return RecibosInfoSerializer(
                instance=rec,
                context={'request': self.context.get("request")}
            ).data
        def get_recibos_org(self, obj):
            recs=Recibos.objects.filter(organization = obj, isActive=True).exclude(status=0)
            serializer = RecibosInfoSerializer(instance = recs, context={'request':self.context.get("request")}, many = True)
            return serializer.data
        def get_org_files(self, obj):
            orgf=OrganizationFile.objects.filter(owner = obj)
            serializer = OrganizationFileHyperSerializer(instance = orgf, context={'request':self.context.get("request")}, many = True)
            return serializer.data
        def get_usuarios(self, obj):
            return len(UserInfo.objects.filter(org = obj))
        def get_perfiles(self, obj):
            return len(Profile.objects.filter(org = obj))  
        
        logo = serializers.SerializerMethodField()
        def get_logo(self,obj):
            return get_url_file(obj.logo)
        logo_mini = serializers.SerializerMethodField()
        def get_logo_mini(self,obj):
            return get_url_file(obj.logo_mini)   
        class Meta:
            model = Organization
            fields = (
                    'name', 'urlname', 'alias', 'phone', 'email', 'logo', 
                    'logo_mini', 'address', 'webpage', 'url', 'id', 'usuarios', 
                    'perfiles', 'created_at', 'info_org', 'billiable', 'last_receipt',
                    'cobranza_pendiente','crear_usuarios_app','observations',
                    'phone_mensajeria','auth_token','account_sid','rfc','razon_social',
                    'gestor_cobranza','email_gestor', 'email_gestor1', 'email_gestor2','phone_gestor','org_files','is_org_demo',
                    'recibos_org','users_payed_op','users_payed_con','price_users_op','price_users_con',
                    'rfc_gestor','num_client','conducto_de_pago','users_payed_cr','price_users_cr','promedio_mensual',
                    'promedio_anual','phone_sms', 'messaging_service_sid','observations_cobranza','whatsappweb'

                )
from django.db.models import F, ExpressionWrapper, DurationField
class OrganizationHyperSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    usuarios = serializers.SerializerMethodField()
    perfiles = serializers.SerializerMethodField()
    info_org = OrganizationApplicationSerializer(many=True, required=False)
    org_files = serializers.SerializerMethodField()    
    recibos_org = serializers.SerializerMethodField(read_only=True,required=False)    
    last_receipt = serializers.SerializerMethodField(read_only=True,required=False)    
    # RecibosDetailsHyperSerializer(many=True, required=False)
    def get_last_receipt(self, obj):
        today = timezone.now().date()

        # Traer todos los recibos válidos
        recs = (
            Recibos.objects
            .filter(organization=obj, isActive=True)
            .exclude(status=0)
            .exclude(fecha_fin__isnull=True)
            .order_by('-fecha_fin', '-id')
        )
        # Seleccionar el que tenga fecha_fin más cercana a hoy
        if recs.exists():
            # Si hay futuros, dame el más próximo
            futuro = recs.filter(fecha_fin__gte=today).order_by('fecha_fin').first()
            if futuro:
                rec = futuro
            else:
                # Si no hay futuros, dame el último pasado
                rec = recs.order_by('-fecha_fin').first()

            serializer = RecibosInfoSerializer(
                instance=rec, context={'request': self.context.get("request")}
            )
            return serializer.data

        return None
    def get_recibos_org(self, obj):
        recs=Recibos.objects.filter(organization = obj, isActive=True).exclude(status=0)
        serializer = RecibosInfoSerializer(instance = recs, context={'request':self.context.get("request")}, many = True)
        return serializer.data
    def get_org_files(self, obj):
        orgf=OrganizationFile.objects.filter(owner = obj)
        serializer = OrganizationFileHyperSerializer(instance = orgf, context={'request':self.context.get("request")}, many = True)
        return serializer.data
    def get_usuarios(self, obj):
        return len(UserInfo.objects.filter(org = obj))
    def get_perfiles(self, obj):
        return len(Profile.objects.filter(org = obj))

    def create(self, validated_data):
        try:
            c_org_saam = save_orginfo_saam(validated_data['urlname'])
            if not c_org_saam:
                raise serializers.ValidationError(get_error('error_saved_info_saam'))
        except:
            pass
        return Organization.objects.create(**validated_data)          


    class Meta:
        model = Organization
        fields = (
                'name', 'urlname', 'alias', 'phone', 'email', 'logo', 'last_receipt',
                'logo_mini', 'address', 'webpage', 'url', 'id', 'usuarios', 
                'perfiles', 'created_at', 'info_org', 'billiable', 
                'cobranza_pendiente','crear_usuarios_app','observations',
                'phone_mensajeria','auth_token','account_sid','rfc','razon_social',
                'gestor_cobranza','email_gestor', 'email_gestor1', 'email_gestor2','phone_gestor','org_files','is_org_demo',
                'recibos_org','users_payed_op','users_payed_con','price_users_op','price_users_con',
                'rfc_gestor','num_client','conducto_de_pago','users_payed_cr','price_users_cr','promedio_mensual',
                'promedio_anual','phone_sms', 'messaging_service_sid','observations_cobranza','whatsappweb'
            )
    def to_representation(self, instance):
        serializer = OrganizationHyperSerializer2(instance = instance, context={'request':self.context.get("request")}, many =False)
        return serializer.data
   
class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'


class OrganizationMinSerializer(serializers.HyperlinkedModelSerializer):
    
    class Meta:
        model = Organization
        fields = ( 'url', 'id', 'name'  )

class OrganizationLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'urlname')


class OrganizationLogoSerializer(serializers.HyperlinkedModelSerializer):
    logo = Base64ImageField(
     max_length=None, use_url=True, 
    )
    class Meta:
        model = Organization
        fields = ( 'logo',  )
    
    def to_representation(self, instance):
        serializer = OrganizationLogoSerializer2(instance = instance, context={'request':self.context.get("request")}, many =False)
        return serializer.data
class OrganizationLogoSerializer2(serializers.HyperlinkedModelSerializer):    
        logo = serializers.SerializerMethodField()
        def get_logo(self,obj):
            return get_url_file(obj.logo)
        class Meta:
            model = Organization
            fields = ( 'logo',  )

class OrganizationLogoMiniSerializer(serializers.HyperlinkedModelSerializer):
    logo_mini = Base64ImageField(
     max_length=None, use_url=True, 
    )
    class Meta:
        model = Organization
        fields = ( 'logo_mini',  )
    
    def to_representation(self, instance):
        serializer = OrganizationLogoMiniSerializer2(instance = instance, context={'request':self.context.get("request")}, many =False)
        return serializer.data
class OrganizationLogoMiniSerializer2(serializers.HyperlinkedModelSerializer):    
        logo_mini = serializers.SerializerMethodField()
        def get_logo_mini(self,obj):
            return get_url_file(obj.logo_mini)   
        class Meta:
            model = Organization
            fields = ( 'logo_mini',  )

class OrganizationDetailsHyperSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    usuarios = serializers.SerializerMethodField()
    usuarios_activos = serializers.SerializerMethodField()
    usuarios_operativos = serializers.SerializerMethodField()
    usuarios_sinacceso = serializers.SerializerMethodField()
    usuarios_consulta = serializers.SerializerMethodField()
    usuarios_superusers = serializers.SerializerMethodField()
    usuarios_crestringida = serializers.SerializerMethodField()
    perfiles = serializers.SerializerMethodField()
    info_org = OrganizationApplicationSerializer(many=True, required=False)
    recibos_org = serializers.SerializerMethodField(read_only=True)
    saam_activo = serializers.SerializerMethodField()
    def get_saam_activo(self, obj):
        try:
            app_ = Application.objects.filter(name = 'SAAM')
            act = OrganizationApplication.objects.filter(organization = obj, application__in = app_)
            if act.exists():
                act = act.first()
                if act.is_active:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            print('error active',e)
            return False
    def get_recibos_org(self, obj):
        try:
            recs = Recibos.objects.filter(organization=obj, org_name=obj.urlname, isActive=True).exclude(status =0).order_by('fecha_inicio')
            ser = RecibosInfoSerializer(instance = recs, context={'request':self.context.get("request")}, many = True)
            return ser.data
        except Exception as e:
            print('error recibos',e)
            return []
    def get_usuarios(self, obj):
        return len(UserInfo.objects.filter(org = obj))
    def get_perfiles(self, obj):
        return len(Profile.objects.filter(org = obj))      
    def get_usuarios_activos(self,obj):        
        return len(UserInfo.objects.filter(org = obj,is_active=True).exclude(manage_profile=3))
    def get_usuarios_sinacceso(self,obj):        
        return len(UserInfo.objects.filter(org = obj,is_active=True,manage_profile=0))
    def get_usuarios_operativos(self,obj):        
        return len(UserInfo.objects.filter(org = obj,is_active=True,manage_profile=1))
    def get_usuarios_consulta(self,obj):        
        return len(UserInfo.objects.filter(org = obj,is_active=True,manage_profile=2))
    def get_usuarios_superusers(self,obj):        
        return len(UserInfo.objects.filter(org = obj,is_active=True,manage_profile=3))
    def get_usuarios_crestringida(self,obj):        
        return len(UserInfo.objects.filter(org = obj,is_active=True,manage_profile=4))
    class Meta:
        model = Organization
        fields = (
                'name', 'urlname', 'alias', 'phone', 'email', 'logo', 
                'logo_mini', 'address', 'webpage', 'url', 'id', 'usuarios', 
                'perfiles', 'created_at', 'info_org', 'billiable', 
                'cobranza_pendiente','crear_usuarios_app','observations',
                'phone_mensajeria','auth_token','account_sid','saam_activo',
                'usuarios_activos','usuarios_operativos','usuarios_sinacceso','is_org_demo',
                'usuarios_consulta','usuarios_superusers','rfc','razon_social','promedio_mensual','promedio_anual',
                'gestor_cobranza','email_gestor', 'email_gestor1', 'email_gestor2','phone_gestor','recibos_org','users_payed_op','users_payed_con',
                'price_users_op','price_users_con','rfc_gestor','num_client','conducto_de_pago','users_payed_cr','price_users_cr',
                'usuarios_crestringida','phone_sms', 'messaging_service_sid','observations_cobranza'
            )

class RecibosHyperSerializer(serializers.HyperlinkedModelSerializer):
    informacion_org = serializers.SerializerMethodField() 
    forma_pago_display = serializers.SerializerMethodField()    
    pago = serializers.SerializerMethodField(read_only  = True)
    recibosFile = serializers.SerializerMethodField(read_only=True)  
    recibosFile = serializers.SerializerMethodField()  
    
    def get_recibosFile(self, obj):
            orgf=RecibosFile.objects.filter(owner = obj, tipo__in = [1,2,3])
            serializer = RecibosFileHyperSerializer(instance = orgf, context={'request':self.context.get("request")}, many = True)
            return serializer.data
    # -----
    def get_recibosFile(self, obj):
        orgf=RecibosFile.objects.filter(owner = obj)
        serializer = RecibosFileHyperSerializer(instance = orgf, context={'request':self.context.get("request")}, many = True)
        return serializer.data
    # -----
    def get_informacion_org(self,obj):
        try:
            org_ = Organization.objects.get(pk=obj.organization.id)
            ser = OrganizationHyperSerializer(instance = org_, context={'request':self.context.get("request")}, many = False)
            return ser.data
        except Exception as e:
            print('error org',e)
            return {}
    def get_forma_pago_display(self, obj):
        fpago=''
        if obj and obj.forma_pago:
            fpago= obj.forma_pago
            if obj.forma_pago ==1:
                fpago = 5
            if obj.forma_pago ==2:
                fpago = 1
            if obj.forma_pago ==3:
                fpago = 2
            if obj.forma_pago ==4:
                fpago = 4
            if obj.forma_pago ==5:
                fpago = 6
            if obj.forma_pago ==6:
                fpago = 12
            return fpago if fpago else obj.forma_pago
        else:
            return fpago if fpago else obj.forma_pago if obj and obj.forma_pago else 'Sin forma de pago'
    def get_pago(self, obj):
        if obj.forma_pago:
            return obj.get_forma_pago_display()   
        else:
            return 'Sin forma de pago'  
    status_vista = serializers.SerializerMethodField(read_only  = True)
    def get_status_vista(self, obj):
        if obj and obj.status:
            return obj.get_status_display()
        else:
            return 'Sin status'
    def get_informacion_org(self,obj):
            try:
                org_ = Organization.objects.get(pk=obj.organization.id)
                ser = OrganizationHyperSerializer(instance = org_, context={'request':self.context.get("request")}, many = False)
                return ser.data
            except Exception as e:
                print('error org',e)
                return {}
    def create(self, validated_data):
        try:
            parsed_date = datetime.strptime(self.request.data['fecha_fin'], "%Y-%m-%d")
            new_date = parsed_date + timedelta(days=1)
        except Exception as t:
            pass
        return Recibos.objects.create(**validated_data)
    class Meta:
        model = Recibos
        fields = (
                'id','recibo_numero','monto','monto_total','status','forma_pago','fecha_inicio',
                'fecha_fin','vencimiento','fecha_renovacion','description','org_name','recibosFile',
                'isActive','isextra','informacion_org','pago','status_vista','url','forma_pago_display','fecha_pago',
                'recibosFile', 'numero_factura','observations')
class CarouselDetailsSerializer(serializers.HyperlinkedModelSerializer):
    imagen = Base64ImageField(
     max_length=None, use_url=True, 
    )
    class Meta:
        model = CarouselGeneral
        fields = '__all__'
    
    def to_representation(self, instance):
        serializer = CarouselSerializer2(instance = instance, context={'request':self.context.get("request")}, many =False)
        return serializer.data
class CarouselSerializer2(serializers.HyperlinkedModelSerializer):
    imagen = serializers.SerializerMethodField()
    def get_imagen(self,obj):        
        return get_url_file(obj.imagen)   
    class Meta:    
        model = CarouselGeneral
        fields = ('url', 'id', 'imagen', 'nombre', 'description', 'visible')
        
        
        

# Serializador para PlantillaCorreo
class PlantillaCorreoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PlantillaCorreo
        fields = ('id', 'nombre', 'html', 'url', 'subject')
# Serializador para CorreoRecibo
from .models import CorreoRecibo

class CorreoReciboSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CorreoRecibo
        fields = ('url', 'id', 'recibo', 'subject', 'message', 'destinatarios', 
                  'plantilla', 'enviado', 'facturaSeleccionada', 'comprobanteSeleccionado', 
                  'complementoSeleccionado', 'error', 'archivos_enviados', 'created_at'
                )
