from django.urls import path

from DSTBundesliga.apps.dstffbl import views

urlpatterns = [
    path('', views.home, name='home'),
    path('anmeldung/', views.register, name='anmeldung'),
    path('early-bird/', views.early_bird, name='early-bird'),
    path('accept_invite/<str:registration_id>/', views.confirm_registration, name='accept_invite'),
    path('login/', views.login, name='login')
]
