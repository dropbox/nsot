import bittle

# These values cannot be reordered. Only add new
# permissions to the end.
PermissionsFlag = bittle.FlagWord([
    "admin",        # Someone who is an admin has full permissions
                    # within a site. Admins are able to grant other
                    # permissions as well as Create/Update/Delete all
                    # resources.
])
