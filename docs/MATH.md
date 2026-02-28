# The Math Behind Polymarket Arbitrage

Based on research from arXiv:2508.03474v1 and arXiv:1606.02825v2.

## Why Simple Math Fails

### The Naive Approach
```
YES price = $0.48
NO price = $0.52
Sum = $1.00 ✓ No arbitrage
```

This works for **single-condition markets**. But most profitable arbitrage is in **multi-condition** and **cross-market** opportunities.

### The Dependency Problem

Consider two markets:
1. "Will Trump win Pennsylvania?" (YES/NO)
2. "Will Republicans win Pennsylvania by 5+ points?" (YES/NO)

Both sum to $1.00 individually. But there's a **logical dependency**: if Republicans win by 5+ points, Trump must win PA.

This creates exploitable mispricing even when individual markets look correct.

## The Marginal Polytope

For n conditions, there are 2^n possible price combinations but only n valid outcomes (exactly one condition resolves TRUE).

**Valid payoff vectors:**
```
Z = {φ(ω) : ω ∈ Ω}
```

Where φ(ω) is a binary vector showing which condition is TRUE in outcome ω.

**Arbitrage-free prices must lie in the marginal polytope:**
```
M = conv(Z)
```

Anything outside M is exploitable.

### Scale Problem
- NCAA 2010 tournament: 63 games, 2^63 possible outcomes
- 2024 US election: 17,218 conditions, 1,576 dependent market pairs

Brute force is impossible. We need smart algorithms.

## Integer Programming Solution

Instead of enumerating outcomes, describe valid sets with linear constraints:

```
Z = {z ∈ {0,1}^I : A^T × z ≥ b}
```

Three linear constraints can replace 16,384 brute force checks.

## Bregman Projection

Finding arbitrage is one problem. Calculating the **optimal exploiting trade** is another.

### The Right Distance Metric

Euclidean distance treats all price movements equally. But market prices represent **implied probabilities** using logarithmic cost functions (LMSR).

The Bregman divergence respects this:

```
D(μ||θ) = R(μ) + C(θ) - θ·μ
```

For LMSR, this becomes the **KL divergence**:

```
D(μ||θ) = Σ μ_i × ln(μ_i / θ_i)
```

### The Key Result

**Maximum guaranteed profit from any trade equals the Bregman divergence:**

```
max_δ [min_ω (δ·φ(ω) - C(θ+δ) + C(θ))] = D(μ*||θ)
```

Where μ* is the Bregman projection of θ onto M.

## Frank-Wolfe Algorithm

Computing Bregman projection directly is intractable (exponentially many vertices).

Frank-Wolfe builds the solution iteratively:

```
1. Start with small set of known vertices Z_0
2. For iteration t:
   a. Solve convex optimization over conv(Z_{t-1})
   b. Find new descent vertex via integer program
   c. Add to active set: Z_t = Z_{t-1} ∪ {z_t}
   d. Compute convergence gap
   e. Stop if gap ≤ ε
```

Even after 100 iterations, you're only tracking 100 vertices instead of 2^63.

### Barrier Frank-Wolfe

Standard Frank-Wolfe assumes bounded gradients. For LMSR:
```
∇R(μ) = ln(μ) + 1
```

As μ → 0, gradient → -∞. Solution: optimize over a contracted polytope:
```
M' = (1-ε)M + εu
```

Adaptively decrease ε as iterations progress.

## Execution Constraints

### Non-Atomic Problem

Polymarket uses a CLOB. Your arbitrage plan:
```
Buy YES at $0.30 ✓
Price updates
Buy NO at $0.78 ✗ (was $0.30)
Total: $1.08, Payout: $1.00
Loss: -$0.08
```

### Volume-Weighted Average Price (VWAP)

Don't assume instant fills. Calculate expected execution price:
```
VWAP = Σ(price_i × volume_i) / Σ(volume_i)
```

### Speed Hierarchy

- Retail: ~2,650ms (API → matching → block → propagation)
- Sophisticated: ~2,040ms (WebSocket → pre-calc → direct RPC → parallel)

That 600ms difference is often the entire opportunity window.

## Results (Apr 2024 - Apr 2025)

| Category | Extracted |
|----------|-----------|
| Single condition (buy both < $1) | $5,899,287 |
| Single condition (sell both > $1) | $4,682,075 |
| Market rebalancing (buy all YES) | $11,092,286 |
| Market rebalancing (sell all YES) | $612,189 |
| Market rebalancing (buy all NO) | $17,307,114 |
| Combinatorial (cross-market) | $95,634 |
| **Total** | **$39,688,585** |

Top trader: $2,009,632 from 4,049 trades (~$496 average).

## References

1. "Unravelling the Probabilistic Forest: Arbitrage in Prediction Markets" (arXiv:2508.03474v1)
2. "Arbitrage-Free Combinatorial Market Making via Integer Programming" (arXiv:1606.02825v2)
3. Polymarket CLOB API documentation
4. Gurobi Optimizer for integer programming
