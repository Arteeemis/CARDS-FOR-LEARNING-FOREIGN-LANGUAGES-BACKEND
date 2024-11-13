from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from app.serializers import WordCardsSerializer, WordListsSerializer, CardsListsSerializer, UserRegisterSerializer, ResolveWordList, UserSerializer
from app.models import WordCards, WordLists, CardsLists, User, CustomUser
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from .minio import add_pic, delete_pic
import datetime
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from .permissions import IsAdmin, IsManager, IsAuth
from django.conf import settings
import redis
import uuid
from .auth import Auth_by_Session, AuthIfPos
from .redis import session_storage


# SINGLE_USER = User(id=2, username='valeron', email='valeron@gmail.com', password='valeron_rox')
# SINGLE_ADMIN = User(id=3, username='admin', email='admin@gmail.com', password='admin')


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([AuthIfPos])
def get_word_cards(request, format=None):
  # word_cards = WordCards.objects.all().order_by('word_level') 
  word_list = get_object_or_404(WordLists, creator=request.user.id, status='draft')
  word_cards = WordCards.objects.filter(cardslists__list=word_list).order_by('cardslists__lists_order') 
  cards = CardsLists.objects.filter(list=word_list).count()
  
  # Get the list order for each card
  card_orders = {}
  for card in word_cards:
    try:
      card_order = CardsLists.objects.get(list=word_list, card=card).lists_order
      card_orders[card.pk] = card_order
    except CardsLists.DoesNotExist:
      card_orders[card.pk] = None # Or handle the missing order as needed

  # Serialize the data with the order included
  serializer = WordCardsSerializer(word_cards, many=True)
  data = {
    "word_list_id": word_list.id,
    "cards_in_list": cards,
    "cards": [
      {
        "lists_order": card_orders.get(card['pk']),
        "word": card['word'],
        "word_level": card['word_level'],
        "word_language": card['word_language'],
        "word_class": card['word_class'],
        "word_translation": card['word_translation'],
        "word_image": card['word_image']
      } 
      for card in serializer.data
    ]
  }
  return Response(data)



# Возвращает информацию о карточке
@api_view(['GET'])
@permission_classes([AllowAny])
def get_word_card_info(request, pk, format=None):
  word_card = get_object_or_404(WordCards, pk=pk)
  serializer = WordCardsSerializer(word_card)
  return Response(serializer.data)


# Добавляет новую карточку
@swagger_auto_schema(method='post', request_body=WordCardsSerializer)
@api_view(['POST'])
@permission_classes([IsManager])
@authentication_classes([Auth_by_Session])
def add_word_card(request, format=None):
  serializer = WordCardsSerializer(data=request.data)
  if serializer.is_valid():
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)
  return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 


# Обновляет информацию о карточке  
@swagger_auto_schema(method='put', request_body=WordCardsSerializer)
@api_view(['PUT'])
@permission_classes([IsManager])
@authentication_classes([Auth_by_Session])
def update_card_info(request, pk, format=None):
  word_card = get_object_or_404(WordCards, pk=pk)
  serializer = WordCardsSerializer(word_card, data=request.data, partial=True)
  if serializer.is_valid():
    serializer.save()
    return Response(serializer.data)
  return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Удаляет карточку 
@api_view(['DELETE'])
@permission_classes([IsManager])
@authentication_classes([Auth_by_Session])
def delete_card(request, pk, format=None):
  word_card = get_object_or_404(WordCards, pk=pk)
  delete_pic(word_card)
  word_card.delete()
  return Response(status=status.HTTP_204_NO_CONTENT)


# Добавляет картинку карточке
@swagger_auto_schema(method='post', request_body=WordCardsSerializer)
@api_view(['POST'])
@permission_classes([IsManager])
@authentication_classes([Auth_by_Session])
def add_card_img(request, pk, format=None):
  word_card = get_object_or_404(WordCards, pk=pk)
  serializer = WordCardsSerializer(word_card)
  pic = request.FILES.get('pic')
  if pic:
    if word_card.word_image != 'null':
        delete_pic(word_card)
        print(pic)
    pic_result = add_pic(serializer.instance, pic)
    if 'error' in pic_result.data:
        return pic_result
  return Response(status=status.HTTP_204_NO_CONTENT)


