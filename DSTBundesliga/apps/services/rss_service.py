import datetime
import feedparser
import pytz

from dateutil.parser import *

from django.conf import settings

from DSTBundesliga.apps.dstffbl.models import News


def update():
    feed = feedparser.parse(settings.RSS_FEED)

    last_dt = get_last_update_ts()

    for entry in reversed(feed.entries):
        entry_dt = parse(entry.published)
        if entry_dt > last_dt:
            create_news(entry)
            set_last_update_ts(parse(entry.published))


def create_news(entry):
    News.objects.create(
        title=entry.title, content=get_content(entry), image=settings.PODCAST_NEWS_LOGO
    )


def get_last_update_ts():
    try:
        with open(settings.RSS_TIMESTAMP_FILE, "r") as ts_file:
            ts = ts_file.readline().strip()
            dt = parse(ts)
    except Exception as e:
        dt = datetime.datetime.now()
        set_last_update_ts(dt)

    return dt.astimezone(pytz.timezone(settings.TIME_ZONE))


def set_last_update_ts(dt):
    with open(settings.RSS_TIMESTAMP_FILE, "w") as ts_file:
        ts_file.write(str(dt))


def get_content(entry):
    return entry.summary + "<p><a href='{link}'>Hier geht's zur neuen Folge</a>".format(
        link=entry.link
    )
