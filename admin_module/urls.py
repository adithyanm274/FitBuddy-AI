from django.urls import path
from . import views

urlpatterns = [
      path('', views.homepage, name='admin_homepage'),
    path('feedbacks/', views.admin_feedback_list, name='admin_feedback_list'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('delete-feedback/<int:feedback_id>/', views.delete_feedback, name='delete_feedback'),

]
