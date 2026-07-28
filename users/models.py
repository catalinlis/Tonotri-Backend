from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from datetime import date
from media.models import Image
from explore.models import Country
import uuid

# Create your models here.
class User(AbstractUser):
    class Gender(models.TextChoices):
        MALE = 'male'
        FEMALE = 'female'

    class RegistrationStep(models.TextChoices):
        ADD_PHOTO = "ADD_PHOTO"
        VISITED_COUNTRIES = "VISITED_COUNTRIES"
        DONE = "DONE"

    username = models.CharField(
        max_length = 20,
        unique = True,
        validators=[MinLengthValidator(6)]
    )
    email = models.EmailField(null=False, unique=True)
    first_name = models.CharField(max_length=20, null=True)
    last_name = models.CharField(max_length=20, null=True)
    birthday = models.DateField(default=date(1970,1,1))
    gender = models.CharField(choices=Gender.choices,null=True)
    guid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    is_active = models.BooleanField(default=True)
    regular_user = models.BooleanField(default=False)
    confirmed_email = models.BooleanField(default=False)
    register_step = models.CharField(choices=RegistrationStep.choices, default=RegistrationStep.ADD_PHOTO)
    profile_image = models.OneToOneField(Image, null=True, blank=True, on_delete=models.SET_NULL)
    visited_countries = models.ManyToManyField(Country, related_name='users', blank=True)