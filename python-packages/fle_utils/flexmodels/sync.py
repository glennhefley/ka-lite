from django.db.models import get_model
from django.db.models.fields.related import ForeignKey


_syncing_models = [] # all models we want to sync
_syncing_model_names = [] # same as _syncing_models but as strings (appname.modelname)
_syncing_model_dependencies = [] # holds dependency lists for models in _syncing_models
_syncing_model_dict = {} # syncing models by _model_identifier


def get_foreign_key_classes(m):
    fkeys = []
    for field in m._meta.fields:
        if isinstance(field, ForeignKey):
            fkeys.append(get_model_name(field.rel.to, m._meta.app_label))
    return set(fkeys)


def get_model_name(model, app_label=""):
    if isinstance(model, basestring):
        if "." not in model:
            model = "%s.%s" % (app_label, model)
    else:
        app_label = model._meta.app_label
        object_name = model._meta.object_name
        model = "%s.%s" % (app_label, object_name)
    return model


def register_syncing_model(model):
    """When sync is run, these models will be sync'd"""

    if model in _syncing_models:
        logging.debug("We are already syncing model %s; likely from different ways of importing the same models file." % unicode(model))
        return

    model_name = get_model_name(model)

    # Add the model to the lookup dict
    if model._model_identifier:
        _syncing_model_dict[model._model_identifier] = model

    # When we add models to be synced, we need to make sure
    #   that models that depend on other models are synced AFTER
    #   the model it depends on has been synced.

    # Get the dependencies of the new model
    foreign_key_classes = get_foreign_key_classes(model)

    # Find all the existing models that this new model refers to.
    class_indices = [_syncing_model_names.index(cls) for cls in foreign_key_classes if get_model_name(cls) in _syncing_model_names]

    # Insert just after the last dependency found,
    #   or at the front if no dependencies
    insert_after_idx = (1 + max(class_indices)) if class_indices else 0

    # Before inserting, make sure that any models referencing *THIS* model
    # appear after this model.
    for dependencies in _syncing_model_dependencies[0:insert_after_idx]:
        if model_name in dependencies:
            raise Exception("Dependency loop detected in syncing models; cannot proceed.")

    # Now we're ready to insert.
    _syncing_models.insert(insert_after_idx, model)
    _syncing_model_names.insert(insert_after_idx, model_name)
    _syncing_model_dependencies.insert(insert_after_idx, foreign_key_classes)


def get_serialized_models():
    serialized_models = []
    for Model in _syncing_models:
        serialized_models += [model.get_serialized() for model in Model.objects.all()]
    return serialized_models


def deserialize_models(serialized_models):
    models = []
    for model in serialized_models:
        if model["model"] in _syncing_model_dict:
            Model = _syncing_model_dict[model["model"]]
        else:
            Model = _syncing_model_dict["zombie"]
        models.append(Model.deserialize(model["data"]))
    return models
