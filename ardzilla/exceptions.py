""" ardzilla exceptions
"""


class EmptyCollectionError(RuntimeError):
    """ Exception raised when trying to create ARD from an empty set of images
    """
    pass
