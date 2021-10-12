from django.urls import path

from DSTBundesliga.apps.leagues import views

urlpatterns = [
    path('', views.LeagueView.as_view(), name='league-list'),
    path('<int:league_id>/', views.roster_list, name='league-detail'),
    path('lev/<int:level>/', views.level_detail, name='level-detail'),
    path('conf/<str:conference>/', views.level_detail, name='conference-overview'),
    path('conf/<str:conference>/lev/<int:level>/', views.level_detail, name='conference-detail'),
    path('conf/<str:conference>/lev/<int:level>/reg/<str:region>/', views.level_detail, name='region-detail'),
    path('my-league/', views.my_league, name='my-league'),
    path('dst-league/', views.listener_league, name='dst-league'),
    path('champions-league/', views.champions_league, name='champions-league'),
    path('stats/draft/', views.draft_stats, name='draft-stats'),
    path('stats/draft/<str:position>/', views.draft_stats, name='draft-stats'),
    path('stats/players/', views.player_stats, name='player-stats'),
    path('stats/players/<str:position>/', views.player_stats, name='player-stats'),
    path('stats/draftboard/<str:league_id>/', views.draftboard, name='draft-board'),
    path('stats/facts_and_figures/<str:league_id>/', views.facts_and_figures_for_league, name='facts_and_figures_league'),
    path('stats/cl_quali/', views.cl_quali, name='cl-quali'),
    path('stats/some_quali/', views.some_quali, name='some-quali'),
    path('stats/facts_and_figures/', views.facts_and_figures, name='facts_and_figures'),
    path('stats/waiver/', views.waiver_stats, name='waiver_stats'),
    path('playoffs/<str:league_id>/', views.playoffs, name='playoffs')
]
