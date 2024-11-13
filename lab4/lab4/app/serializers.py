from app.models import WordCards, WordLists, CardsLists, User
from rest_framework import serializers
from collections import OrderedDict
from app.models import CustomUser



class WordCardsSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = WordCards
        # Поля, которые мы сериализуем
        fields = [
                    'pk',
                    'status',
                    'word',
                    'word_level',
                    'word_language',
                    'word_class',
                    'word_description',
                    'word_translation',
                    'word_example',
                    'word_synonyms',
                    'word_image',
                 ]
        
        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields
        
        
        

class WordListsSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = WordLists
        # Поля, которые мы сериализуем
        fields = [
                    'pk', 
                    'status' , 
                    'creation_date',
                    'submition_date', 
                    'completion_date',    
                    'creator',   
                    'moderator',  
                    'learn_until_date'  
                 ]
        
        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields
        

class CardsListsSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = CardsLists
        # Поля, которые мы сериализуем
        fields = [
                    'pk', 
                    'card',
                    'list',
                    'lists_order' 
                 ]
        
        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields
        
        
        

class UserRegisterSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True)

  class Meta:
    model = User
    fields = ['username', 'email', 'password']

  def create(self, validated_data):
    user = User(**validated_data) # Сохраняем пароль без хеширования
    user.save()
    return user
  

class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'is_staff', 'is_superuser']


class ResolveWordList(serializers.ModelSerializer):
    class Meta:
        model = WordLists
        fields = ['status']


