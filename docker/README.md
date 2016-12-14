# NSoT Docker Image

This Docker image runs NSoT. Perfect for quick developing and even deploying in
production.

## Using this image

`nsot-server --config=/etc/nsot/nsot.conf.py` is the image entrypoint, so the
command passed to docker run becomes CLI parameters. This is equivalent to what
the default is:

```
$ docker run -p 8990:8990 -d --name=nsot nsot/nsot start --noinput
```

Image tags should correspond with NSoT release version numbers. Basic usage is
like:

```bash

$ NSOT_SECRET='X9HqplzM_0E3Ghf3QOPDnO2k5VpVHkfzsZsVer4OeKA='
$ docker run -p 8990:8990 -d --name=nsot -e NSOT_SECRET=$NSOT_SECRET nsot/nsot:1.0.10
```

## Getting started

With the docker container running, you need to create a superuser
From the command above, create the super user as follows:

```bash
$ docker exec -it nsot bash
# nsot-server --config=/etc/nsot/nsot.conf.py createsuperuser —email your@email.here
```

This will prompt you for a password, which you can then use to log into http://dockerhost:8990/

If you have an established database and you don't wish to attempt to upgrade it
then you'll need to specify `--no-upgrade`

If you wanted to do interactive debugging, use the docker run flags `-ti` and
pass the relevant options:

```bash
$ docker run -p 8990:8990 -ti --rm nsot/nsot dbshell
    SQLite version 3.8.2 2013-12-06 14:53:30
    Enter ".help" for instructions
    Enter SQL statements terminated with a ";"
    sqlite> exit

OR

$ docker run -p 8990:8990 -ti --rm nsot/nsot shell_plus
    # Shell Plus Model Imports
    from django.contrib.admin.models import LogEntry
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.sessions.models import Session
    from nsot.models import Assignment, Attribute, Change, Device, Interface,
    Network, Site, User, Value
    # Shell Plus Django Imports
    from django.utils import timezone
    from django.conf import settings
    from django.core.cache import cache
    from django.db.models import Avg, Count, F, Max, Min, Sum, Q, Prefetch
    from django.core.urlresolvers import reverse
    from django.db import transaction
    Python 2.7.6 (default, Jun 22 2015, 17:58:13)
    Type "copyright", "credits" or "license" for more information.

    IPython 3.1.0 -- An enhanced Interactive Python.
    ?         -> Introduction and overview of IPython's features.
    %quickref -> Quick reference.
    help      -> Python's own help system.
    object?   -> Details about 'object', use 'object??' for extra details.

    In [1]:
```

If you want to add an entire custom config, volume mount it to
`/etc/nsot/nsot.conf.py`

## Ports

Only TCP 8990 is exposed

## Environment Variables

Pass these with `-e` to control the configuration. `NSOT_SECRET` should be the
bare minimum set, setting an external DB if in production or wanting
persistence should be second.

Note that the `NSOT_SECRET` must be 32 url-safe base64-encoded bytes. You may
generate one by executing this:

```
python -c "import base64, os; print base64.urlsafe_b64encode(os.urandom(32))"
```

| Variable            | Default Value    |
|:--------------------|:-----------------|
| `DB_ENGINE`         | `django.db.backends.sqlite3` |
| `DB_NAME`           | `nsot.sqlite3`               |
| `DB_USER`           | `nsot`                       |
| `DB_PASSWORD`       | ''                           |
| `DB_HOST`           | ''                           |
| `DB_PORT`           | ''                           |
| `NSOT_EMAIL`        | `X-NSoT-Email`               |
| `NSOT_SECRET`       | `nJvyRB8tckUWvquJZ3ax4QnhpmqTgVX2k3CDY13yK9E=` |

## Contributing

This image is maintained upstream under `docker/Dockerfile.sub` template.
Changes to `docker/Dockerfile` will be overwritten during the next version
bump.
