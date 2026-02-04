from django.contrib.auth.models import AbstractUser,PermissionsMixin
from django.db import models
from django.contrib.auth.models import UserManager
from django.contrib.auth.base_user import BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from uuid import uuid4
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("メールアドレスは必須です")

        email = self.normalize_email(email)
        username = extra_fields.pop("username", None)
        if not username:
            username = email.split("@")[0]
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = models.CharField(max_length=255, unique=True, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
class UserActivateToken(models.Model):
    token = models.UUIDField(db_index=True, unique=True)
    expired_at = models.DateTimeField()
    user = models.OneToOneField(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='user_activate_token'
    )

    

    class Meta:
        db_table = 'user_activate_token'

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, blank=True)
    birthday = models.DateField(null=True, blank=True)
    goal = models.CharField(max_length=20, blank=True)
    icon = models.ImageField(upload_to='icons/', blank=True, null=True)

    def __str__(self):
        return self.user.email

@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    if created:
      Profile.objects.create(user=instance)

#@receiver(post_save, sender=CustomUser)
#def publish_token(sender, instance,created, **kwargs):
#    user_activate_token = UserActivateToken.objects.create_or_update_token(instance)
#    print(
#        f'http://127.0.0.1:8000/accounts/activate_user/{user_activate_token.token}'
   #     )
# Create your models here.

class StudyRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=50)
    date = models.DateField()
    achieved = models.BooleanField(default=True)
    result = models.CharField(
        max_length=20,
        choices=[
            ('achieved', '達成'),('not_achieved', '未達成'),
            ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    stamp_shape = models.CharField(max_length=20, blank=True)
    stamp_color = models.CharField(max_length=20, blank=True)
                                                      

class Goal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    date = models.DateField()
    subject = models.CharField(max_length=50)
    study_hour = models.IntegerField(default=0)
    study_minute = models.IntegerField(default=0)
    page_start = models.IntegerField(null=True, blank=True)
    page_end = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.subject}"
         