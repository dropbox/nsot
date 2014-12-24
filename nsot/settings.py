import yaml


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


settings = Settings({
    "log_format": "%(asctime)-15s\t%(levelname)s\t%(message)s",
    "num_processes": 1,
    "database": None,
    "debug": False,
    "port": 8990,
    "user_auth_header": "X-NSoT-Email",
})
