from django.contrib.auth import logout
from django.db.models import Max
from django.shortcuts import render, redirect
from django.urls import reverse

from DSTBundesliga.apps.dstffbl.forms import RegisterForm
from DSTBundesliga.apps.dstffbl.models import SeasonUser, News
from DSTBundesliga.apps.leagues.models import Matchup, Season, DSTPlayer
from DSTBundesliga.apps.services.awards_service import AwardService


def home(request):
    week = Matchup.objects.all().aggregate(Max('week')).get('week__max')
    awards_service = AwardService(week)
    awards = awards_service.get_random(4)
    news = News.objects.all().order_by('-date')[:3]

    return render(request, "dstffbl/home.html", {
        "news_list": news,
        "awards": awards
    })


def register(request):
    user = request.user

    if user.is_authenticated:
        if request.method == 'POST':
            form = RegisterForm(request.POST)

            if form.is_valid():
                season_user, created = SeasonUser.objects.get_or_create(
                    user=user,
                    season=Season.get_active(),
                    defaults={
                        'sleeper_id': form.cleaned_data.get('sleeper_username'),
                        'region': form.cleaned_data.get('region'),
                        'new_player': DSTPlayer.objects.filter(sleeper_id=form.cleaned_data.get('sleeper_username')).count() > 0
                    }
                )

        if request.method == 'GET':
            try:
                season_user = SeasonUser.objects.get(user=user)
            except SeasonUser.DoesNotExist as e:
                season_user = None

            form = RegisterForm()

        return render(request, 'dstffbl/register.html', {'form': form, 'region_choices': SeasonUser.REGIONS, 'current_season': Season.get_active(), 'season_user': season_user})

    else:
        return render(request, 'dstffbl/login.html', {'next': '/register/'})
