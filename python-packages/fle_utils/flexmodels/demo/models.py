from django.db import models

from flexmodels.models import FlexModel

class TestModel(FlexModel):

    _model_identifier = "flexmodels.testmodel"

    name = models.CharField(max_length=10)
    age = models.IntegerField()
    description = models.TextField()

class Test2Model(models.Model):
    name = models.CharField(max_length=10)