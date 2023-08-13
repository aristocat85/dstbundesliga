import logging
from urllib.parse import urlencode

from django.db.models import Max
from django.shortcuts import render, redirect

import sleeper_wrapper
from django.urls import reverse

from DSTBundesliga.apps.dstffbl.forms import RegisterForm, ProfileForm
from DSTBundesliga.apps.dstffbl.models import (
    SeasonUser,
    News,
    SeasonRegistration,
    DSTEmail,
    REGIONS,
)
from DSTBundesliga.apps.dstffbl.services import season_service
from DSTBundesliga.apps.leagues.models import Matchup, Season, DSTPlayer, League
from DSTBundesliga.apps.services.awards_service import AwardService
from DSTBundesliga.apps.services.season_service import is_registration_open


def home(request):
    week = (
        Matchup.objects.filter(
            season=Season.get_active(),
            league_id__in=League.objects.filter(type=League.BUNDESLIGA).values_list(
                "sleeper_id"
            ),
        )
        .aggregate(Max("week"))
        .get("week__max")
    )
    awards_service = AwardService(request, week)
    awards = awards_service.get_random(0)
    news = News.objects.all().order_by("-date")[:3]

    return render(request, "dstffbl/home.html", {"news_list": news, "awards": awards})


def register(request, early_bird=False):
    user = request.user
    season_registration = None
    season_user = None
    form = None

    if user.is_authenticated:
        if request.method == "POST":
            form = RegisterForm(request.POST)

            if form.is_valid():
                sleeper_id = form.cleaned_data.get("sleeper_username")
                dst_player = None
                last_years_league = None

                try:
                    dst_player = DSTPlayer.objects.get(
                        sleeper_id=form.cleaned_data.get("sleeper_username")
                    )
                    if dst_player:
                        last_years_league = season_service.get_last_years_league(
                            player=dst_player
                        )
                except:
                    pass

                season_registration, created = SeasonRegistration.objects.get_or_create(
                    user=user,
                    season=Season.get_active(),
                    defaults={
                        "sleeper_id": sleeper_id,
                        "region": form.cleaned_data.get("region"),
                        "new_player": dst_player is None,
                        "last_years_league": last_years_league,
                        "possible_commish": form.cleaned_data.get("possible_commish"),
                    },
                )

                sleeper_user = sleeper_wrapper.User(sleeper_id)
                sleeper_username = sleeper_user.get_username()
                dst_player, _ = DSTPlayer.objects.update_or_create(
                    sleeper_id=sleeper_id, defaults={"display_name": sleeper_username}
                )

                season_registration.dst_player = dst_player
                season_registration.save()
                if created:
                    season_registration.create_mail()

        elif request.method == "GET":
            try:
                season_registration = SeasonRegistration.objects.get(
                    user=user, season=Season.get_active()
                )
                season_user = SeasonUser.objects.get(
                    user=user, season=Season.get_active()
                )
            except SeasonRegistration.DoesNotExist as e:
                season_registration = None
            except SeasonUser.DoesNotExist as e:
                season_user = None
            if not form:
                form = RegisterForm()

        if is_registration_open() or early_bird:
            if season_registration and not season_user:
                return render(request, "dstffbl/registration_success.html")
            else:
                return render(
                    request,
                    "dstffbl/register.html",
                    {
                        "form": form,
                        "region_choices": REGIONS,
                        "current_season": Season.get_active(),
                        "season_user": season_user,
                    },
                )
        else:
            return render(request, "dstffbl/waiting_for_register.html")

    else:
        login_url = reverse("dstffbl:login")
        return redirect("{}?{}".format(login_url, urlencode({"next": "/anmeldung/"})))


def early_bird(request):
    return register(request, early_bird=True)


