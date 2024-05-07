from cashflower import variable

@variable()
def NoPolsBoP(t):
    """No of policies at the start of period"""
    if ((t==0 or t>PolTerm())) :
        return 0
    elif (t==1) :
        return 1
    else:
        return NoPolsEoP(t-1)-MattNo(t-1)

@variable()
def LapseRateY(t):
    """Annual Lapse Rate"""
    if ((t==0 or t>PolTerm())) :
        return 0
    elif ((t-1)%(12)==0) :
        return 0.05
    else:
        return LapseRateY(t-1)

@variable()
def LapseRateM(t):
    """Monthly Lapse Rate"""
    return 1-(1-LapseRateY(t))**(1/12)

@variable()
def DeathRateY(t):
    """Annual Death Rate"""
    if ((t==0 or t>PolTerm())) :
        return 0
    elif ((t-1)%(12)==0) :
        return 0.001
    else:
        return DeathRateY(t-1)

@variable()
def DeathRateM(t):
    """Monthly Death Rate"""
    return 1-(1-DeathRateY(t))**(1/12)

@variable()
def LapseRateD(t):
    """Monthly Lapse Rate (dependent)"""
    return LapseRateM(t)*(1-DeathRateM(t)*LapseT())

@variable()
def DeathRateD(t):
    """Monthly Death Rate (dependent)"""
    return DeathRateM(t)*(1-LapseRateM(t)*LapseT())

@variable()
def SurrNo(t):
    """No of surrenders"""
    return NoPolsBoP(t)*LapseRateD(t)

@variable()
def DeathNo(t):
    """No of deaths"""
    return NoPolsBoP(t)*DeathRateD(t)

@variable()
def MatRate(t):
    """Annual Maturity Rate"""
    if (t==PolTerm()) :
        return 1
    else:
        return 0

@variable()
def MatRateM(t):
    return 1-(1-MatRate(t))**(1/12)

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
    elif (t>PolTerm()) :
        return 0
    else:
        return NoPolsBoP(t)-SurrNo(t)-DeathNo(t)

@variable()
def PolTerm():
    return 288

def LapseT():
    return 0.5
