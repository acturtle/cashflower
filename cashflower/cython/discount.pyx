cimport numpy as np
import numpy as np


cpdef np.ndarray[double] discount(np.ndarray[double] cash_flows, np.ndarray[double] discount_rates):
    cdef int n = cash_flows.shape[0]
    cdef np.ndarray[double] result = np.empty(n)
    cdef int t

    result[-1] = cash_flows[-1]

    for t in range(n-2, -1, -1):
        result[t] = cash_flows[t] + result[t+1] * discount_rates[t+1]

    return result
