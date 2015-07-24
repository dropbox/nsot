"""
Custom context processors for templates.

Put me in ``settings.py`` like so::

    TEMPLATE_CONTEXT_PROCESSORS = (
        # ...
        'nsot.ui.context_processors.app_version',
    )

Credit: http://stackoverflow.com/a/4256485/194311
"""

def app_version(request):
    """A template variable to display current version."""
    from nsot import __version__
    return {'NSOT_VERSION': __version__}
