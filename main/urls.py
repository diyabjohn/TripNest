# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('hotel/<int:hotel_id>/', views.hotel_detail, name='hotel_detail'),
    path('hotel/<int:hotel_id>/book/', views.book_hotel, name='book_hotel'), 
    path('search/', views.search_view, name='search'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('map/', views.hotel_map, name='hotel_map'),


]
