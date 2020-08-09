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
        for level, title in LEVEL_MAP.items():
            counter += 1
            level_node = NavigationNode(title, reverse('level-detail', kwargs={"level": level}), counter)
            nodes.append(level_node)

            for region in League.objects.filter(level=level).values_list("region", flat=True).distinct().order_by('region'):
                if region:
                    counter += 1
                    nodes.append(NavigationNode(region, reverse('region-detail', kwargs={"level": level, "region": region}), counter, parent_id=level_node.id))

        # Stats
        counter += 1
        nodes.append(NavigationNode("Draft", reverse('draft-stats'), counter))

        # My League
        counter += 1
        nodes.append(NavigationNode("Meine Liga", reverse('my-league'), counter, attr={'li_class': 'right border-left'}))

        return nodes


menu_pool.register_menu(LeaguesMenu)
