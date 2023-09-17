import math

from cashflower import variable
from input import assumption, main, runplan
from settings import settings


@variable()
def proj_len():
    return max(12 * policy_term() - duration_mth(0) + 1, 0)


@variable()
def age(t):
    return main.get("age_at_entry") + duration(t)


@variable()
def av_at_bef_mat(t):
    return av_pp_at_bef_prem(t) * pols_if_at_bef_mat(t)


@variable()
def av_at_bef_nb(t):
    return av_pp_at_bef_prem(t) * pols_if_at_bef_nb(t)


@variable()
def av_at_bef_fee(t):
    return av_pp_at_bef_fee(t) * pols_if_at_bef_decr(t)


@variable()
def av_change(t):
    if t == settings["T_MAX_CALCULATION"]:
        return 0
    return av_at_bef_mat(t+1) - av_at_bef_mat(t)


@variable()
def av_pp_at_bef_prem(t):
    if t == 0:
        return main.get("av_pp_init")
    else:
        return av_pp_at_bef_inv(t-1) + inv_income_pp(t-1)


@variable()
def av_pp_at_bef_fee(t):
    return av_pp_at_bef_prem(t) + prem_to_av_pp(t)


@variable()
def av_pp_at_bef_inv(t):
    return av_pp_at_bef_fee(t) - maint_fee_pp(t) - coi_pp(t)


@variable()
def av_pp_at_mid_mth(t):
    return av_pp_at_bef_inv(t) + 0.5 * inv_income_pp(t)


@variable()
def claim_pp_death(t):
    return max(main.get("sum_assured"), av_pp_at_mid_mth(t))


@variable()
def claim_pp_lapse(t):
    return av_pp_at_mid_mth(t)


@variable()
def claim_pp_maturity(t):
    return av_pp_at_bef_prem(t)


@variable()
def claims_death(t):
    return claim_pp_death(t) * pols_death(t)


@variable()
def claims_lapse(t):
    return claims_from_av_lapse(t) - surr_charge(t)


@variable()
def claims_maturity(t):
    return claims_from_av_maturity(t)


@variable()
def claims(t):
    return claims_death(t) + claims_lapse(t) + claims_maturity(t)


@variable()
def claims_from_av_death(t):
    return av_pp_at_mid_mth(t) * pols_death(t)


@variable()
def claims_from_av_lapse(t):
    return av_pp_at_mid_mth(t) * pols_lapse(t)


@variable()
def claims_from_av_maturity(t):
    return av_pp_at_bef_prem(t) * pols_maturity(t)


@variable()
def claims_over_av(t):
    return (claim_pp_death(t) - av_pp_at_mid_mth(t)) * pols_death(t)


@variable()
def coi(t):
    return coi_pp(t) * pols_if_at_bef_decr(t)


@variable()
def coi_rate(t):
    return 1.1 * mort_rate_mth(t)


@variable()
def coi_pp(t):
    return coi_rate(t) * net_amt_at_risk(t)


@variable()
def commissions(t):
    return 0.05 * premiums(t)


