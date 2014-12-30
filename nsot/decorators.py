import functools

from .permissions import PermissionsFlag


def _has_any_perm(user, site_id, perms):
    permissions_flag = user.get_permissions(site_id)
    for perm in perms:
        if permissions_flag.has(perm):
            return True
    return False


def any_perm(*perms):
    """ Takes a list of permissions and fails if none are valid for a user.

    """
    def dec(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if "site_id" not in kwargs:
                raise ValueError(
                    "Permission decorator used on handler method "
                    "without site_id keyword argument."
                )
            if not _has_any_perm(self.current_user, kwargs["site_id"], perms):
                return self.unauthorized()
            return method(self, *args, **kwargs)
        return wrapper
    return dec
