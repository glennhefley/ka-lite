import json

from django.db import models
from django.db.models.base import ModelBase
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from fle_utils.django_utils import ExtendedModel

from .fields import JSONField
from .sync import register_syncing_model

""" TODO
    - clear "serialized" field when changing other fields (to mark "dirty" and force reserialization)
    - Handle the case of two zombie models from other devices with same ID needing to be merged.
"""

class FlexModelMetaclass(ModelBase):
    """
    This class does the following:
        * adds a signal listener to prevent any deletes from ever happening
        * adds subclasses of FlexModel to the set of syncing models
    """

    def __init__(cls, name, bases, clsdict):

        # TODO(jamalex): do we need this conditional?
        if len(cls.mro()) > 4 and not cls._meta.abstract:

            # Add the deletion signal listener.
            if not hasattr(cls, "_do_not_delete_signal"):
                @receiver(pre_delete, sender=cls)
                def disallow_delete(sender, instance, **kwargs):
                    if not getattr(settings, "DEBUG_ALLOW_DELETIONS", False):
                        raise NotImplementedError("Objects of FlexModel subclasses (like %s) cannot be deleted." % instance.__class__)
                cls._do_not_delete_signal = disallow_delete  # don't let Python destroy this fn on __init__ completion.

            # Add subclass to set of syncing models.
            register_syncing_model(cls)

        super(FlexModelMetaclass, cls).__init__(name, bases, clsdict)


class FlexModel(ExtendedModel):

    __metaclass__ = FlexModelMetaclass

    class Meta:
        abstract = True

    extra_fields = JSONField()
    serialized = models.TextField(blank=True)

    _unserialized_fields = ["extra_fields", "serialized"]
    _model_identifier = None

    @classmethod
    def deserialize(cls, serialized_model):
        return clas(**json.loads(serialized_model))

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

    def get_model_identifier(self):
        return self._model_identifier

    def get_serialized(self):
        # if not already serialized since last modification, serialize now
        if not self.serialized:
            # if the model is new, we need to save first to get an ID
            if not self.id:
                self.save()
            # serialize to JSON and store in "serialized" field
            self.serialized = json.dumps({
                "model": self.get_model_identifier(),
                "data": self.to_json(),
            })
            self.save()
        return self.serialized

    def __setattr__(self, attrname, attrval):
        # if we're changing a field, clear the serialized field as well
        if (attrname in self._meta.field_names) and (attrname != "serialized"):
            self.serialized = ""
        super(FlexModel, self).__setattr__(attrname, attrval)

    def to_json(self):
        return json.dumps(self.to_dict())



def ZombieModel(FlexModel):
    """A ZombieModel is used to store records that could not be imported into
    a specific subclass of FlexModel (either because it didn't exist, or there
    was an error). We remember the original model_identifier so we can
    re-serialize the model properly later.
    """

    _unserialized_fields = FlexModel._unserialized_fields + ["model_identifier", "error"]
    _model_identifier = "zombie"

    model_identifier = models.CharField(max_length=100)
    error = models.TextField()

    def get_model_identifier(self):
        return self.model_identifier
