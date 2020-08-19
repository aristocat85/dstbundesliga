from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from menus.base import Menu, NavigationNode
from menus.menu_pool import menu_pool

from DSTBundesliga.apps.leagues.config import LEVEL_MAP
from DSTBundesliga.apps.leagues.models import League


class LeaguesMenu(Menu):

    def get_nodes(self, request):
        """
        This method is used to build the menu tree.
        """
        nodes = []
        counter = 1
        nodes.append(NavigationNode("Startseite", "/", counter))
        all_leagues = League.objects.all()
        conferences = {}
        regions = {}

        for level, title in LEVEL_MAP.items():
            conference_id = None

            level_leagues = all_leagues.filter(level=level)

            for conference in level_leagues.values_list("conference", flat=True).distinct().order_by('conference'):
                if conference:
                    conference_node = conferences.get(conference)
                    if not conference_node:
                        counter += 1
                        conference_node = NavigationNode(conference, reverse('conference-detail', kwargs={"level": level, "conference": conference}), counter, attr={'li_class': conference})
                        nodes.append(conference_node)
                        conferences[conference] = conference_node
                    conference_id = conference_node.id

                conference_leagues = level_leagues.filter(conference=conference)

                counter += 1
                kwargs = {"level": level}
                url = reverse('level-detail', kwargs=kwargs)
                if conference:
                    kwargs["conference"] = conference
                    url = reverse('conference-detail', kwargs=kwargs)

                print(title, conference, conference_id)

                league_node = NavigationNode(title, url, counter, parent_id=conference_id, attr={'li_class': conference})
                league_id = league_node.id
                nodes.append(league_node)

                for region in conference_leagues.values_list("region", flat=True).distinct().order_by('region'):
                    if region:
                        print("Region: ", region, conference_node, conference, conference_id)
                        region_node = regions.get(conference, {}).get(region)
                        if not region_node:
                            counter += 1
                            region_node = NavigationNode(region, reverse('region-detail', kwargs={"level": level, "conference": conference, "region": region}), counter, parent_id=league_id, attr={'li_class': conference})
                            #nodes.append(region_node)
                            if not regions.get(conference):
                                regions[conference] = {}
                            regions[conference][region] = region_node

                    counter += 1

        # Stats
        counter += 1
        nodes.append(NavigationNode("Draft", reverse('draft-stats'), counter))

        # My League
        counter += 1
        nodes.append(NavigationNode("Meine Liga", reverse('my-league'), counter, attr={'li_class': 'right border-left'}))

        return nodes


menu_pool.register_menu(LeaguesMenu)
