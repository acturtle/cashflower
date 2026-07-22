cimport cython
cimport numpy as np
import numpy as np


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef np.ndarray[double] discount(np.ndarray[double] cash_flows, np.ndarray[double] discount_rates):
    """
    Calculate the present value of cash flows for all the periods at once.

    The function returns an array, so the variable that holds the result
    must be declared as an array variable, using '@variable(array=True)'.

    Parameters
    ----------
    cash_flows : numpy.ndarray
        Cash flows to be discounted, as float values.
    discount_rates : numpy.ndarray
        Forward discount rates corresponding to each period, as float values.

    Returns
    -------
    numpy.ndarray
        Present value of the cash flows for each period.

    Examples
    --------
    >>> import numpy as np
    >>> from cashflower import discount
    >>> discount(np.array([90.0, 120.0, 100.0]), np.array([1.0, 0.8, 0.9]))
    array([258., 210., 100.])
    """
    cdef int t
    cdef int n1 = cash_flows.shape[0]
    cdef int n2 = discount_rates.shape[0]
    cdef np.ndarray[double] result = np.empty(n1)

    if n1 != n2:
        raise ValueError("Arrays must have the same length.")

    result[n1-1] = cash_flows[n1-1]

    for t in range(n1-2, -1, -1):
        result[t] = cash_flows[t] + result[t+1] * discount_rates[t+1]

    return result
