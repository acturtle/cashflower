Life insurance
==============

The aim of the life insurances is to reduce the financial impact of the event of untimely death.
The life insurances are long-term in their nature which provides a significant element of uncertainty.

The size and time of payment in life insurance depend on the time of death of the insured.
The actuarial cash flow models are built as a function of the :code:`t` variable.

We usually consider life insurance as a insurance on human lives, but the same idea can apply for objects, such as: equipment, machines or loans.

There are multiple types of the life insurance. We will build simple models to illustrate mechanism behind:
* level benefit insurance
	* a whole life insurance
	* an n-year term life insurance
* endowment insurance
	* an n-year pure endowment
	* an n-year endowment insurance
* deferred insurance
	* an m-year deferred insurance

In our models, we will calculate the net single premium.

The present value of the benefit payment is a random variable. The expectation of the this variable at policy issue is called the net single premium.
* It is a net premium because it does not contain risk loading (compensation for taking the risk of variability).
* It is a single premium in contrast to monthly, annual or other premiums that are aceptable in life insurance practice.

The net single premium tells how much a life insurance is worth.

The table below present the actuarial notation for the net single premium for these insurances.

<tabela przy pomocy mathjaxa>


Level benefit insurance



Whole life


Whole life insurance provides for a payment following the death of the insured at any time in the future.

Term life


An n-year term life insurance provides a payment only if the insured dies within the n-year term of an insurance commencing at issue.


Endowment insurance


Pure endowment


An n-year pure endowment provides for a payment at the end of the n years if and only if the insured surives at least  n years from the time of policy issue.

Endowment

An n-year endowment insurance provides for an amount to be payable either following the death of the insured or upon the surviva of the insured to the end of the n-year term, whichever occurs first.


Deferred insurance


An m-year deferred insurance provides for a benefit following the death of the insured only if the insured dies at least m years following policy issue.


Repositories:
- whole_life
- term_life
- pure_edowment
- endowment
- deferred
