import json
from django.db import models
# from annoying.fields import JSONField
# from django_extensions.db.fields.json import JSONField
from fle_utils.django_utils import ExtendedModel
from django.core.serializers.json import DjangoJSONEncoder

class JSONField(models.TextField):
    """
    JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly.
    Django snippet #1478

    example:
        class Page(models.Model):
            data = JSONField(blank=True, null=True)


        page = Page.objects.get(pk=5)
        page.data = {'title': 'test', 'type': 3}
        page.save()
    """

    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if value == "":
            return None

        try:
            if isinstance(value, basestring):
                return json.loads(value)
        except ValueError:
            pass
        return value

    def get_db_prep_save(self, value, *args, **kwargs):
        if value == "":
            return None
        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)
        return super(JSONField, self).get_db_prep_save(value, *args, **kwargs)


class FlexModel(ExtendedModel):

    class Meta:
        abstract = True

    extra_fields = JSONField()
    serialized = models.TextField(blank=True)

    _unserialized_fields = ["extra_fields", "serialized"]
    _model_identifier = None

    def __init__(self, *args, **kwargs):

        # Check that all needed settings were specified
        assert self._model_identifier, "You must specify a unique identifier (name) for this model class"

        # calculate and remember field names, for later efficiency
        # TODO(jamalex): this should probably be moved into a metaclass
        self._meta.field_names = set([f.name for f in self._meta.fields if f.name not in self._unserialized_fields])

        # put kwargs that do not correspond to fields into "extra_fields"
        extra_fields = {}
        for kwarg in kwargs.keys():
            if kwarg not in self._meta.field_names:
                extra_fields[kwarg] = kwargs.pop(kwarg)

        super(FlexModel, self).__init__(*args, **kwargs)

        self.extra_fields = extra_fields

    def to_dict(self):
        data = dict([(key, getattr(self, key)) for key in self._meta.field_names])

        # Mix the extra_fields into the top-level structure
        data.update(self.extra_fields)

        return data

    def get_serialized(self):
        if not self.serialized:
            self.serialized = json.dumps({
                "model": self._model_identifier,
                "data": self.to_json(),
            })
            # self.save()
        return self.serialized

    def to_json(self):
        return json.dumps(self.to_dict())