#добвить в список
@swagger_auto_schema(method='post', request_body=None)
@api_view(['POST'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def add_to_list(request, pk):
    word_card = WordCards.objects.filter(id=pk).first()
    if word_card is None:
        return Response('No such card', status=status.HTTP_404_NOT_FOUND)
    req = WordLists.objects.filter(creator = request.user.id, status='draft').first()
    if not(req):
      words_list = WordLists.objects.create(status="draft", creation_date=datetime.datetime.now().date(), creator=request.user.id)
      words_list.save()
      req = words_list
    word_list_id = req.id
    existing_cards_count = CardsLists.objects.filter(list=req).count()
    order = existing_cards_count + 1
    card_list = CardsLists.objects.filter(card=pk, list=word_list_id).first()
    if not card_list:
        list_card = CardsLists(card=word_card, list=req, lists_order=order)
        list_card.save()
    return Response('Succesfully added card to list')

#удалить из списка
@api_view(['DELETE'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def delete_from_list(request, ck, lk):
    word_list = WordLists.objects.filter(pk=lk)
    if not request.user.is_staff and word_list.creator != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    card_in_list = CardsLists.objects.filter(card=ck, list=lk).first()
    print(ck , lk)
    if card_in_list is None:
        return Response("Card not found", status=status.HTTP_404_NOT_FOUND)
    card_in_list.delete()
    # list_id = card_in_list.list
    # print(list_id)
    # card_id = card_in_list.card
    # word_list = WordLists.objects.filter(id=lk).first()
    # card = WordCards.objects.filter(id=ck).first()
    # word_list.save()
    return Response('Card deleted from list', status=status.HTTP_200_OK)

#изменить карточку в списке
@swagger_auto_schema(method='put', request_body=None)
@api_view(['PUT'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def change_card_in_list(request, ck, lk):
    print(ck, lk)
    word_list = WordLists.objects.get(pk=lk)
    if not request.user.is_staff and word_list.creator != request.user.id:
        return Response(status=status.HTTP_403_FORBIDDEN)
    card_in_list = CardsLists.objects.get(card=ck, list=lk)
    if card_in_list is None:
        return Response("Card not found", status=status.HTTP_404_NOT_FOUND)
    print(word_list, card_in_list)
    # Get the current order of the card being changed
    current_order = card_in_list.lists_order
    # Move the card to the top of the list
    card_in_list.lists_order += 1  
    card_in_list.save()
    # Adjust other cards in the list
    other_cards = CardsLists.objects.filter(list=lk).exclude(card=ck)
    for card in other_cards:
        if card.lists_order > current_order:
            card.lists_order -= 1
        elif card.lists_order < current_order:  # No need for second condition here
            card.lists_order += 1
        card.save()
    return Response({"message": "Card position updated successfully."}, status=status.HTTP_200_OK) 


#Возращает информацию о заявке
@api_view(['GET'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def get_word_list_info(request, pk, format=None):
    try:
        if not request.user.is_staff:
          word_list = WordLists.objects.get(pk=pk, creator = request.user.id)
        else:
          word_list = WordLists.objects.get(pk=pk)
    except WordLists.DoesNotExist:
        return Response({"error": "Список не найден"}, status=status.HTTP_404_NOT_FOUND)
    # word_cards = WordCards.objects.all().order_by('word_level') 
    word_cards = WordCards.objects.filter(cardslists__list=word_list).order_by('cardslists__lists_order') 
    cards = CardsLists.objects.filter(list=word_list).count()
    
    # Get the list order for each card
    card_orders = {}
    for card in word_cards:
      try:
        card_order = CardsLists.objects.get(list=word_list, card=card).lists_order
        card_orders[card.pk] = card_order
      except CardsLists.DoesNotExist:
        card_orders[card.pk] = None # Or handle the missing order as needed

    # Serialize the data with the order included
    serializer = WordCardsSerializer(word_cards, many=True)
    data = {
      "word_list_id": word_list.id,
      "status": word_list.status,
      "cards_in_list": cards,
      "cards": [
        {
          "pk": card['pk'],
          "lists_order": card_orders.get(card['pk']),
          "word": card['word'],
          "word_level": card['word_level'],
          "word_language": card['word_language'],
          "word_class": card['word_class'],
          "word_translation": card['word_translation'],
          "word_image": card['word_image']
        } 
        for card in serializer.data
      ]
    }
    return Response(data)


#редактирует заявку
@swagger_auto_schema(method='put', request_body=WordListsSerializer)
@api_view(['PUT'])
@permission_classes([IsManager])
@authentication_classes([Auth_by_Session])
def update_word_list(request, pk, format=None):
    try:
        word_list = WordLists.objects.get(pk=pk)
    except WordLists.DoesNotExist:
        return Response({"error": "Список не найден"}, status=status.HTTP_404_NOT_FOUND)
    # time_to_learn = request.data.get('time_to_learn')
    # if time_to_learn == 'week':
    #   word_list.learn_until_date = (datetime.datetime.now() + datetime.timedelta(weeks=1)).date()
    # elif time_to_learn == 'month':
    #   word_list.learn_until_date = (datetime.datetime.now() + datetime.timedelta(weeks=4)).date()
    # else:
    #   return Response("Incorrect time_to_learn", status=status.HTTP_400_BAD_REQUEST)
    serializer = WordListsSerializer(word_list, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#сформировать отправление
@swagger_auto_schema(method='put', request_body=WordListsSerializer)
@api_view(['PUT'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def form_list(request, pk):
  word_list = get_object_or_404(WordLists, pk=pk, status='draft', creator = request.user.id)
  if word_list is None:
      return Response("No word_list ready for formation", status=status.HTTP_404_NOT_FOUND)

  time_to_learn = request.data.get('time_to_learn')
  if time_to_learn is None or time_to_learn == "":
      return Response("No time_to_learn written", status=status.HTTP_400_BAD_REQUEST)

  word_list.status = 'formed'
  word_list.submition_date = datetime.datetime.now().date()
  if time_to_learn == 'week':
    word_list.learn_until_date = (datetime.datetime.now() + datetime.timedelta(weeks=1)).date()
  elif time_to_learn == 'month':
      word_list.learn_until_date = (datetime.datetime.now() + datetime.timedelta(weeks=4)).date()
  else:
      return Response("Incorrect time_to_learn", status=status.HTTP_400_BAD_REQUEST)
  word_list.save()
  serializer = WordListsSerializer(word_list)
  return Response(serializer.data, status=status.HTTP_200_OK)


#завершить/отклонить модератором
@swagger_auto_schema(method='put', request_body=ResolveWordList)
@api_view(['PUT'])
@permission_classes([IsManager])
@authentication_classes([Auth_by_Session])
def resolve_word_list(request, pk):
    word_list = WordLists.objects.filter(id=pk, status='formed').first()
    resolve_decision = request.data.get('resolve_decision')
    if resolve_decision == 'complete':
       resolve_decision == 'completed'
    else:
       resolve_decision == 'cancelled'
    
    if word_list is None:
      return Response("No word list found", status=status.HTTP_404_NOT_FOUND)
    serializer = ResolveWordList(word_list,data=request.data,partial=True)
    if serializer.is_valid():
      serializer.save()
      word_list = WordLists.objects.get(id=pk)
      word_list.completion_date = datetime.datetime.now().date()
      word_list.moderator = request.user.id
      word_list.status = resolve_decision
      word_list.save()
      serializer = ResolveWordList(word_list)
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response('Failed to resolve the list', status=status.HTTP_400_BAD_REQUEST)


#удалить заявку
@api_view(['DELETE'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def delete_word_list(request, format=None):
    # Получаем все списки слов, соответствующие условиям
    word_lists = WordLists.objects.filter(status='draft', creator=request.user.id)
    
    # Проверяем, есть ли такие списки
    if not word_lists.exists():
        return Response({"error": "Список не найден"}, status=status.HTTP_404_NOT_FOUND)

    # Обновляем статус для каждого списка
    for word_list in word_lists:
        word_list.status = "deleted"
        print(word_list)
        word_list.save()

    return Response('deleted successfully', status=status.HTTP_204_NO_CONTENT)



#заявки
@api_view(['GET'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def get_word_lists(request):
  # Получаем параметры из запроса
  status_filter = request.data.get('status')
  start_date_str = request.data.get('creation_date')
  end_date_str = request.data.get('completion_date')
  # Фильтруем по статусу (кроме "deleted" и "draft")
  
  if not request.user.is_staff:
     word_lists = WordLists.objects.filter(creator = request.user.id)
  else:
     word_lists = WordLists.objects.all()
  

  # Фильтруем по диапазону дат (если заданы)
  if start_date_str and end_date_str:
    try:
      start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
      end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
      word_lists = word_lists.filter(creation_date__range=[start_date, end_date])
    except ValueError:
      return Response({"error": "Неверный формат даты"}, status=status.HTTP_400_BAD_REQUEST)

  # Фильтруем по статусу (если задан)
  if status_filter:
    if status_filter != 'draft' and status_filter != 'deleted':
        word_lists = word_lists.filter(status=status_filter)

  serializer = WordListsSerializer(word_lists, many=True)
  return Response(serializer.data)



# Создание пользователя
# @swagger_auto_schema(method='post', request_body=UserRegisterSerializer)
# @api_view(['POST'])
# def register_user(request):
#   serializer = UserRegisterSerializer(data=request.data)
#   if serializer.is_valid():
#     serializer.save()
#     return Response(serializer.data, status=status.HTTP_201_CREATED)
#   return Response('Creation failed', status=status.HTTP_400_BAD_REQUEST)


# #Вход
# @swagger_auto_schema(method='post', request_body=None)
# @api_view(['POST'])
# def login_user(request):
#     return Response('Login', status=status.HTTP_200_OK)



# #деавторизация
# @swagger_auto_schema(method='post', request_body=None)
# @api_view(['POST'])
# def logout_user(request):
#     return Response('Logout', status=status.HTTP_200_OK)


#Обновление данных пользователя
@swagger_auto_schema(method='put', request_body=UserRegisterSerializer)
@api_view(['PUT'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def update_user(request):
    new_password = request.data.get("password")
    
    if new_password:
        request.user.set_password(new_password)
        request.user.save()  # Не забудьте сохранить изменения
        return Response("Пароль успешно обновлён", status=status.HTTP_200_OK)
    
    return Response("Пароль не указан", status=status.HTTP_400_BAD_REQUEST)
     
    

class UserViewSet(viewsets.ModelViewSet):
    """Класс, описывающий методы работы с пользователями
    Осуществляет связь с таблицей пользователей в базе данных
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]


    def create(self, request):
        """
        Функция регистрации новых пользователей
        Если пользователя c указанным в request email ещё нет, в БД будет добавлен новый пользователь.
        """
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            self.model_class.objects.create_user(email=serializer.data['email'],
                                     password=serializer.data['password'],
                                     is_superuser=serializer.data['is_superuser'],
                                     is_staff=serializer.data['is_staff'])
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes        
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator
    
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
@csrf_exempt
def login_view(request):
    username = request.data.get("email")
    password = request.data.get("password")
    print(username, password)
    user = authenticate(request, email=username, password=password)
    if user is not None:
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)

        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)

        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")


@swagger_auto_schema(method='post',
                     responses={
                         status.HTTP_204_NO_CONTENT: "No content",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                     })
@api_view(['POST'])
@permission_classes([IsAuth])
def logout_view(request):
    session_id = request.COOKIES["session_id"]
    print(session_id)
    if session_storage.exists(session_id):
        session_storage.delete(session_id)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("session_id")
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(status=status.HTTP_403_FORBIDDEN)