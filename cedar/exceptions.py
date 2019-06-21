""" cedar exceptions
"""


class EmptyCollectionError(ValueError):
    """ Raised when trying to create pre-ARD from an empty set of images
    """
    pass


class EmptyOrderError(ValueError):
    """ Raised when trying to submit an empty pre-ARD order
    """
    pass
