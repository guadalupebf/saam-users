from django.db import models

# Create your models here.


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-
    . fields.
    updating ``created`` and ``updated_at``
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


        

class Application(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    


class DemoRequest(TimeStampedModel):
    email = models.EmailField(max_length=70, unique=True)
    name = models.CharField(max_length=200)
    telefono = models.CharField(max_length=200, null=True, blank=True)
    status = models.CharField(max_length=50, default = 'PENDIENTE')

