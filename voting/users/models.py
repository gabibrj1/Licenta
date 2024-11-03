from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

#manager personalizat pentru User
class CustomUserManager(BaseUserManager):
    #crearea unui utilizator obisnuit
    def create_user(self, email=None, password=None, cnp=None, **extra_fields):
        if not email and not cnp:
            raise ValueError('Utilizatorii trebuie să aibă fie o adresă de email, fie un CNP.')
        user = self.model(
            email=self.normalize_email(email) if email else None,
            cnp=cnp,
            **extra_fields
        )

        #setam parola daca este furnizata 
        if password:
            user.set_password(password)

        user.save(using=self._db)
        return user

def create_superuser(self, email, password=None, **extra_fields):
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_superuser', True)
    extra_fields.setdefault('is_active', True)

    #verif ca atributele pt admin sa fie corecte
    if extra_fields.get('is_staff') is not True:
        raise ValueError('Superuser must have is_staff=True.')
    if extra_fields.get('is_superuser') is not True:
        raise ValueError('Superuser must have is_superuser=True.')

    return self.create_user(email, password, **extra_fields)

#modelul personalizat de utilizator
class User(AbstractBaseUser, PermissionsMixin):
    #email ul este unic, dar optional, pt a permite autentif si prin buletin
    email = models.EmailField(_('email address'), unique=True, blank=True, null=True)
    first_name = models.CharField(_('first name'), max_length=255, blank=True)
    last_name = models.CharField(_('last name'), max_length=255, blank=True)
    cnp = models.CharField(max_length=13, blank=True, null=True, unique=True)

    # Detalii buletin
    series = models.CharField(max_length=2, blank=True, null=True)
    number = models.CharField(max_length=6, blank=True, null=True)
    place_of_birth = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    issuing_authority = models.CharField(max_length=100, blank=True, null=True)
    sex = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')], blank=True, null=True)
    date_of_issue = models.DateField(blank=True, null=True)
    date_of_expiry = models.DateField(blank=True, null=True)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    is_verified_by_id = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    #asociem managerul personalizat
    objects = CustomUserManager()

    #repr text a modelului ( email sau cnp )
    def __str__(self):
        return self.email if self.email else self.cnp

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
