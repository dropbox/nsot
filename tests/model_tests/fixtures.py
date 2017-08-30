from django.contrib.auth.models import Group
import pytest
from pytest_django.fixtures import  django_user_model, transactional_db
import logging

from nsot import models


log = logging.getLogger(__name__)


@pytest.fixture
def user(django_user_model):
    """Create and return a non-admin user."""
    user = django_user_model.objects.create(email='user@localhost')
    return user


@pytest.fixture
def admin_user(django_user_model):
    """Create and return an admin user."""
    user = django_user_model.objects.create(
        email='admin@localhost', is_superuser=True, is_staff=True
    )
    return user


@pytest.fixture
def site():
    """Create and return a Site object."""
    site = models.Site.objects.create(
        name='Test Site', description='This is a Test Site.'
    )
    return site


@pytest.fixture
def device(site):
    """Create and return a Device object bound to ``site``."""
    device = models.Device.objects.create(site=site, hostname='foo-bar1')
    return device


@pytest.fixture
def circuit(site):
    """Create and return a Circuit object bound to ``site``."""
    device_a = models.Device.objects.create(site=site, hostname='foo-bar1')
    device_z = models.Device.objects.create(site=site, hostname='foo-bar2')

    # Create a network for interface assignments
    network = models.Network.objects.create(
        cidr='10.32.0.0/24', site=site,
    )

    # Create A/Z-side interfaces
    iface_a = models.Interface.objects.create(
        device=device_a, name='eth0', addresses=['10.32.0.1/32']
    )
    iface_z = models.Interface.objects.create(
        device=device_z, name='eth0', addresses=['10.32.0.2/32']
    )

    # Create the circuit
    circuit = models.Circuit.objects.create(
        endpoint_a=iface_a, endpoint_z=iface_z
    )
    return circuit


@pytest.fixture
def test_group():
    """Create and return a Group object."""
    test_group = Group.objects.create(name='test_group')
    return test_group
