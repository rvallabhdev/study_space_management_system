# study_space_management/signals.py

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import StudySpace, TimeSlot

@receiver(pre_save, sender=StudySpace)
def deactivate_time_slots_on_space_deactivation(sender, instance, **kwargs):
    """
    If a study space is being set to inactive, deactivate all its time slots.
    """
    if instance.pk:
        try:
            old = StudySpace.objects.get(pk=instance.pk)
            if old.is_active and not instance.is_active:
                # Space is being deactivated → deactivate its slots
                TimeSlot.objects.filter(study_space=instance).update(is_active=False)
        except StudySpace.DoesNotExist:
            pass