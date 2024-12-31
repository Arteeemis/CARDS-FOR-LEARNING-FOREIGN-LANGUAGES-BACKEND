from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, UserManager, AbstractBaseUser, BaseUserManager


# Create your models here.

class WordLists(models.Model):
    status = models.CharField(max_length=10)
    creation_date = models.DateField()
    submition_date = models.DateField(blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)
    creator = models.IntegerField()
    moderator = models.IntegerField(blank=True, null=True)
    learn_until_date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=30) #заполняеморе поле
    time_to_learn = models.IntegerField(blank=True, null=True) #вычисляемое поле

    class Meta:
        managed = False
        db_table = 'word_lists'


class WordCards(models.Model):
    status = models.CharField(max_length=10)
    word = models.CharField(max_length=30)
    word_level = models.CharField(max_length=5)
    word_language = models.CharField(max_length=30)
    word_class = models.CharField(max_length=30)
    word_description = models.TextField(blank=True, null=True)
    word_translation = models.CharField(max_length=255)
    word_example = models.TextField(blank=True, null=True)
    word_synonyms = models.CharField(max_length=255, blank=True, null=True)
    word_image = models.TextField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'word_cards'


class CardsLists(models.Model):
    card = models.ForeignKey('WordCards', models.SET_NULL, blank=True, null=True)
    list = models.ForeignKey('WordLists', models.SET_NULL, blank=True, null=True)
    lists_order = models.IntegerField(blank=True, null=True, default=1)

    class Meta:
        managed = False
        db_table = 'cards_lists'
        unique_together = ('card', 'list')


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    username = models.CharField(unique=True, max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=150)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        managed = False
        db_table = 'auth_user'


# class User(models.Model):
#     password = models.CharField(max_length=128)
#     username = models.CharField(unique=True, max_length=150)
#     email = models.CharField(max_length=254)

#     class Meta:
#         verbose_name = "Пользователь"
#         verbose_name_plural = "Пользователи"
#         db_table = 'word_cards'
#         managed = False
        


class NewUserManager(UserManager):
    def create_user(self,email,password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields) 
        user.set_password(password)
        user.save(using=self.db)
        return user

# class CustomUser(AbstractBaseUser, PermissionsMixin):
#     email = models.EmailField(("email адрес"), unique=True)
#     password = models.CharField(max_length=128, verbose_name="Пароль")    
#     is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь менеджером?")
#     is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь админом?")

#     USERNAME_FIELD = 'email'

#     objects =  NewUserManager()
