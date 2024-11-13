from django.contrib import admin
from app import views
from django.urls import include, path
from rest_framework import routers
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path(r'word_cards', views.get_word_cards, name='wordcards-list'),
    path(r'word_card/<int:pk>', views.get_word_card_info, name='wordcards-detail'),
    path(r'word_card/add', views.add_word_card, name='add-word-card'),
    path(r'word_card/<int:pk>/change', views.update_card_info, name='update_word_card'),
    path(r'word_card/<int:pk>/delete', views.delete_card, name='delete_word_card'),
    path(r'word_card/<int:pk>/add_img', views.add_card_img, name='add_card_img'),
    path(r'word_card/<int:pk>/add_to_list', views.add_to_list, name='add_to_list'),
    path('word_card/<int:ck>/<int:lk>/delete', views.delete_from_list, name='delete_from_list'), 
    path('word_card/<int:ck>/<int:lk>/change', views.change_card_in_list, name='change_from_list'),
    path(r'word_lists', views.get_word_lists, name='wordlists-list'),
    path(r'word_list/<int:pk>', views.get_word_list_info, name='wordlist-detail'),
    path(r'word_list/<int:pk>/change', views.update_word_list, name='update-word-list'), 
    path(r'word_list/delete', views.delete_word_list, name='delete-word-list'), 
    path(r'word_list/<int:pk>/form', views.form_list, name='form-list'), 
    path(r'word_list/<int:pk>/resolve', views.resolve_word_list, name='resolve-form-list'),
   #  path(r'register', views.register_user, name='register-user'),
   #  path(r'login', views.login_user, name='login-user'),
   #  path(r'logout', views.logout_user, name='logout-user'),
    path(r'user/change', views.update_user, name='update-user'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('login/',  views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('admin/', admin.site.urls)
]

