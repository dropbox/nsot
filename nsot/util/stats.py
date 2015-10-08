from __future__ import unicode_literals, print_function

"""
Gettings stats out of NSoT.
"""

from netaddr import IPNetwork, IPSet


__all__ = ('calculate_network_utilization', 'get_network_utilization')


def calculate_network_utilization(parent, hosts, as_string=False):
    """
    Calculate utilization for a network and its descendents.

    :param parent:
        The parent network

    :param hosts:
        List of host IPs descendent from parent

    :param as_string:
        Whether to return stats as a string
    """
    parent = IPNetwork(str(parent))
    hosts = IPSet(str(ip) for ip in hosts if IPNetwork(str(ip)) in parent)

    used = float(hosts.size) / float(parent.size)
    free = 1 - used
    num_free = parent.size - hosts.size

    stats = {
        'percent_used': used,
        'num_used': hosts.size,
        'percent_free': free,
        'num_free': num_free,
        'max': parent.size,
    }

    # 10.47.216.0/22 - 14% used (139), 86% free (885)
    if as_string:
        return '{} - {:.0%} used ({}), {:.0%} free ({})'.format(
            parent, used, hosts.size, free, num_free
        )

    return stats


def get_network_utilization(network, as_string=False):
    """
    Get utilization from Network instance.

    :param network:
        A Network model instance

    :param as_string:
        Whether to return stats as a string
    """
    descendents = network.get_descendents().filter(is_ip=True)
    return calculate_network_utilization(network, descendents, as_string)
