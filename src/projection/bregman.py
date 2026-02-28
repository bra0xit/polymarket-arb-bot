"""
Bregman Projection for Optimal Arbitrage Calculation

Based on the research paper: "Arbitrage-Free Combinatorial Market Making via Integer Programming"
(arXiv:1606.02825v2)

The Bregman divergence for LMSR markets is the KL divergence:
D(μ||θ) = Σ μ_i * ln(μ_i / θ_i)

The optimal arbitrage trade is found by projecting current prices
onto the arbitrage-free polytope M using this divergence.
"""

import numpy as np
from scipy.optimize import minimize
from typing import Optional
import warnings


def kl_divergence(mu: np.ndarray, theta: np.ndarray, eps: float = 1e-10) -> float:
    """
    Compute KL divergence D(μ||θ) = Σ μ_i * ln(μ_i / θ_i)
    
    This is the Bregman divergence for LMSR cost function.
    """
    # Ensure numerical stability
    mu = np.clip(mu, eps, 1 - eps)
    theta = np.clip(theta, eps, 1 - eps)
    
    return np.sum(mu * np.log(mu / theta))


def negative_entropy(mu: np.ndarray, eps: float = 1e-10) -> float:
    """
    R(μ) = Σ μ_i * ln(μ_i)
    
    The convex conjugate of LMSR cost function.
    """
    mu = np.clip(mu, eps, 1 - eps)
    return np.sum(mu * np.log(mu))


def bregman_projection_simplex(
    theta: np.ndarray,
    eps: float = 1e-10
) -> np.ndarray:
    """
    Project prices onto the probability simplex using Bregman projection.
    
    For a simple YES/NO market, this normalizes prices to sum to 1
    while preserving the information structure (via KL divergence).
    
    Closed-form solution for simplex projection with KL divergence:
    μ* = θ / Σθ (proportional normalization)
    """
    theta = np.clip(theta, eps, 1 - eps)
    return theta / np.sum(theta)


def bregman_projection_constrained(
    theta: np.ndarray,
    A: np.ndarray,
    b: np.ndarray,
    bounds: Optional[tuple] = None,
    max_iter: int = 1000
) -> tuple[np.ndarray, float]:
    """
    Project prices onto constrained polytope using Bregman projection.
    
    Solves: min_μ D(μ||θ) s.t. Aμ ≥ b, μ ∈ bounds
    
    Args:
        theta: Current market prices (n-dimensional)
        A: Constraint matrix (m x n)
        b: Constraint bounds (m-dimensional)
        bounds: Variable bounds, default (0.01, 0.99) for each
        max_iter: Maximum optimization iterations
    
    Returns:
        (projected_prices, divergence)
    """
    n = len(theta)
    
    if bounds is None:
        bounds = [(0.01, 0.99)] * n
    
    # Objective: minimize KL divergence
    def objective(mu):
        return kl_divergence(mu, theta)
    
    # Gradient of KL divergence w.r.t. mu
    def gradient(mu):
        eps = 1e-10
        mu = np.clip(mu, eps, 1 - eps)
        return np.log(mu / theta) + 1
    
    # Constraints: Aμ ≥ b
    constraints = []
    for i in range(len(b)):
        constraints.append({
            'type': 'ineq',
            'fun': lambda mu, i=i: np.dot(A[i], mu) - b[i]
        })
    
    # Initial guess: simplex projection
    mu0 = bregman_projection_simplex(theta)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = minimize(
            objective,
            mu0,
            method='SLSQP',
            jac=gradient,
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': max_iter, 'ftol': 1e-9}
        )
    
    mu_star = result.x
    divergence = result.fun
    
    return mu_star, divergence


def calculate_arbitrage_profit(
    theta: np.ndarray,
    mu_star: np.ndarray
) -> float:
    """
    Calculate the maximum extractable arbitrage profit.
    
    From the paper: The max guaranteed profit equals the Bregman divergence
    between current prices and the arbitrage-free projection.
    
    profit = D(μ*||θ)
    """
    return kl_divergence(mu_star, theta)


def calculate_optimal_trade(
    theta: np.ndarray,
    mu_star: np.ndarray
) -> np.ndarray:
    """
    Calculate the optimal trade direction.
    
    The gradient ∇D tells us which positions to buy/sell.
    Positive = buy, Negative = sell
    """
    eps = 1e-10
    theta = np.clip(theta, eps, 1 - eps)
    mu_star = np.clip(mu_star, eps, 1 - eps)
    
    # Trade direction: proportional to log ratio
    return np.log(mu_star / theta)


# Example usage
if __name__ == "__main__":
    # Simple YES/NO market example
    # Mispriced: YES=0.30, NO=0.30 (sum=0.60, should be 1.00)
    theta = np.array([0.30, 0.30])
    
    print("Current prices:", theta)
    print("Sum:", np.sum(theta))
    
    # Project onto simplex (sum = 1)
    mu_star = bregman_projection_simplex(theta)
    
    print("\nProjected prices:", mu_star)
    print("Sum:", np.sum(mu_star))
    
    # Calculate arbitrage opportunity
    profit = calculate_arbitrage_profit(theta, mu_star)
    trade = calculate_optimal_trade(theta, mu_star)
    
    print(f"\nKL Divergence (profit proxy): {profit:.4f}")
    print(f"Optimal trade direction: {trade}")
    print(f"Action: BUY YES by {trade[0]:.2f}, BUY NO by {trade[1]:.2f}")
