import math

def calculate_area(radius):
    """
    Calculate the area of a circle given its radius.

    Parameters
    ----------
    radius : float
        The radius of the circle. Must be a non-negative value.

    Returns
    -------
    float
        The area of the circle.

    Raises
    ------
    ValueError
        If the radius is negative.

    Examples
    --------
    >>> calculate_area(5)
    78.53981633974483
    >>> calculate_area(0)
    0.0
    >>> calculate_area(-3)
    Traceback (most recent call last):
        ...
    ValueError: Radius cannot be negative
    """
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    return math.pi * radius ** 2


import doctest
doctest.testmod()