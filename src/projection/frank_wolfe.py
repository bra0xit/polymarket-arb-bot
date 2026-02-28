"""
Frank-Wolfe Algorithm for Bregman Projection

The Frank-Wolfe (conditional gradient) algorithm solves the Bregman projection
problem without needing to enumerate all vertices of the constraint polytope.

Key insight: Instead of optimizing over all of M at once, Frank-Wolfe builds
the solution iteratively by finding descent directions via linear programs.

Based on: "Arbitrage-Free Combinatorial Market Making via Integer Programming"
"""

import numpy as np
from typing import Callable, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FrankWolfeResult:
    """Result of Frank-Wolfe optimization."""
    solution: np.ndarray
    objective_value: float
    iterations: int
    gap: float
    converged: bool
    active_vertices: list[np.ndarray]


def frank_wolfe(
    theta: np.ndarray,
    linear_oracle: Callable[[np.ndarray], np.ndarray],
    objective: Callable[[np.ndarray], float],
    gradient: Callable[[np.ndarray], np.ndarray],
    max_iter: int = 200,
    tol: float = 1e-6,
    eps: float = 0.1,
    adaptive_eps: bool = True
) -> FrankWolfeResult:
    """
    Frank-Wolfe algorithm for Bregman projection.
    
    Args:
        theta: Current market prices (starting point)
        linear_oracle: Solves min_{z ∈ Z} c·z where Z is the valid outcomes set
        objective: The objective function F(μ) to minimize (Bregman divergence)
        gradient: Gradient of F(μ)
        max_iter: Maximum iterations
        tol: Convergence tolerance
        eps: Contraction parameter for barrier Frank-Wolfe
        adaptive_eps: Whether to adaptively decrease eps
    
    Returns:
        FrankWolfeResult with solution and diagnostics
    """
    n = len(theta)
    
    # Initialize with uniform distribution on simplex
    mu = np.ones(n) / n
    
    # Active set of vertices
    active_vertices = [mu.copy()]
    
    for t in range(max_iter):
        # Compute gradient at current point
        grad = gradient(mu)
        
        # Linear minimization oracle: find descent vertex
        # z_t = argmin_{z ∈ Z} ∇F(μ_t)·z
        z_t = linear_oracle(grad)
        
        # Compute Frank-Wolfe gap (duality gap)
        gap = np.dot(grad, mu - z_t)
        
        # Check convergence
        if gap < tol:
            return FrankWolfeResult(
                solution=mu,
                objective_value=objective(mu),
                iterations=t + 1,
                gap=gap,
                converged=True,
                active_vertices=active_vertices
            )
        
        # Adaptive epsilon adjustment (Barrier Frank-Wolfe)
        if adaptive_eps:
            # g_u is the gap at interior point u
            u = np.ones(n) / n
            g_u = np.dot(gradient(u), u - linear_oracle(gradient(u)))
            
            if gap / (-4 * g_u) < eps and g_u < 0:
                eps = min(gap / (-4 * g_u), eps / 2)
        
        # Line search: find optimal step size
        # For KL divergence, we can use closed-form or backtracking
        alpha = line_search(mu, z_t, objective, max_alpha=1.0)
        
        # Update: μ_{t+1} = (1-α)μ_t + αz_t
        mu = (1 - alpha) * mu + alpha * z_t
        
        # Add vertex to active set
        active_vertices.append(z_t.copy())
    
    return FrankWolfeResult(
        solution=mu,
        objective_value=objective(mu),
        iterations=max_iter,
        gap=gap,
        converged=False,
        active_vertices=active_vertices
    )


def line_search(
    mu: np.ndarray,
    direction: np.ndarray,
    objective: Callable[[np.ndarray], float],
    max_alpha: float = 1.0,
    num_points: int = 20
) -> float:
    """
    Simple line search to find optimal step size.
    
    For Bregman divergence, the optimal step can sometimes be computed
    analytically, but grid search is more robust.
    """
    best_alpha = 0.0
    best_obj = objective(mu)
    
    for i in range(1, num_points + 1):
        alpha = (i / num_points) * max_alpha
        mu_new = (1 - alpha) * mu + alpha * direction
        obj_new = objective(mu_new)
        
        if obj_new < best_obj:
            best_obj = obj_new
            best_alpha = alpha
    
    return best_alpha


def simplex_linear_oracle(gradient: np.ndarray) -> np.ndarray:
    """
    Linear oracle for the probability simplex.
    
    Solves: min_{z ∈ Δ} c·z where Δ = {z : Σz = 1, z ≥ 0}
    Solution: Put all weight on the smallest component.
    """
    n = len(gradient)
    z = np.zeros(n)
    z[np.argmin(gradient)] = 1.0
    return z


def binary_market_oracle(gradient: np.ndarray) -> np.ndarray:
    """
    Linear oracle for binary markets where YES + NO = 1.
    
    Returns the vertex of the simplex that minimizes the gradient.
    For binary markets, this is either [1, 0] or [0, 1].
    """
    if gradient[0] < gradient[1]:
        return np.array([1.0, 0.0])
    else:
        return np.array([0.0, 1.0])


def kl_objective(theta: np.ndarray, eps: float = 1e-10):
    """Create KL divergence objective function."""
    def objective(mu):
        mu = np.clip(mu, eps, 1 - eps)
        t = np.clip(theta, eps, 1 - eps)
        return np.sum(mu * np.log(mu / t))
    return objective


def kl_gradient(theta: np.ndarray, eps: float = 1e-10):
    """Create gradient of KL divergence."""
    def gradient(mu):
        mu = np.clip(mu, eps, 1 - eps)
        t = np.clip(theta, eps, 1 - eps)
        return np.log(mu / t) + 1
    return gradient


# Example usage
if __name__ == "__main__":
    # Example: Binary market with mispricing
    # YES = 0.35, NO = 0.35 (sum = 0.70, arbitrage opportunity!)
    theta = np.array([0.35, 0.35])
    
    print("="*50)
    print("Frank-Wolfe Bregman Projection Example")
    print("="*50)
    print(f"\nCurrent prices: YES=${theta[0]:.3f}, NO=${theta[1]:.3f}")
    print(f"Sum: ${np.sum(theta):.3f} (should be $1.00)")
    print(f"Mispricing: ${1 - np.sum(theta):.3f}")
    
    # Create objective and gradient
    objective = kl_objective(theta)
    gradient = kl_gradient(theta)
    
    # Run Frank-Wolfe
    result = frank_wolfe(
        theta=theta,
        linear_oracle=simplex_linear_oracle,
        objective=objective,
        gradient=gradient,
        max_iter=100,
        tol=1e-8
    )
    
    print(f"\n--- Results ---")
    print(f"Converged: {result.converged}")
    print(f"Iterations: {result.iterations}")
    print(f"Final gap: {result.gap:.2e}")
    print(f"\nProjected prices: YES=${result.solution[0]:.3f}, NO=${result.solution[1]:.3f}")
    print(f"Sum: ${np.sum(result.solution):.3f}")
    print(f"Objective (KL divergence): {result.objective_value:.4f}")
    
    # Calculate arbitrage profit
    profit = 1 - np.sum(theta)  # Simple case
    print(f"\nArbitrage profit per $1 wagered: ${profit:.3f} ({profit*100:.1f}%)")
