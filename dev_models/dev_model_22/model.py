from cashflower import variable

@variable()
def NoPolsBoP(t):
    """No of policies at the start of period"""
    if ((t==0 or t>288)) :
        return 0
    elif (t==1) :
        return 1
    else:
        return NoPolsEoP(t-1)-MattNo(t-1)

@variable()
def MatRateM(t):
    return 0.01

@variable()
def LapseRateD(t):
    return 0.01

@variable()
def DeathRateD(t):
    return 0.01

@variable()
def SurrNo(t):
    return NoPolsBoP(t)*LapseRateD(t)

@variable()
def DeathNo(t):
    return NoPolsBoP(t)*DeathRateD(t)


@variable()
def MattNo(t):
    if (t==0) :
        return 0
    else:
        return MatRateM(t)*NoPolsEoP(t-1)

@variable()
def NoPolsEoP(t):
    if (t==0) :
        return 1
    elif (t>288) :
        return 0
    else:
        return NoPolsBoP(t)-SurrNo(t)-DeathNo(t)
