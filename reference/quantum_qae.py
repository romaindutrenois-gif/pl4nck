"""QAE for a vanilla European call (qc-implementation-core + qae-skeleton).
Skeleton: load log-normal S_T -> encode payoff -> amplitude-estimate -> discount.
Reference-anchored: judged against Black-Scholes. Criteria are LOCKED (criteria.txt);
qubit count is an implementation parameter, not a criterion.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
from baseline import CallSpec, bs_call
from qiskit_finance.circuit.library import LogNormalDistribution
from qiskit_finance.applications.estimation import EuropeanCallPricing
from qiskit_algorithms import IterativeAmplitudeEstimation
from qiskit.primitives import StatevectorSampler

SEED = 42
spec = CallSpec(S0=100, K=110, r=0.05, sigma=0.20, T=1.0)
ref = bs_call(spec)
disc = np.exp(-spec.r * spec.T)

mu = np.log(spec.S0) + (spec.r - 0.5 * spec.sigma**2) * spec.T
variance = (spec.sigma * np.sqrt(spec.T))**2
mean_ST = np.exp(mu + variance/2)
stddev = np.sqrt((np.exp(variance)-1)*np.exp(2*mu+variance))
low, high = max(0.0, mean_ST - 3*stddev), mean_ST + 3*stddev

def run(nq, transpile_report=False):
    model = LogNormalDistribution(nq, mu=mu, sigma=variance, bounds=(low, high))
    eur = EuropeanCallPricing(num_state_qubits=nq, strike_price=spec.K,
                              rescaling_factor=0.25, bounds=(low, high), uncertainty_model=model)
    problem = eur.to_estimation_problem()
    iae = IterativeAmplitudeEstimation(epsilon_target=0.01, alpha=0.05,
                                       sampler=StatevectorSampler(seed=SEED))
    res = iae.estimate(problem)
    price = disc * eur.interpret(res)
    ci = tuple(disc * c for c in res.confidence_interval_processed)
    return price, ci

print(f"Black-Scholes reference (exact): {ref:.6f}\n")
print(f"{'qubits':>6} {'QAE price':>11} {'rel err':>9} {'C1<2%':>6} {'C2 in CI':>9}")
for nq in (3, 4, 5, 6):
    price, ci = run(nq)
    rel = abs(price - ref)/ref
    c1, c2 = rel < 0.02, ci[0] <= ref <= ci[1]
    print(f"{nq:>6} {price:>11.4f} {rel*100:>8.2f}% {str(c1):>6} {str(c2):>9}")

# Final verdict at the highest-fidelity config against the LOCKED criteria
price, ci = run(6)
rel = abs(price - ref)/ref
c1, c2 = rel < 0.02, ci[0] <= ref <= ci[1]
print(f"\nAt 6 qubits: price {price:.4f}, CI [{ci[0]:.4f}, {ci[1]:.4f}]")
print(f"VERDICT: {'Validated' if (c1 and c2) else 'Not validated'}")
