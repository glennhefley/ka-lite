from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

import settings


def require_admin(handler):
    def wrapper_fn(request, *args, **kwargs):
        if (settings.CENTRAL_SERVER and request.user.is_authenticated()) or getattr(request, "is_admin", False):
            return handler(request, *args, **kwargs)
        # Translators: Please ignore the html tags e.g. "Please login as one below, or <a href='%s'>go to home.</a>" is simply "Please login as one below, or go to home."
        messages.error(request, mark_safe(_("To view the page you were trying to view, you need to be logged in as a teacher or an admin. Please login as one below, or <a href='%s'>go to home.</a>") % reverse("homepage")))
        return HttpResponseRedirect(reverse("login") + "?next=" + request.path)
    return wrapper_fn
    


def central_server_only(handler):
    def wrapper_fn(*args, **kwargs):
        if not settings.CENTRAL_SERVER:
            return HttpResponseNotFound("This path is only available on the central server.")
        return handler(*args, **kwargs)
    return wrapper_fn


def distributed_server_only(handler):
    def wrapper_fn(*args, **kwargs):
        if settings.CENTRAL_SERVER:
            return HttpResponseNotFound(_("This path is only available on distributed servers."))
        return handler(*args, **kwargs)
    return wrapper_fn
    

#@login_required
def authorized_login_required(handler):
    def wrapper_fn(*args, **kwargs):
        return handler(*args,**kwargs)
    return wrapper_fn