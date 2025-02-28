def annuity_certain(i, n, timing="immediate"):
    if timing == "immediate":
        return (1 - (1 + i) ** (-n) / i) * (1 + i)
    elif timing == "due":
        return 1 - (1 + i) ** (-n) / i
    else:
        raise ValueError("Invalid timing. Must be 'due' or 'immediate'.")


# Macaulay duration
def macaulay_duration(cash_flows, discount_rate):
    """
    Calculate the Macaulay Duration of a bond.

    Parameters:
    - cash_flows: A list of cash flows (coupon payments and principal repayment).
    - discount_rate: The discount rate (as a decimal, e.g., 0.05 for 5%).

    Returns:
    - The Macaulay Duration.
    """
    # Calculate present values of cash flows
    present_values = [cf / (1 + discount_rate) ** (i + 1) for i, cf in enumerate(cash_flows)]

    # Calculate the total present value (price of the bond)
    bond_price = sum(present_values)

    # Calculate the weighted sum of time periods (i + 1) multiplied by the present value of each cash flow
    weighted_sum = sum((i + 1) * present_values[i] for i in range(len(cash_flows)))

    # Macaulay Duration formula
    duration = weighted_sum / bond_price
    return duration


# Example Usage:
cash_flows = [50, 50, 50, 50, 1050]  # Coupon payments and face value at maturity
discount_rate = 0.05  # 5% discount rate

duration = macaulay_duration(cash_flows, discount_rate)
print(f"Macaulay Duration: {duration} years")
