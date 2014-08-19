import json

from django.test import TestCase

from kalite.dynamic_assets import models


class DynamicSettingsModelsTests(TestCase):

    def test_can_define_new_dynamic_setting_instance(self):

        models.DynamicSettings(
            namespace='test',
            schema={
                'test_intsetting': models.IntField,
                'test_boolsetting': models.BoolField,
                'test_strsetting': models.StrField,
            })

    def test_can_call_dynamic_settings_without_arguments(self):
        models.DynamicSettings()

    def test_source_is_dict_gains_those_fields(self):
        source = {
            'intfield': 1,
            'boolfield': True,
            'strfield': 'hi there!',
        }

        settings = models.DynamicSettings(
            namespace='test',
            source=source,
            schema={
                'intfield': models.IntField,
                'boolfield': models.BoolField,
                'strfield': models.StrField,
            })

        self.assertTrue(settings.test.intfield, 'Dynamic setting instance did not gain fields')

    def test_can_define_multiple_namespaces(self):

        settings = models.DynamicSettings(
            namespace='namespace1',
            schema={'attr': models.IntField},
            source={'attr': 1},
        )

        settings += models.DynamicSettings(
            namespace='namespace2',
            schema={'attr': models.IntField},
            source={'attr': 1},
        )

        self.assertTrue(settings.namespace1.attr, "namespace1 wasn't created properly")
        self.assertTrue(settings.namespace2.attr, "namespace2 wasn't created properly")

    def test_ds_must_be_json_serializable(self):
        json.dumps(models.DynamicSettings(
            namespace='namespace1',
            schema={'attr': models.IntField},
            source={'attr': 1},
        ))


class FieldValidationTests(TestCase):

    def test_cant_instantiate_a_basefield(self):

        with self.assertRaises(TypeError):
            models.BaseField()

    def test_invalid_intfield_raises_error(self):

        s = models.DynamicSettings(namespace='test',
                                   schema={
                                       'intfield': models.IntField()
                                   },
                                   source={
                                       'intfield': False
                                   })

        with self.assertRaises(ValueError):
            s.validate()