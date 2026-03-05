from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='user_home'),
    path("chatbot/", views.chatbot_response, name="chatbot_response"),
    # path('login/', views.login_page, name='user_login'),
    path('feedback/', views.feedback, name='feedback'),
    path('register-user/', views.register_user, name='register_user'),
    path('food-recommender/', views.food_recommender_view, name='food_recommender'),
    path('exercise/', views.exercise_recommender, name='exercise_recommender'),
    path('generate_exercise/', views.generate_exercise, name='generate_exercise'),
    path('load_chat/<str:date>/', views.load_chat_by_date, name='load_chat_by_date'),
    path('workout_history/', views.workout_history, name='workout_history'),
    #########################################
    path('chatbot/', views.chatbot_response, name='chatbot'),
    
]