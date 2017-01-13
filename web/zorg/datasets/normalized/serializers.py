# Packages
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
# Projects
from . import models
from datasets.general import events


class ZorgModelSerializer(serializers.ModelSerializer):

    event_model = None

    def __init__(self, *args, **kwargs):
        print(args, kwargs)
        super(ZorgModelSerializer, self).__init__(*args, **kwargs)

    def validate_guid(self, value):
        print(value)
        return value

    def create(self, validated_data):
        print(validated_data)
        # Creating the guid
        guid = events.guid_from_id('CODE', validated_data['id'])

        # There can bew two cases in which create can be made:
        # 1. There is no previous entry
        # 2. The laatste event was een delete
        prev_events = list(self.event_model.objects.filter(
                      guid=guid).order_by('sequence'))
        if len(prev_events) == 0:
            sequence = 0
        elif prev_events[-1].event_type == 'D':
            sequence = prev_events[-1].sequence + 1
        else:
            # Does not match creation rule
            # @TODO convert to self.fail call
            raise ValidationError('Object already exists')

        event = self.event_model(
            guid=guid,
            sequence=sequence,
            event_type='C',
            data=validated_data
        )
        new_item = event.save()
        return new_item

    def update(self, instance, validated_data):
        # Creating the guid
        guid = instance.guid

        # There can bew two cases in which create can be made:
        # 1. There is no previous entry
        # 2. The laatste event was een delete
        prev_events = list(self.event_model.objects.filter(
                      guid=guid).order_by('sequence'))
        if len(prev_events) == 0 or prev_events[-1].event_type == 'D':
            # @TODO convert to self.fail call
            raise ValidationError('Object not found')
        else:
            sequence = prev_events[-1].sequence + 1

        event = self.event_model(
            guid=guid,
            sequence=sequence,
            event_type='U',
            data=validated_data
        )
        item = event.save()
        return item


class OrganisatieSerializer(ZorgModelSerializer):

    event_model = models.OrganisatieEventLog

    class Meta(object):
        fields = '__all__'
        model = models.Organisatie


class LocatieSerializer(ZorgModelSerializer):

    event_model = models.LocatieEventLog

    class Meta(object):
        fields = '__all__'
        model = models.Locatie


class ActiviteitSerializer(ZorgModelSerializer):

    event_model = models.ActiviteitEventLog

    class Meta(object):
        fields = '__all__'
        model = models.Activiteit
