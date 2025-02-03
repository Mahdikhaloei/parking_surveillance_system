from django.db import models
from django.utils.translation import gettext_lazy as _

from backend.utils.mixins.models import Timestampable


class CameraModel(Timestampable, models.Model):
    ip_address = models.CharField(max_length=255, verbose_name=_("IP Address"))
    tripwire = models.CharField(max_length=255, verbose_name=_("Tripwire"), unique=True)
    channel = models.SmallIntegerField(verbose_name=_("Channel"))

    def __str__(self):
        return f"Camera {self.id} - {self.tripwire}"

    class Meta:
        verbose_name = _("Camera")
        verbose_name_plural = _("Cameras")


class EventModel(Timestampable, models.Model):
    camera = models.ForeignKey(CameraModel, on_delete=models.CASCADE, related_name="events", verbose_name=_("Camera"))
    title = models.CharField(max_length=255, verbose_name=_("Event Title"), blank=True)
    info = models.TextField(verbose_name=_("Event Info"), blank=True)
    snapshot = models.ImageField(upload_to="parkings/events", verbose_name=_("Snapshot"), blank=True)

    def __str__(self):
        return f"Event {self.id} - {self.title}"

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")