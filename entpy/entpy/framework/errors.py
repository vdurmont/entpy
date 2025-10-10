class PrivacyError(Exception):
    """
    Used when an action cannot be performed because the current ViewerContext
    does not have the permission to do so.
    """

    pass


class EntNotFoundError(Exception):
    """
    Used when an action cannot be performed because the targeted entity could not
    be found.
    """

    pass


class ExecutionError(Exception):
    """
    Used when something unexpected happened at runtime.
    """

    pass
