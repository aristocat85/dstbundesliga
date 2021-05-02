from django.urls import path

from DSTBundesliga.apps.dstffbl import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register')
]
