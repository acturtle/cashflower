def annuity_certain(i, n, timing="immediate"):
    if timing == "immediate":
        return (1 - (1 + i) ** (-n) / i) * (1 + i)
    elif timing == "due":
        return 1 - (1 + i) ** (-n) / i
    else:
        raise ValueError("Invalid timing. Must be 'due' or 'immediate'.")
