from django.urls import path

from . import views


urlpatterns = [
    path('', views.public_registration, name='public_registration'),
    path('submitted/', views.public_success, name='public_success'),
    path('temple/login/', views.login_view, name='temple_login'),
    path('temple/logout/', views.logout_view, name='temple_logout'),
    path('temple/', views.temple_dashboard, name='temple_dashboard'),
    path('temple/devotees/', views.devotee_list, name='devotee_list'),
    path('temple/devotees/<int:pk>/', views.devotee_detail, name='devotee_detail'),
    path('temple/allocate/', views.allocate_seva, name='allocate_seva'),
    path('temple/unallocate/', views.unallocate_seva, name='unallocate_seva'),
    path('temple/special-dates/', views.special_seva_dates, name='special_seva_dates'),
    path('temple/seva/new/', views.seva_event_new, name='seva_event_new'),
    path('temple/users/', views.temple_user_list, name='temple_user_list'),
]
