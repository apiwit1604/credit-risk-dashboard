# 1. Bond-Implied PD (Reduced-Form Models)

Two related but distinct techniques for backing default probability out
of bond prices, implemented in `credit_risk/bond_pd.py` and
`credit_risk/bond_calibration.py`.

## 1.1 From a credit-spread curve (`bond_pd.py`)

**Inputs:** a risk-free spot-rate curve and a risky (corporate) spot-rate
curve of the *same* maturities.

**Idea.** Price a zero-coupon claim off each curve:

$$
P^{rf}_t = \frac{FV}{(1+r^{rf}_t)^t}, \qquad
P^{risky}_t = \frac{FV}{(1+r^{risky}_t)^t}
$$

Under risk-neutral pricing and a zero-recovery assumption, the risky
price is the riskless price scaled down by the probability of surviving
to time $t$:

$$
P^{risky}_t = P^{rf}_t \cdot Q(\tau > t)
\quad\Longrightarrow\quad
Q(\tau > t) = \frac{P^{risky}_t}{P^{rf}_t}
$$

where $\tau$ is the (risk-neutral) default time. From the cumulative
survival probability $Q(\tau>t)$ we get the cumulative default
probability $F(t) = 1 - Q(\tau>t)$, and by differencing:

$$
\text{Unconditional PD}_t = F(t) - F(t-1), \qquad
\text{Conditional PD}_t = \frac{F(t)-F(t-1)}{Q(\tau>t-1)}
$$

i.e. the *marginal* (forward) default probability, conditional on having
survived to $t-1$.

**Assumption to be explicit about:** zero recovery. If the risky bond
actually recovers some fraction of face value on default, this method
over-states PD (some of the "spread" compensates for the discount rate
and liquidity premium, not just default risk).

## 1.2 From an observed market price (`bond_calibration.py`)

**Inputs:** a bond's face value, coupon, a recovery assumption, a
risk-free curve, and its *observed market price*.

**Idea.** Price the bond as the risk-neutral expected value of its cash
flows under a candidate PD:

$$
\text{Price}(PD) = \sum_{t=1}^{n} \frac{
    S(t-1)\big[(1-PD_t) \cdot CF_t + PD_t \cdot R\big]
}{(1+r^{rf}_t)^t}
$$

where $S(t)$ is cumulative survival to $t$, $CF_t$ is the coupon (or
coupon + face value at maturity), and $R$ is the recovery value paid on
default. Solve for $PD$ (or a $PD_t$ *term structure*) that minimizes:

$$
\min_{PD} \; \big(\text{Price}(PD) - \text{Market Price}\big)^2
$$

Two variants are implemented:

- **`calibrate_flat_pd`** — one PD for every period. Well-identified: 1
  free parameter, 1 price constraint.
- **`calibrate_term_structure_pd`** — one PD per period.

> **Identification warning.** The term-structure variant fits $n$ free
> parameters against a **single** price constraint. The problem is
> under-determined: many different PD paths can reproduce the same bond
> price to the optimizer's tolerance (you can check this yourself by
> changing the initial guess and watching the solution move). Treat its
> period-by-period shape as illustrative, not uniquely identified,
> unless you add more constraints — e.g. quoted prices for several
> bonds of different maturities on the same issuer, which is how real
> desks build a PD term structure from a full curve of CDS or bond
> quotes.
