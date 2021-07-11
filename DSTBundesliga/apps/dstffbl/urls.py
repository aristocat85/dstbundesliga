from django.urls import path

from DSTBundesliga.apps.dstffbl import views

urlpatterns = [
    path('', views.home, name='home'),
    path('anmeldung/', views.register, name='anmeldung'),
    path('login/', views.login, name='login')
]
