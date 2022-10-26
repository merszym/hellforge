from django.db.models.signals import post_save
from django.dispatch import receiver
from main.models import Layer, Culture, Epoch, Checkpoint
import statistics

@receiver(post_save, sender=Layer)
@receiver(post_save, sender=Culture)
@receiver(post_save, sender=Epoch)
@receiver(post_save, sender=Checkpoint)
def calculate_mean_datings(sender, instance, **kwargs):
    if instance.date.first():
        mean_lower = statistics.mean([x.lower for x in instance.date.all()])
        mean_upper = statistics.mean([x.upper for x in instance.date.all()])
        # since saving causes the signal to fire again, dont save if no update
        # causes the signals to run twice, I know, but thats for now the best to
        # reduce repetitive code
        if instance.mean_lower == mean_lower and instance.mean_upper == mean_upper:
            pass
        else:
            instance.mean_lower = mean_lower
            instance.mean_upper = mean_upper
            instance.save()