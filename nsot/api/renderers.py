from __future__ import unicode_literals
from rest_framework.renderers import BrowsableAPIRenderer


class FilterlessBrowsableAPIRenderer(BrowsableAPIRenderer):
    """Custom browsable API renderer that doesn't show filter forms."""
    def get_filter_form(self, data, view, request):
        """
        Disable filter form display.

        This is because of major performance problems with large installations,
        especially with large sets of related objects.

        FIXME(jathan): Revisit this after browsable API rendering has improved
        in future versions of DRF.
        """
        return
