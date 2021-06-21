import sleeper_wrapper
from django import forms
from django.utils.translation import gettext as _

from DSTBundesliga.apps.dstffbl.models import SeasonUser


class RegisterForm(forms.Form):
    sleeper_username = forms.CharField(max_length=100)
    region = forms.ChoiceField(choices=SeasonUser.REGIONS)
    possible_commish = forms.BooleanField(required=False)

    def clean_sleeper_username(self):
        data = self.cleaned_data
        sleeper_username = data.get('sleeper_username')

        try:
            sleeper_user = sleeper_wrapper.User(sleeper_username)
            sleeper_id = sleeper_user.get_user_id()
        except TypeError:
            raise forms.ValidationError(
                message=_('Dein Sleeper Benutzername scheint falsch zu sein - bitte gib deinen aktuellen Benutzernamen an!'))

        return sleeper_id