@variable()
def discount_ann(t):
    if t > 0 and (t-1)//12 == t//12:
        return discount_ann(t-1)
    return float(assumption["disc_rate_ann"].get_value(str(t // 12), "zero_spot"))


@variable()
def discount(t):
    return (1 + discount_ann(t))**(-t/12)


@variable()
def duration(t):
    return duration_mth(t) // 12


@variable()
def duration_mth(t):
    if t == 0:
        return main.get("duration_mth")
    else:
        return duration_mth(t-1) + 1


@variable()
def expenses(t):
    return (assumption["expense_acq"] * pols_new_biz(t) +
            pols_if_at_bef_decr(t) * assumption["expense_maint"]/12 * inflation_factor(t))


@variable()
def inflation_factor(t):
    return (1 + assumption["inflation_rate"])**(t/12)


@variable()
def inv_income(t):
    if t == settings["T_MAX_CALCULATION"]:
        return 0
    return inv_income_pp(t) * pols_if_at_bef_mat(t+1) + 0.5 * inv_income_pp(t) * (pols_death(t) + pols_lapse(t))


@variable()
def inv_income_pp(t):
    return inv_return_mth(t) * av_pp_at_bef_inv(t)


@variable()
def inv_return_mth(t):
    mu = 0.02
    sigma = 0.03
    dt = 1 / 12
    std_norm_rand = float(assumption["std_norm_rand"].get_value((str(runplan.get("scen_id")), str(t)), "std_norm_rand"))
    return math.exp((mu - 0.5 * sigma ** 2) * dt + sigma * dt ** 0.5 * std_norm_rand) - 1


@variable()
def lapse_rate(t):
    return max(0.1 - 0.02 * duration(t), 0.02)


@variable()
def maint_fee(t):
    return maint_fee_pp(t) * pols_if_at_bef_decr(t)


@variable()
def maint_fee_rate():
    return 0.01 / 12


@variable()
def maint_fee_pp(t):
    return maint_fee_rate() * av_pp_at_bef_fee(t)


@variable()
def margin_expense(t):
    return (main.get("load_prem_rate") * premium_pp(t) * pols_if_at_bef_decr(t) + surr_charge(t) + maint_fee(t)
            - commissions(t)) - expenses(t)


@variable()
def margin_mortality(t):
    return coi(t) - claims_over_av(t)


@variable()
def mort_rate(t):
    if t > 0 and age(t-1) == age(t) and (duration(t-1) == duration(t) or duration(t) > 5):
        return mort_rate(t-1)
    age_t = str(max(min(age(t), 120), 18))
    duration_t = str(max(min(duration(t), 5), 0))
    return float(assumption["mort_table"].get_value(age_t, duration_t))


@variable()
def mort_rate_mth(t):
    return 1 - (1-mort_rate(t))**(1/12)


@variable()
def mort_table_last_age():
    return 120


@variable()
def net_amt_at_risk(t):
    return max(main.get("sum_assured") - av_pp_at_bef_fee(t), 0)


@variable()
def net_cf(t):
    if t >= proj_len():
        return 0

    return premiums(t) + inv_income(t) - claims(t) - expenses(t) - commissions(t) - av_change(t)


@variable()
def policy_term():
    if main.get("is_wl"):
        return mort_table_last_age() - main.get("age_at_entry")
    else:
        return main.get("policy_term")


@variable()
def pols_death(t):
    return pols_if_at_bef_decr(t) * mort_rate_mth(t)


@variable()
def pols_if(t):
    return pols_if_at_bef_mat(t)


@variable()
def pols_if_at_bef_mat(t):
    if t == 0:
        return pols_if_init()
    else:
        return pols_if_at_bef_decr(t-1) - pols_lapse(t-1) - pols_death(t-1)


@variable()
def pols_if_at_bef_nb(t):
    return pols_if_at_bef_mat(t) - pols_maturity(t)


@variable()
def pols_if_at_bef_decr(t):
    return pols_if_at_bef_nb(t) + pols_new_biz(t)


@variable()
def pols_if_init():
    if duration_mth(0) > 0:
        return main.get("policy_count")
    else:
        return 0


@variable()
def pols_lapse(t):
    return (pols_if_at_bef_decr(t) - pols_death(t)) * (1-(1 - lapse_rate(t))**(1/12))


@variable()
def pols_maturity(t):
    if duration_mth(t) == policy_term() * 12:
        return pols_if_at_bef_mat(t)
    else:
        return 0


@variable()
def pols_new_biz(t):
    if duration_mth(t) == 0:
        return main.get("policy_count")
    else:
        return 0


@variable()
def prem_to_av(t):
    return prem_to_av_pp(t) * pols_if_at_bef_decr(t)


@variable()
def prem_to_av_pp(t):
    return (1 - main.get("load_prem_rate")) * premium_pp(t)


@variable()
def premium_pp(t):
    if main.get("premium_type") == 'SINGLE':
        if duration_mth(t) == 0:
            return main.get("premium_pp")
        else:
            return 0
    elif main.get("premium_type") == 'LEVEL':
        if duration_mth(t) < 12 * policy_term():
            return main.get("premium_pp")
        else:
            return 0


@variable()
def premiums(t):
    return premium_pp(t) * pols_if_at_bef_decr(t)


@variable()
def pv_av_change(t):
    if t == settings["T_MAX_CALCULATION"]:
        return av_change(t) * discount(t)
    return av_change(t) * discount(t) + pv_av_change(t+1)


@variable()
def pv_claims(t):
    if t == settings["T_MAX_CALCULATION"]:
        return claims(t) * discount(t)
    return claims(t) * discount(t) + pv_claims(t+1)


@variable()
def pv_commissions(t):
    if t == settings["T_MAX_CALCULATION"]:
        return commissions(t) * discount(t)
    return commissions(t) * discount(t) + pv_commissions(t+1)


@variable()
def pv_expenses(t):
    if t == settings["T_MAX_CALCULATION"]:
        return expenses(t) * discount(t)
    return expenses(t) * discount(t) + pv_expenses(t+1)


@variable()
def pv_inv_income(t):
    if t == settings["T_MAX_CALCULATION"]:
        return inv_income(t) * discount(t)
    return inv_income(t) * discount(t) + pv_inv_income(t+1)


@variable()
def pv_net_cf(t):
    return pv_premiums(t) + pv_inv_income(t) - pv_claims(t) - pv_expenses(t) - pv_commissions(t) - pv_av_change(t)


@variable()
def pv_pols_if(t):
    if t == settings["T_MAX_CALCULATION"]:
        return pols_if(t) * discount(t)
    return pols_if(t) * discount(t) + pv_pols_if(t+1)


@variable()
def pv_premiums(t):
    if t == settings["T_MAX_CALCULATION"]:
        return premiums(t) * discount(t)
    return premiums(t) * discount(t) + pv_premiums(t+1)


@variable()
def surr_charge(t):
    return surr_charge_rate(t) * av_pp_at_mid_mth(t) * pols_lapse(t)


@variable()
def surr_charge_rate(t):
    if main.get("has_surr_charge"):
        if duration(t) > 10:
            return surr_charge_rate(t-1)
        else:
            return float(assumption["surr_charge_table"].get_value(str(duration(t)), main.get("surr_charge_id")))
    else:
        return 0
