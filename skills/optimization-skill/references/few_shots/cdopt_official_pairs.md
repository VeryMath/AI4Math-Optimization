# CDOpt Official Problem-Code Pairs

## Dictionary Learning

source_page: https://github.com/cdopt/cdopt.github.io/blob/main/docs/examples/dictionary_learning.html
source_artifact: https://github.com/cdopt/cdopt.github.io/blob/main/docs/_sources/examples/dictionary_learning.ipynb

### Official problem statement

Given data `y_i = Q z_i`, where `Q` is an unknown orthogonal matrix and `z_i`
are sparse Bernoulli-Gaussian latent vectors, solve the fourth-power model on
the Stiefel manifold

```text
minimize_X    - sum_{i=1}^m || y_i^T X ||_4^4
subject to    X^T X = I.
```

### Official solving code

```python
M = cdopt.manifold_torch.stiefel_torch((n, n), device=device, dtype=dtype)

def obj_fun(X):
    return -torch.norm(torch.matmul(Y, X), p=4) ** 4

problem_test = cdopt.core.problem(M, obj_fun, beta="auto")
cdf_fun_np = problem_test.cdf_fun_vec_np
cdf_grad_np = problem_test.cdf_grad_vec_np
Xinit = problem_test.Xinit_vec_np

out_msg = sp.optimize.minimize(
    cdf_fun_np,
    Xinit,
    method="L-BFGS-B",
    jac=cdf_grad_np,
    options={"disp": None, "maxcor": 10, "ftol": 0, "gtol": 1e-6, "eps": 0e-8},
)
feas = M.Feas_eval(M.v2m(M.array2tensor(out_msg.x)))
stationarity = np.linalg.norm(out_msg["jac"], 2)
result_lbfgs = [out_msg["fun"], out_msg["nit"], out_msg["nfev"], stationarity, feas]

out_msg = sp.optimize.minimize(
    cdf_fun_np,
    Xinit,
    method="CG",
    jac=cdf_grad_np,
    options={"disp": None, "gtol": 1e-6, "eps": 0e-8},
)
feas = M.Feas_eval(M.v2m(M.array2tensor(out_msg.x)))
stationarity = np.linalg.norm(out_msg["jac"], 2)
result_cg = [out_msg["fun"], out_msg["nit"], out_msg["nfev"], stationarity, feas]
```

## Dictionary Learning Accelerated By JIT

source_page: https://github.com/cdopt/cdopt.github.io/blob/main/docs/examples/dictionary_learning_jax.html
source_artifact: https://github.com/cdopt/cdopt.github.io/blob/main/docs/_sources/examples/dictionary_learning_jax.ipynb

### Official problem statement

Use the same dictionary-learning model as above:

```text
minimize_X    - sum_{i=1}^m || y_i^T X ||_4^4
subject to    X^T X = I.
```

### Official solving code

```python
jax.config.update("jax_enable_x64", True)
M = cdopt.manifold_jax.stiefel_jax((n, n))

def obj_fun(X):
    return -jnp.linalg.norm(jnp.matmul(Y, X), ord=4) ** 4

problem_jit = cdopt.core.problem(M, obj_fun, beta="auto", enable_jit=True)
problem_nojit = cdopt.core.problem(M, obj_fun, beta="auto", enable_jit=False)

Xinit = problem_jit.Xinit_vec_np
out_msg = sp.optimize.minimize(
    problem_jit.cdf_fun_vec_np,
    Xinit,
    method="L-BFGS-B",
    jac=problem_jit.cdf_grad_vec_np,
    options={"disp": None, "maxcor": 10, "ftol": 0, "gtol": 1e-6, "eps": 0e-8},
)
```

## Discretized 1D Kohn-Sham Equation

source_page: https://github.com/cdopt/cdopt.github.io/blob/main/docs/examples/nonlinear_eigenvalue.html
source_artifact: https://github.com/cdopt/cdopt.github.io/blob/main/docs/_sources/examples/nonlinear_eigenvalue.ipynb

### Official problem statement

For matrix `L`, parameter `alpha`, and density vector `rho(X)`, solve

```text
minimize_X    0.5 trace(X^T L X) + (alpha / 4) rho(X)^T L^{-1} rho(X)
subject to    X^T X = I_p.
```

### Official solving code

