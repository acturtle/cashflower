from cashflower import variable

@variable()
def NoPolsBoP(t):
    if ((t==0 or t>288)) :
        return 0
    elif (t==1) :
        return 1
    else:
        return NoPolsEoP(t-1)-MattNo(t-1)

@variable()
def NoPolsEoP(t):
    if (t==0) :
        return 1
    elif (t>288) :
        return 0
    else:
        return NoPolsBoP(t)-SurrNo(t)-DeathNo(t)

@variable()
def DeathNo(t):
    return NoPolsBoP(t)

@variable()
def SurrNo(t):
    return NoPolsBoP(t)

@variable()
def MattNo(t):
    if (t==0) :
        return 0
    else:
        return NoPolsEoP(t-1)
