"""
credit_risk
===========
A small toolkit of credit-risk models built from first principles:

- bond_pd                 : PD bootstrapped from a risk-free vs. risky bond spread
- bond_calibration         : PD calibrated to match an observed market bond price
- merton                   : Merton (1974) structural model (equity as a call on firm assets)
- kmv_montecarlo            : Portfolio Monte Carlo built on the Merton/KMV asset model
- credit_var_ratings        : CreditMetrics-style ratings-migration Monte Carlo Credit VaR
- basel_single_factor       : Basel II/III IRB single-factor (ASRF) regulatory capital formula

See docs/ for the mathematical derivation behind each model, and for a
note on the asset-correlation convention (rho vs. R = rho^2) that
differs between kmv_montecarlo/basel_single_factor and credit_var_ratings.
"""