```python
M = cdopt.manifold_np.stiefel_np((n, p))

problem_test = cdopt.core.problem(
    M,
    obj_fun,
    obj_grad=obj_grad,
    obj_hvp=obj_hvp,
    beta=30,
)
cdf_fun_np = problem_test.cdf_fun_vec_np
cdf_grad_np = problem_test.cdf_grad_vec_np
cdf_hvp_np = problem_test.cdf_hvp_vec_np
Xinit = problem_test.Xinit_vec_np

out_msg = sp.optimize.minimize(
    cdf_fun_np,
    Xinit,
    method="L-BFGS-B",
    jac=cdf_grad_np,
    options={"disp": None, "maxcor": 10, "ftol": 0, "gtol": 1e-6, "eps": 0e-8},
)
```

## Low-Rank Nearest Correlation Estimation

source_page: https://github.com/cdopt/cdopt.github.io/blob/main/docs/examples/nearest_correlation_estimation.html
source_artifact: https://github.com/cdopt/cdopt.github.io/blob/main/docs/_sources/examples/nearest_correlation_estimation.ipynb

### Official problem statement

For target matrix `G`, weight matrix `H`, and row vectors `x_i`, solve

```text
minimize_X    0.5 || H o (X X^T - G) ||_F^2
subject to    || x_i ||_2 = 1,    i = 1, ..., n.
```

### Official solving code

```python
M = cdopt.manifold_torch.oblique_torch((n, p), device=device, dtype=dtype)

def obj_fun(X):
    return 0.5 * torch.norm(H * (torch.matmul(X, X.T) - G), p="fro") ** 2

problem_test = cdopt.core.problem(M, obj_fun, beta="auto")
cdf_fun_np = problem_test.cdf_fun_vec_np
cdf_grad_np = problem_test.cdf_grad_vec_np
Xinit = problem_test.Xinit_vec_np

out_msg = sp.optimize.minimize(
    cdf_fun_np,
    Xinit,
    method="L-BFGS-B",
    jac=cdf_grad_np,
    options={"disp": None, "maxcor": 10, "ftol": 0, "gtol": 1e-6, "eps": 0e-8},
)
```

## Bose-Einstein Condensates

source_page: https://github.com/cdopt/cdopt.github.io/blob/main/docs/examples/bose_einstein_condensates.html
source_artifact: https://github.com/cdopt/cdopt.github.io/blob/main/docs/_sources/examples/bose_einstein_condensates.ipynb

### Official problem statement

For real vector `x` on the unit sphere, matrix `A`, and coefficient `alpha`,
solve

```text
minimize_x    0.5 x^T A x + alpha sum_i x_i^4
subject to    || x ||_2 = 1.
```

### Official solving code

```python
M = cdopt.manifold_np.sphere_np((n,))

def obj_fun(x):
    return 0.5 * x.T @ A @ x + alpha * np.sum(x**4)

problem_test = cdopt.core.problem(M, obj_fun, beta="auto")
cdf_fun_np = problem_test.cdf_fun_vec_np
cdf_grad_np = problem_test.cdf_grad_vec_np
Xinit = problem_test.Xinit_vec_np

out_msg = sp.optimize.minimize(
    cdf_fun_np,
    Xinit,
    method="L-BFGS-B",
    jac=cdf_grad_np,
    options={"disp": None, "maxcor": 10, "ftol": 0, "gtol": 1e-6, "eps": 0e-8},
)
```

## Symplectic Eigenvalue Problem

source_page: https://github.com/cdopt/cdopt.github.io/blob/main/docs/examples/symplectic_eigenvalue.html
source_artifact: https://github.com/cdopt/cdopt.github.io/blob/main/docs/_sources/examples/symplectic_eigenvalue.ipynb

### Official problem statement

For symmetric positive definite matrix `L` and canonical symplectic matrices
`J_n` and `J_p`, solve

```text
minimize_X    0.5 trace(X^T L X)
subject to    X^T J_n X = J_p.
```

### Official solving code

```python
M = cdopt.manifold_torch.symp_stiefel_torch(shape, device=device, dtype=dtype)

def obj_fun(X):
    return 0.5 * torch.trace(torch.matmul(X.T, torch.matmul(L, X)))

problem_test = cdopt.core.problem(M, obj_fun, beta="auto")
cdf_fun_np = problem_test.cdf_fun_vec_np
cdf_grad_np = problem_test.cdf_grad_vec_np
Xinit = problem_test.Xinit_vec_np

out_msg = sp.optimize.minimize(
    cdf_fun_np,
    Xinit,
    method="L-BFGS-B",
    jac=cdf_grad_np,
    options={"disp": None, "maxcor": 10, "ftol": 0, "gtol": 1e-6, "eps": 0e-8},
)
```
