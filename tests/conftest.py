import os


def pytest_report_header(config):
    """Customize the report header to display API version."""
    api_version = os.getenv('NSOT_API_VERSION')
    return 'Using NSoT API version: %s' % api_version
