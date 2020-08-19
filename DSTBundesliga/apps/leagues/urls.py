from django.urls import path

from DSTBundesliga.apps.leagues import views

urlpatterns = [
    path('', views.LeagueView.as_view(), name='league-list'),
    path('<int:league_id>/', views.roster_list, name='league-detail'),
    path('level/<int:level>/', views.level_detail, name='level-detail'),
    path('level/<int:level>/<str:conference>/', views.level_detail, name='conference-detail'),
    path('level/<int:level>/<str:conference>/<str:region>/', views.level_detail, name='region-detail'),
    path('my-league/', views.my_league, name='my-league'),
    path('stats/draft/', views.draft_stats, name='draft-stats'),
    path('stats/draft/<str:position>/', views.draft_stats, name='draft-stats'),
]
