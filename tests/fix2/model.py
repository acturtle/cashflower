from cashflower import assign, ModelVariable


var_a = ModelVariable()
var_b = ModelVariable()
var_c = ModelVariable()


@assign(var_a)
def var_a_formula(t):
    return 2


@assign(var_b)
def var_b_formula(t):
    return var_a(t) * 2


@assign(var_c)
def var_c_formula(t):
    return var_b(t) * 2
