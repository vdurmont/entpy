class PrivacyError(Exception):
    """
    Used when an action cannot be performed because the current ViewerContext
    does not have the permission to do so.
    """

    pass
