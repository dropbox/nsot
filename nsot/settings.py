import yaml

from ipaddress import ip_network


class Settings(object):
    def __init__(self, initial_settings):
        self.settings = initial_settings

    @classmethod
    def from_settings(cls, settings, initial_settings=None):
        _settings = {}
        _settings.update(settings.settings)
        if initial_settings:
            _settings.update(initial_settings)
        return cls(_settings)

    def update_from_config(self, filename):
        with open(filename) as config:
            data = yaml.safe_load(config.read())

        settings = {}
        settings.update(data)

        for key, value in settings.iteritems():
            key = key.lower()

            if key not in self.settings:
                continue

            override = getattr(self, "override_%s" % key, None)
            if override is not None and callable(override):
                value = override(value)

            self.settings[key] = value

    def __getitem__(self, key):
        return self.settings[key]

    def __getattr__(self, name):
        try:
            return self.settings[name]
        except KeyError as err:
            raise AttributeError(err)

    # Overrides

    def override_restrict_networks(self, values):
        if values is None:
            return []

        if not isinstance(values, (list, set)):
            values = [values]

        new_values = []
        for value in values:
            if not isinstance(value, unicode):
                value = unicode(value)
            new_values.append(ip_network(value))

        return new_values


settings = Settings({
    "log_format": "%(asctime)-15s\t%(levelname)s\t%(message)s",
    "num_processes": 1,
    "database": None,
    "debug": False,
    "port": 8990,
    "user_auth_header": "X-NSoT-Email",
    "restrict_networks": [],
    "bind_address": None,
    "api_xsrf_enabled": True,
    "secret_key": "SECRET_KEY",
    "auth_token_expiry": 600,  # 10 minutes
    "sentry_dsn": None,
})
