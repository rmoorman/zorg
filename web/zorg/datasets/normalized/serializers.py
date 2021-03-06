# Packages
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
# Projects
from . import models
from datasets.general import events


class ZorgModelSerializer(serializers.ModelSerializer):

    event_model = None

    def get_extra_kwargs(self):
        # On create guid should be empty
        extra_kwargs = super(ZorgModelSerializer, self).get_extra_kwargs()
        action = self.context['view'].action
        if action == 'create':
            kwargs = extra_kwargs.get('guid', {})
            kwargs['required'] = False
            extra_kwargs['guid'] = kwargs
        return extra_kwargs

    def create(self, validated_data):
        # Creating the guid
        guid = events.guid_from_id(self.context['request'].user, validated_data['id'])
        # If a guid is given, remove it from the data
        if 'guid' in validated_data:
            del(validated_data['guid'])
        # There can bew two cases in which create can be made:
        # 1. There is no previous entry
        # 2. The laatste event was een delete
        prev_events = list(self.event_model.objects.filter(guid=guid).order_by('sequence'))
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
        extra_kwargs = {'client': {'required': 'False'}}


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
