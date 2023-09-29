cimport cython
cimport numpy as np
import numpy as np


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef np.ndarray[double] discount(np.ndarray[double] cash_flows, np.ndarray[double] discount_rates):
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
