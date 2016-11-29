from django.contrib.postgres.fields import JSONField
from django.db import IntegrityError, models, transaction
from datasets.general import events

class EventLogMixin(models.Model):
    ref_model = None  # This must be overwritten

    EVENT_TYPES = (
        ('C', 'CREATE'),
        ('U', 'UPDATE'),
        ('D', 'DELETE'),
    )

    guid = models.CharField(max_length=255)
    sequence = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)  # This makes the field un-editable.
    event_type = models.CharField(max_length=1, choices=EVENT_TYPES)
    data = JSONField()

    def save(self, *args, **kwargs):
        # Making sure that Saving event and model is atomic
        success = False
        try:
            with transaction.atomic():
                # Saving the event
                super(EventLogMixin, self).save(args, kwargs)
                # Updating the Read optimized model
                success = events.handle_event(self, self.ref_model)
                print('Transaction succesful')
        except IntegrityError:
            pass

        return success

    class Meta(object):
        abstract = True
        unique_together = ['guid', 'sequence']