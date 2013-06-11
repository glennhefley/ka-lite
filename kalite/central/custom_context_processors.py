from django.conf import settings
from config.models import Settings
from main.models import LanguagePack

def custom(request):
    return {
        "base_template": "base_central.html",
    }
