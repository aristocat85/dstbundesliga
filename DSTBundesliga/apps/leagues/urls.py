from django.urls import path

from DSTBundesliga.apps.leagues import views

urlpatterns = [
    path('', views.LeagueView.as_view(), name='league-list'),
    path('<int:league_id>/', views.roster_list, name='league-detail')
]
