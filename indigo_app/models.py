from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from rest_framework.authtoken.models import Token

from indigo_api.models import Country


class EditorManager(models.Manager):
    def get_queryset(self):
        return super(EditorManager, self).get_queryset()\
            .prefetch_related('country')


class Editor(models.Model):
    """ A complement to Django's User model that adds extra
    properties that we need, like a default country.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    country = models.ForeignKey('indigo_api.Country', on_delete=models.SET_NULL, null=True, verbose_name=_("country"))
    accepted_terms = models.BooleanField(_("accepted terms"), default=False)
    permitted_countries = models.ManyToManyField(Country, related_name='editors', help_text=_("Countries the user can work with."), blank=True, verbose_name=_("permitted countries"))
    language = models.CharField(_("language"), max_length=10, blank=False, null=False, default="en-us", help_text=_("Preferred language"))

    objects = EditorManager

    class Meta:
        verbose_name = _("editor")
        verbose_name_plural = _("editors")

    @property
    def country_code(self):
        if self.country:
            return self.country.country_id.lower()
        return None

    @country_code.setter
    def country_code(self, value):
        if value is None:
            self.country = value
        else:
            self.country = Country.objects.get(country_id=value.upper())

    def has_country_permission(self, country):
        return self.user.is_superuser or country in self.permitted_countries.all()

    def api_token(self):
        # TODO: handle many
        return Token.objects.get_or_create(user=self.user)[0]


class Publication(models.Model):
    """ The publications available in the UI. They aren't enforced by the API.
    """
    country = models.ForeignKey('indigo_api.Country', null=False, on_delete=models.CASCADE, verbose_name=_("country"))
    name = models.CharField(_("name"), max_length=512, null=False, blank=False, unique=False, help_text=_("Name of this publication"))

    class Meta:
        ordering = ['name']
        unique_together = (('country', 'name'),)
        verbose_name = _("publication")
        verbose_name_plural = _("publications")

    def __str__(self):
        return str(self.name)


@receiver(post_save, sender=User)
def create_editor(sender, **kwargs):
    # create editor for user objects
    user = kwargs["instance"]
    if not hasattr(user, 'editor') and not kwargs.get('raw'):
        editor = Editor(user=user, language=settings.LANGUAGE_CODE)
        # ensure there is a country
        editor.country = Country.objects.first()
        editor.save()
