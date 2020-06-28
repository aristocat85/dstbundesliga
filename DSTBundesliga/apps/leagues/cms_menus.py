from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from cms.menu_bases import CMSAttachMenu
from menus.base import NavigationNode
from menus.menu_pool import menu_pool

from DSTBundesliga.apps.leagues.models import League


class LeaguesMenu(CMSAttachMenu):
    name = _("League Menu")  # give the menu a name this is required.

    def get_nodes(self, request):
        """
        This method is used to build the menu tree.
        """
        nodes = []
        for league in League.objects.all():
            node = NavigationNode(
                title=league.sleeper_name,
                url=reverse('league-detail', args=(league.sleeper_id,)),
                id=league.id,
            )
            nodes.append(node)
        return nodes


menu_pool.register_menu(LeaguesMenu)
