from django.db import models

from flexmodels.models import FlexModel


class ResultModel(FlexModel):

    _model_identifier = "flexmodels.resultmodel"

    person = models.ForeignKey("PersonModel")
    score = models.IntegerField()


class LogModel(FlexModel):

    _model_identifier = "flexmodels.logmodel"

    person = models.ForeignKey("PersonModel")
    result = models.ForeignKey("ResultModel")


class PersonModel(FlexModel):

    _model_identifier = "flexmodels.personmodel"

    name = models.CharField(max_length=10)
    age = models.IntegerField()
    description = models.TextField()

