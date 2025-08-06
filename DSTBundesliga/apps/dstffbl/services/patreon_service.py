import csv
import re
import patreon
import time

from django.conf import settings

from DSTBundesliga.apps.dstffbl.models import (
    Patron
)


def read_patreon_file(filepath=None):
    with open(filepath) as csv_file:
        dialect = csv.Sniffer().sniff(csv_file.readline())
        csv_file.seek(0)
        patreon_reader = csv.DictReader(csv_file, dialect=dialect)

        return [row for row in patreon_reader]


def read_ffbl_file(filepath=None):
    with open(filepath) as csv_file:
        csv_file.readline()
        ffbl_data = csv_file.readlines()

        return [row.strip().upper() for row in ffbl_data]


def get_names(patreon_data):
    return [row.get("Name").strip().upper() for row in patreon_data]


def get_emails(patreon_data):
    return [row.get("Email").strip().upper() for row in patreon_data]


def get_discord(patreon_data):
    return [
        row.get("Discord").split("#")[0].strip().upper()
        for row in patreon_data
        if "#" in row.get("Discord")
    ]


def find_missing_users(patreon_filepath, ffbl_filepath):
    patreon_data = read_patreon_file(patreon_filepath)
    names = get_names(patreon_data)
    emails = get_emails(patreon_data)
    discord_names = get_discord(patreon_data)

    names_to_find = read_ffbl_file(ffbl_filepath)

    no_direct_hit = []

    for name in names_to_find:
        if name in names:
            names.remove(name)
        elif name in emails:
            emails.remove(name)
        else:
            no_direct_hit.append(name)

    second_run_names = [name.replace(" ", "") for name in names]
    no_second_run_hit = []

    for name in no_direct_hit:
        stripped_name = re.sub(r"\([^)]*\)", "", name).replace(" ", "").strip()
        stripped_email = stripped_name
        if "(" in name and ")" in name:
            stripped_email = name[name.find("(") + 1 : name.find(")")]

        if stripped_name in second_run_names:
            second_run_names.remove(stripped_name)
        elif stripped_email in emails:
            emails.remove(stripped_email)
        elif stripped_name in discord_names:
            discord_names.remove(stripped_name)
        else:
            no_second_run_hit.append(name)

    no_last_run_hit = [name for name in no_second_run_hit if name != ""]

    for patreon_name in second_run_names:
        if patreon_name == "":
            continue
        for name in no_last_run_hit:
            if patreon_name in name or name in patreon_name:
                if name == "N0LSKI":
                    return patreon_name, patreon_name, patreon_name, patreon_name
                    print("NAME:", name, "PAT_NAME:", patreon_name)
                no_last_run_hit.remove(name)

    for patreon_email in emails:
        if patreon_email == "":
            continue
        for name in no_last_run_hit:
            if patreon_email in name or name in patreon_email:
                if name == "N0LSKI":
                    print("name:", name, "pat_mail:", patreon_email)
                no_last_run_hit.remove(name)

    found = set(names_to_find) - set(no_direct_hit)
    likely_found = set(no_direct_hit) - set(no_second_run_hit)
    maybe_found = set(no_second_run_hit) - set(no_last_run_hit)
    not_found = no_last_run_hit

    with open("local/maybe_found.txt", "w") as file:
        for name in maybe_found:
            file.write(name + "\n")

    with open("local/not_found.txt", "w") as file:
        for name in not_found:
            file.write(name + "\n")

    return list(found), list(likely_found), list(maybe_found), not_found


def check_patreon_status(user):
    return len(set([sa.uid for sa in user.socialaccount_set.all()]) & set(list(Patron.objects.all().values_list("pledge_id", flat=True)))) > 0


def update_patrons():
    print("Updating Patrons")
    api_client = patreon.API(settings.PATREON_TOKEN)

    campaign_response = api_client.fetch_campaign()
    campaign_id = campaign_response.data()[0].id()

    pledges = []
    cursor = None
    retries = 10
    while True:
        if retries == 0:
            break
        try:
            pledges_response = api_client.fetch_page_of_pledges(campaign_id, page_size=1000, cursor=cursor)
            pledges += pledges_response.data()
            time.sleep(1)
            cursor = api_client.extract_cursor(pledges_response)
            print(len(pledges), cursor)
        except:
            retries -= 1
            print("An error occured. ", retries, " retries left.")
        if not cursor:
            break

    print("Found ", len(pledges), " Patrons!")
    print("Updating Database")

    Patron.objects.all().delete()

    for pledge in pledges:
        Patron.objects.update_or_create(pledge_id=pledge.relationship("patron").id())