def confirm_registration(request, registration_id):
    EMAIL_SUBJECT = "Anmeldung erfolgreich!"

    EMAIL_TEXT = """'
    Hallo {sleeper_name},
    
    Du bist für die Saison {current_season} angemeldet! Weitere Infos folgen in einigen Tagen per Mail und über unsere 
    Social Media Seiten.
    
    Beste Grüße von
    Michael und dem gesamten Organisationsteam der DSTFanFooBL
    """

    EMAIL_HTML = """
    <p>Hallo {sleeper_name},</p>
    
    <p>Du bist für die Saison {current_season} angemeldet! Weitere Infos folgen in einigen Tagen per Mail und über 
    unsere Social Media Seiten.</p>
    
    <p>Beste Grüße von<br>
    Michael und dem gesamten Organisationsteam der DSTFanFooBL</p>
    """

    try:
        registration = SeasonRegistration.objects.filter(
            season=Season.get_active()
        ).get(id=registration_id)

        season_user, created = SeasonUser.objects.get_or_create(
            user=registration.user,
            registration=registration,
            dst_player=registration.dst_player,
            season=registration.season,
            sleeper_id=registration.sleeper_id,
            region=registration.region,
            new_player=registration.new_player,
            last_years_league=registration.last_years_league,
            possible_commish=registration.possible_commish,
        )

        DSTEmail.objects.create(
            recipient=registration.user.email,
            subject=EMAIL_SUBJECT,
            text=EMAIL_TEXT.format(
                sleeper_name=registration.dst_player.display_name,
                current_season=registration.season,
            ),
            html=EMAIL_HTML.format(
                sleeper_name=registration.dst_player.display_name,
                current_season=registration.season,
            ),
            type=2,
        )

        return render(
            request,
            "dstffbl/register.html",
            {"current_season": Season.get_active(), "season_user": season_user},
        )

    except SeasonRegistration.DoesNotExist as e:
        logging.error(f"Registration with id {registration_id} not found.", e)
        return render(
            request,
            "dstffbl/confirmation_error.html",
            {
                "confirmation_error": "Es tut uns leid, deine Registierung ist nicht mehr gültig. Bitte melde dich erneut an."
            },
        )


def login(request):
    next = request.GET.get("next", "/")

    if request.user.is_authenticated:
        return redirect(next)

    return render(request, "dstffbl/login.html", {"next": next})


def profile(request):
    user = request.user
    season = Season.get_active()

    season_user = None
    season_registration = None
    message = ""
    season_data = None
    registration_open = is_registration_open()

    try:
        season_user = SeasonUser.objects.get(user=user, season=season)
        season_data = season_user
        registration_status = "confirmed"
    except SeasonUser.DoesNotExist:
        try:
            season_registration = SeasonRegistration.objects.get(
                user=user, season=Season.get_active()
            )
            season_data = season_registration
            registration_status = "pending"
        except SeasonRegistration.DoesNotExist:
            registration_status = "not_registered"

    if request.method == "POST":
        form = ProfileForm(request.POST)

        if form.is_valid():
            submitted_sleeper_id = form.cleaned_data.get("sleeper_username")
            sleeper_user = sleeper_wrapper.User(submitted_sleeper_id)
            sleeper_id = sleeper_user.get_user_id()
            sleeper_username = sleeper_user.get_username()
            dst_player, _ = DSTPlayer.objects.update_or_create(
                sleeper_id=sleeper_id, defaults={"display_name": sleeper_username}
            )

            season_data.sleeper_id = sleeper_id
            season_data.dst_player.display_name = sleeper_username

            season_data.user.email = form.cleaned_data.get("email")
            season_data.region = form.cleaned_data.get("region")
            season_data.possible_commish = form.cleaned_data.get("possible_commish")
            season_data.save()
            season_data.user.save()
            season_data.dst_player.save()

            message = "Deine Daten wurden erfolgreich gespeichert!"

    else:
        if season_data:
            form = ProfileForm(
                data={
                    "sleeper_username": season_data.dst_player.display_name,
                    "email": season_data.user.email,
                    "possible_commish": season_data.possible_commish,
                    "region": season_data.region,
                }
            )
        else:
            form = ProfileForm()

    return render(
        request,
        "dstffbl/profile.html",
        {
            "season": season,
            "season_data": season_data,
            "registration_status": registration_status,
            "registration_open": registration_open,
            "region_choices": REGIONS,
            "form": form,
            "message": message,
            "resend_url": reverse("dstffbl:resend_invite"),
            "register_url": reverse("dstffbl:anmeldung"),
        },
    )


def resend_invite(request):
    try:
        season_registration = SeasonRegistration.objects.get(
            user=request.user, season=Season.get_active()
        )
        season_registration.create_mail()
    except SeasonRegistration.DoesNotExist:
        pass

    return render(request, "dstffbl/registration_success.html")
