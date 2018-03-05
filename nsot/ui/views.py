# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from httplib import responses
import logging

from django.shortcuts import render
from django.views.generic import TemplateView


log = logging.getLogger(__name__)


class FeView(TemplateView):
    """
    Front-end UI view that hands-off rendering to Angular.js.

    Any additional context needed to be passed to the templates, should be
    added in ``nsot.ui.context_processors``
    """
    template_name = 'ui/app.html'


def render_error(request, status_code, template_name='ui/error.html'):
    """Generic base for rendering error pages."""
    message = responses[status_code].upper()
    context = {'code': status_code, 'message': message}
    return render(request, template_name, context, status=status_code)


def handle400(request):
    """Handler for 400."""
    return render_error(request, 400)


def handle403(request):
    """Handler for 403."""
    return render_error(request, 403)


def handle404(request):
    """Handler for 404."""
    return render_error(request, 404)


def handle500(request):
    """Handler for 500."""
    return render_error(request, 500)
