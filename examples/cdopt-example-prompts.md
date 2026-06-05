# CDOpt Example Prompts

English | [简体中文](cdopt-example-prompts.zh-CN.md)

These prompts are example user requests for exercising `$optimization-skill` on CDOpt-style optimization tasks.

They are application-level examples, not CDOpt installation tests. For CDOpt routes, the agent should first run or propose the post-install manifold smoke test described in `skills/optimization-skill/references/solver_catalog.md`, then use one of these prompts to test a concrete problem workflow.

Use pattern: copy one complete `text` block into a fresh agent session after the Skill is installed and discoverable.

## Prompt 0: Extract CDOpt Example Map

```text
Use $optimization-skill.

I want to use a set of CDOpt-style optimization examples as problem statements for this Skill. Extract the problem map into three groups:

1. Optimization via SciPy
2. Training neural networks with manifold constraints via PyTorch
3. Training neural networks with manifold constraints via JAX and FLAX

For each example, report:
- problem title;
- optimization/manifold concept being used;
- required backend packages;
- runtime class: light, medium, heavy, or distributed;
- whether the data is synthetic, generated in code, downloaded, or absent.

Do not install packages or run code. End by recommending the first two examples I should try manually and why.
```

## Prompt 1: SciPy / Dictionary Learning

```text
Use $optimization-skill.

Set up and solve the "Dictionary Learning" problem with CDOpt.

Goal:
Build and optionally run a small CPU version of the orthogonal dictionary learning problem. Use a Stiefel constraint and solve the CDOpt constraint-dissolving objective with SciPy optimizers.

Problem:
Given Y in R^(m x n), solve
minimize_X  -sum((Y X)^4)
subject to X^T X = I_n.
Treat X as an n x n Stiefel variable.

Data:
- Use synthetic Bernoulli-Gaussian style data generated in code.
- For a quick run, use seed=0, n=6, m=10*n^2, theta=0.3, dtype float64, CPU only.
- Generate Y with the same spirit as the problem setup: normal quantile samples masked by a sparsity pattern controlled by theta.
- Do not assume any external data file.

Implementation requirements:
- Check whether cdopt, torch, numpy, scipy are available.
- If dependencies are missing, stop and tell me the exact install command you would need, but do not install without approval.
- Generate a local script under `.local/cdopt-runs/dictionary_learning_torch_scipy/`.
- Use `cdopt.manifold_torch.stiefel_torch((n, n), device=cpu, dtype=torch.float64)`.
- Create `cdopt.core.problem(M, obj_fun, beta='auto')`.
- Route to SciPy L-BFGS-B first; optionally compare CG if cheap.
- Report fval, iterations, function evaluations, gradient norm/stationarity, feasibility via the manifold feasibility evaluator, and CPU time.

Run policy:
First produce the model summary and the generated script. Ask me before installing dependencies or running anything longer than a tiny CPU run.
```

## Prompt 2: SciPy / Dictionary Learning Accelerated by JAX JIT

```text
Use $optimization-skill.

Set up and solve the "Dictionary Learning Accelerated by JIT" problem with CDOpt.

Goal:
Route the same dictionary-learning model through CDOpt's JAX backend and compare JIT vs non-JIT gradient evaluation.

Problem:
Given Y in R^(m x n), solve
minimize_X  -sum((Y X)^4)
subject to X^T X = I_n,
where X is an n x n Stiefel variable.

Data:
- Synthetic data only.
- Use seed=0, n=6 for a quick CPU run, m=10*n^2, theta=0.3.
- Generate Y as Bernoulli-Gaussian style data in JAX/NumPy and convert to jax.numpy.
- Enable 64-bit JAX mode if available.

Implementation requirements:
- Check whether cdopt, jax, jaxlib, numpy, scipy are available.
- If JAX or CDOpt is missing, do not install automatically; explain the dependency gap.
- Generate a local script under `.local/cdopt-runs/dictionary_learning_jax_jit/`.
- Use `cdopt.manifold_jax.stiefel_jax((n, n))`.
- Build two CDOpt problems: one with `enable_jit=True`, one with `enable_jit=False`, same beta.
- Warm up JIT before timing.
- Compare gradient evaluation time for both variants on the same initial point.
- Then solve a tiny L-BFGS-B run with the JIT-enabled problem if dependencies are present.

Report:
- model and data summary;
- JIT vs non-JIT timing;
- solver status, fval, stationarity, feasibility, CPU time;
- failure diagnosis if JAX version, cdopt API, 64-bit mode, or scipy bridge fails.

Run policy:
Ask before installing dependencies. If dependencies exist, run only the tiny CPU version.
```

## Prompt 3: SciPy / Discretized 1D Kohn-Sham Equation

```text
Use $optimization-skill.

Set up and solve the "Discretized 1D Kohn-Sham Equation" problem with CDOpt.

Goal:
Solve a NumPy/SciPy sparse-matrix Stiefel problem where the agent must supply objective, gradient, and Hessian-vector product manually.

Problem:
Solve the simplified 1D Kohn-Sham model
minimize_X  0.5 * tr(X^T L X) + alpha/4 * rho^T L^{-1} rho
subject to X^T X = I_p,
where rho = diag(X X^T), L is tridiagonal with 2 on the diagonal and -1 on off-diagonals.

Data:
- No external data.
- Generate L with scipy.sparse.diags.
- For quick run use n=120, p=4, alpha=1. Use a larger n=1000, p=10.

Implementation requirements:
- Check cdopt, numpy, scipy availability.
- Generate a local script under `.local/cdopt-runs/kohn_sham_1d/`.
- Use `cdopt.manifold_np.stiefel_np((n, p))`.
- Implement objective, gradient, and Hessian-vector product using scipy sparse operations and `spsolve`.
- Create `cdopt.core.problem(M, obj_fun, obj_grad=obj_grad, obj_hvp=obj_hvp, beta=30)`.
- Route to SciPy L-BFGS-B first; if cheap, compare CG and trust-krylov/trust-ncg.
- Use tight but reasonable max iterations for a quick local run.

Report:
- objective formula and constraint;
- generated sparse matrix shape and nnz;
- solver table with fval, nit, nfev, stationarity, feasibility, CPU time;
- diagnosis for sparse solve, Hessian-vector product, or trust-region failures.

Run policy:
Do not install dependencies automatically. Ask before running if the estimated run time is more than a tiny CPU run.
```

## Prompt 4: SciPy / Low-Rank Nearest Correlation Estimation

```text
Use $optimization-skill.

Set up and solve the "Low-Rank Nearest Correlation Estimation" problem with CDOpt.

Goal:
Solve an Oblique-manifold formulation with a generated symmetric target matrix and weight matrix.

Problem:
The nearest correlation matrix problem is
minimize_W  0.5 * || H o (W - G) ||_F^2
subject to diag(W)=1 and rank(W)<=p.
Use the low-rank factorization W = X X^T and solve
minimize_X  0.5 * || H o (X X^T - G) ||_F^2
subject to ||x_i||_2 = 1 for every row x_i.
Treat X in R^(n x p) as an Oblique-manifold variable.

Data:
- No external data.
- Use seed=0, n=80, p=8 for the quick CPU run. Use n=1000, p=40.
- Generate Y ~ N(0,1) in R^(n x p), row-normalize Y, set G = Y Y^T + 0.5 * noise, and set H with entries uniformly in [0.5, 1].
- Use torch float64 on CPU.

Implementation requirements:
- Check cdopt, torch, numpy, scipy availability.
- Generate a local script under `.local/cdopt-runs/nearest_correlation_oblique/`.
- Use `cdopt.manifold_torch.oblique_torch((n, p), device=cpu, dtype=torch.float64)`.
- Create `cdopt.core.problem(M, obj_fun, beta='auto')`.
- Route to SciPy L-BFGS-B first and optionally CG if cheap.

Report:
- factorized model and how diag(W)=1 is enforced by row-normalized X;
- data-generation summary;
- fval, nit, nfev, stationarity, feasibility, CPU time;
- failure diagnosis for memory blow-up, dense matrix size, or torch/scipy bridge issues.

Run policy:
Ask before installing dependencies. Use the tiny CPU size unless I explicitly approve the full size.
```

## Prompt 5: SciPy / Bose-Einstein Condensates

```text
Use $optimization-skill.

Set up and solve the "Bose-Einstein Condensates" problem with CDOpt.

Goal:
Solve a sphere-constrained nonlinear eigenvalue-style optimization problem.

Problem:
Use the real simplified BEC model
minimize_x  0.5 * x^T A x + alpha * sum(x_i^4)
subject to ||x||_2 = 1.
Treat x as a vector on the sphere.

Data:
- No external data.
- Use seed=0, n=200, alpha=1 for the quick CPU run. Use n=1000.
- Use A = ones((n, n)) to match the simple data construction, unless you find a more stable tiny variant and explain it.

Implementation requirements:
- Check cdopt, numpy, scipy, autograd availability.
- Generate a local script under `.local/cdopt-runs/bose_einstein_sphere/`.
- Use `cdopt.manifold_np.sphere_np((n, 1))`.
- Build `cdopt.core.problem(M, obj_fun, beta='auto')`.
- Route to SciPy L-BFGS-B and optionally CG.

Report:
- objective and sphere constraint;
- whether autograd is used by CDOpt or manual derivatives are needed;
- solver status, fval, stationarity, feasibility, CPU time;
- diagnosis for autograd, shape, or sphere feasibility issues.

Run policy:
Ask before installing dependencies. Run only the tiny CPU version if dependencies are already present.
```

## Prompt 6: SciPy / Symplectic Eigenvalue Problem

```text
Use $optimization-skill.

Set up and solve the "Symplectic Eigenvalue Problem" problem with CDOpt.

Goal:
Recognize and route a symplectic Stiefel-manifold optimization problem.

Problem:
Given a positive definite matrix L, solve
minimize_X  0.5 * tr(X^T L X)
subject to X^T Q_m X = Q_p,
where Q_k is the canonical symplectic matrix.
Use CDOpt's symplectic Stiefel manifold implementation rather than hand-coding the constraint.

Data:
- No external data.
- Use seed=0, n=80, p=4 for the quick CPU run. Use n=1000, p=10.
- Generate L as a tridiagonal sparse matrix with diagonal 3 and off-diagonal -1, following the problem setup's construction.
- Use torch float64 on CPU.

Implementation requirements:
- Check cdopt, torch, numpy, scipy availability.
- Generate a local script under `.local/cdopt-runs/symplectic_eigenvalue/`.
- Use `cdopt.manifold_torch.symp_stiefel_torch((n, p), device=cpu, dtype=torch.float64)`.
- Build `cdopt.core.problem(M, obj_fun, beta='auto')`.
- Route to SciPy L-BFGS-B first; optionally compare a trust-region solver only if Hessian-vector products are stable.

Report:
- symplectic constraint interpretation;
- sparse L construction details;
- solver table with fval, nit, nfev, stationarity, feasibility, CPU time;
- diagnosis for torch sparse, symplectic manifold API, or shape mismatch failures.

Run policy:
Do not use GPU unless I explicitly approve it. Ask before dependency installation or long runs.
```

## Prompt 7: PyTorch / LeNet with Constrained Convolution Kernels

```text
Use $optimization-skill.

Set up and solve the "Training LeNet with Constrained Convolution Kernels" problem with CDOpt.

Goal:
Use CDOpt neural-network layers and quadratic penalty reporting, without requiring a full MNIST training run by default.

Example concept:
Train a LeNet-style CNN on MNIST where convolution kernels are constrained through CDOpt's Stiefel manifold support. The loss is negative log-likelihood plus `get_quad_penalty(model)`.

Data:
- Problem setup downloads MNIST with torchvision.
- For the first run, do not download data. Use a synthetic one-batch smoke run:
  - seed=1
  - batch_size=8
  - images shape `(8, 1, 28, 28)`
  - labels shape `(8,)` with integer classes 0..9.
- Only propose the real MNIST 5-epoch run as an optional follow-up requiring approval.

Implementation requirements:
- Check cdopt, torch, torchvision availability.
- Generate a local script under `.local/cdopt-runs/lenet_constrained_conv/`.
- Build a LeNet-like model with constrained convolution layers using `Conv2d_cdopt(..., manifold_class=stiefel_torch, penalty_param=0.05)`.
- Also mention the alternative pattern using `set_constraint_dissolving` on normal `nn.Conv2d` weights, but implement only one path.
- Run exactly one forward/backward/optimizer step on synthetic data if dependencies are present.
- Use CPU by default.

Report:
- model architecture summary;
- synthetic batch loss before/after one optimizer step if run;
- `get_quad_penalty(model)` and per-layer penalty if available;
- feasibility/penalty interpretation;
- diagnosis for missing cdopt.nn modules, API drift, torchvision, or CUDA assumptions.

Run policy:
Do not download MNIST or run 5 epochs unless I approve. Do not install dependencies automatically.
```

## Prompt 8: PyTorch / Single-Layer RNN with Constrained Weights

```text
Use $optimization-skill.

Set up and solve the "Training Single-Layer RNN with Constrained Weights" problem with CDOpt.

Goal:
Use a constrained recurrent layer through `RNN_cdopt` and the Skill's ability to reduce a heavy MNIST training notebook into a safe one-batch problem-solving request.

Example concept:
Use an RNN over MNIST rows. Use batch_size=64, input_size=28, hidden_size=150, output_size=10, `RNN_cdopt(..., manifold_class=stiefel_torch, penalty_param=0.2)`, CrossEntropy loss plus `get_quad_penalty(model)`.

Data:
- Do not download MNIST for the first run.
- Use synthetic image-row data:
  - seed=1234
  - batch_size=8
  - input tensor shape `(8, 28, 28)`
  - labels shape `(8,)`, integer classes 0..9.

Implementation requirements:
- Check cdopt, torch, numpy availability.
- Generate a local script under `.local/cdopt-runs/rnn_single_layer/`.
- Build a `VanillaRNN_MNIST`-style model with `RNN_cdopt`.
- Run one forward/backward/Adam step on CPU if dependencies are present.
- Include the penalty in the loss.

Report:
- sequence interpretation of 28x28 images;
- output shape and hidden state shape;
- loss, penalty, and one-step status;
- diagnosis for RNN_cdopt API drift, hidden-state shape errors, or missing torch.

Run policy:
Do not download MNIST or train epochs unless I approve. Do not install dependencies automatically.
```

## Prompt 9: PyTorch / Multi-Layer RNN with Constrained Weights

```text
Use $optimization-skill.

Set up and solve the "Training Multi-Layer RNN with Constrained Weights" problem with CDOpt.

Goal:
Build a deeper constrained recurrent model and verify that the Skill distinguishes this from the lighter single-layer smoke run.

Example concept:
Use `RNN_cdopt(input_size, hidden_size, layer_size, batch_first=True, nonlinearity='tanh' or 'relu', manifold_class=stiefel_torch, penalty_param=0.2)` followed by a linear classifier. The problem setup trains on MNIST.

Data:
- Do not download MNIST by default.
- Use synthetic data:
  - seed=1234
  - batch_size=8
  - input_size=28
  - sequence length=28
  - hidden_size=32 for quick run
  - layer_size=2
  - output_size=10
  - labels shape `(8,)`.

Implementation requirements:
- Check cdopt, torch, numpy availability.
- Generate a local script under `.local/cdopt-runs/rnn_multi_layer/`.
- Build a `MultilayerRNN_MNIST`-style model with `RNN_cdopt`.
- Run one forward/backward/Adam step on CPU if dependencies are present.
- Include `get_quad_penalty(model)` in the loss.

Report:
- why this is a medium integration run rather than a first smoke run;
- output shape, loss, penalty, and one-step status;
- diagnosis for batch_first, hidden-state shape, layer count, and penalty issues.

Run policy:
No MNIST download or multi-epoch training unless I approve. No dependency installation without approval.
```

## Prompt 10: PyTorch / LSTM with Constrained Weights

```text
Use $optimization-skill.

Set up and solve the "Training LSTM with Constrained Weights" problem with CDOpt.

Goal:
Use `LSTM_cdopt` with constrained recurrent weights, including bidirectional hidden/cell state shape handling.

Example concept:
Use MNIST row sequences, a bidirectional multi-layer LSTM, and CrossEntropy loss plus `get_quad_penalty(model)`. It includes a one-pass batch check before full training.

Data:
- Do not download MNIST by default.
- Use synthetic one-batch data:
  - seed=1234
  - batch_size=8
  - input tensor shape `(8, 28, 28)`
  - labels shape `(8,)`
  - input_size=28
  - hidden_size=32 for quick run
  - layer_size=2
  - output_size=10
  - bidirectional=True.

Implementation requirements:
- Check cdopt, torch, numpy availability.
- Generate a local script under `.local/cdopt-runs/lstm_constrained_weights/`.
- Build an `LSTM_MNIST`-style model using `LSTM_cdopt(..., batch_first=True, bidirectional=True, manifold_class=stiefel_torch, penalty_param=0.5)`.
- Run one forward/backward/Adam step on CPU if dependencies are present.
- Include `get_quad_penalty(model)` in the loss.

Report:
- hidden state and cell state shapes;
- output shape;
- loss and penalty;
- one-step optimizer result;
- diagnosis for bidirectional dimension mismatch, CDOpt LSTM API drift, or missing torch.

Run policy:
Do not download MNIST or train all images unless I approve. Do not install dependencies automatically.
```

## Prompt 11: PyTorch / Sine Sequence Prediction with Orthogonality-Constrained LSTM

```text
Use $optimization-skill.

Set up and solve the "Time Sequence Prediction with Orthogonality Constrained LSTM" problem with CDOpt.

Goal:
Solve a fully synthetic sequence-prediction task using `LSTMCell_cdopt`, with a tiny training loop and result parsing.

Example concept:
Generate sine waves with random phase offsets. Train two constrained LSTMCell layers to predict the next sine value and optionally future values. Use T=20, L=1000, N=100, hidden size 51, total_steps=15, LBFGS, and MSE plus `get_quad_penalty(seq)`.

Data:
- No external data.
- Use seed=2.
- For quick run use T=20, L=120, N=20, hidden_size=16, total_steps=3, future=40.
- Generate `x` by adding random phase offsets to range(L), then `data = sin(x / T)`.

Implementation requirements:
- Check cdopt, torch, numpy, matplotlib availability. Matplotlib is optional; do not fail if unavailable.
- Generate a local script under `.local/cdopt-runs/sine_sequence_lstmcell/`.
- Build a `Sequence` model with two `LSTMCell_cdopt` layers using `stiefel_torch` and penalty_param=0.01, followed by a linear output layer.
- Train on CPU with double precision.
- Use LBFGS if stable; fall back to Adam for a smoke run if LBFGS closure fails, and diagnose the fallback.

Report:
- data shape and train/validation split;
- per-step validation loss;
- penalty contribution;
- whether future prediction ran;
- diagnosis for dtype, LBFGS closure, hidden-state, or penalty failures.

Run policy:
Ask before installing dependencies. Use only the tiny synthetic run unless I approve the full settings.
```

## Prompt 12: PyTorch Distributed / RNN with Constrained Weights

```text
Use $optimization-skill.

Analyze and prepare a safe CDOpt run plan for the "Distributed Training for RNN with Constrained Weights" problem.

Goal:
Prepare the problem without executing distributed training immediately. Extract the solver/model pattern and produce a safe run plan, because this example starts RPC workers and multiprocessing.

Example concept:
The problem setup builds a distributed RNN model with remote embedding/decoder modules and a local `LSTM_cdopt` constrained recurrent layer. It uses PyTorch RPC, distributed autograd, and `DistributedOptimizer`. It trains on random token data.

Data:
- Synthetic random token data generated in code.
- Tiny shapes include batch=5, ntoken=7, ninp=2, nhid=3, nindices=6, nlayers=4, and a 2-process setup with trainer and parameter server.

Required output:
- Produce a modeling and execution checkpoint, not a direct run.
- Identify all risky operations: multiprocessing, RPC initialization, ports, distributed autograd, backend compatibility, and CUDA assumptions.
- Generate a local script proposal under `.local/cdopt-runs/distributed_rnn_rpc/`, but do not run it unless I approve.
- Include a one-process non-distributed smoke-run alternative that only verifies `LSTM_cdopt` plus `get_quad_penalty` on synthetic data.

Report:
- distributed architecture summary;
- why this is a heavy integration run;
- proposed exact command and timeout;
- failure diagnostics checklist for port conflict, RPC backend, process spawn, CUDA, and API drift.

Run policy:
Do not run distributed RPC without explicit approval. Do not install dependencies automatically.
```

## Prompt 13: PyTorch Distributed / Simple Network by RPC Framework

```text
Use $optimization-skill.

Analyze and prepare a safe CDOpt run plan for the "Distributed Training for A Simple Network by Distributed RPC Framework" problem.

Goal:
Prepare a safe safe problem prompt without executing it by default, because it combines DistributedDataParallel, RPC, multiprocessing, and remote modules.

Example concept:
The model has:
- a sparse embedding component on a parameter server via `RemoteModule`;
- a dense local component replicated on trainers through DDP;
- a CDOpt constrained dense layer using `cdopt.nn.Linear_cdopt(16, 8, manifold_class=stiefel_torch, penalty_param=0.5)`;
- CrossEntropy loss plus `get_quad_penalty(model)`.

Data:
- Synthetic random embedding indices, offsets, and random class targets.
- Constants include NUM_EMBEDDINGS=100 and EMBEDDING_DIM=16.

Required output:
- Produce a modeling and execution checkpoint, not a direct run.
- Explain the worker roles: trainers, master, parameter server.
- Identify risks: multiprocessing, `gloo` process group, RPC backend ports, CUDA `.cuda(rank)` assumptions, DDP availability, and cleanup.
- Generate a local script proposal under `.local/cdopt-runs/distributed_linear_rpc/`, but do not run it unless I approve.
- Also generate a CPU-only single-process fallback smoke run for `Linear_cdopt` using synthetic dense inputs.

Report:
- architecture summary;
- exact proposed command and timeout if approved;
- expected metrics or printed penalty;
- failure diagnosis checklist.

Run policy:
Do not start RPC/DDP processes without explicit approval. Do not install dependencies automatically.
```

## Prompt 14: JAX/FLAX / LeNet with Constrained Convolution Kernels

```text
Use $optimization-skill.

Set up and solve the "Training LeNet with Constrained Convolution Kernels by JAX and FLAX" problem with CDOpt.

Goal:
Use the JAX/FLAX route for neural-network constraints, while avoiding a full TFDS/MNIST training run by default.

Example concept:
Build a Flax CNN where the first convolution uses `Conv_cdopt(..., manifold_class=stiefel_jax)` and the loss includes a CDOpt quadratic penalty. The problem setup trains on MNIST loaded through TensorFlow Datasets, with optax SGD, learning_rate=0.05, momentum=0.9, num_epochs=10, batch_size=64.

Data:
- Do not download TFDS/MNIST by default.
- Use synthetic image data:
  - seed=0
  - batch_size=8
  - image shape `(8, 28, 28, 1)`
  - labels shape `(8,)`, classes 0..9.

Implementation requirements:
- Check cdopt, jax, flax, optax availability.
- Generate a local script under `.local/cdopt-runs/lenet_jax_flax_constrained_conv/`.
- Build a compact Flax CNN with one `Conv_cdopt` layer, a normal conv or dense layer, and a classifier.
- Run one JIT-compiled train step if dependencies are present.
- Include penalty in the loss and report metrics.

Report:
- model architecture and constrained layer;
- loss, accuracy, penalty/feasibility metric for the synthetic batch;
- whether JIT compilation succeeded;
- diagnosis for missing flax/optax/tfds, API drift, device/CPU fallback, or JAX shape issues.

Run policy:
Do not run TFDS download or 10 epochs unless I approve. Do not install dependencies automatically.
```

## Prompt 15: Natural-Language Model Extraction Stress Prompt

```text
Use $optimization-skill.

I want a natural-language-to-model request based on CDOpt examples. I will not give you code. Build the model, generate a tiny reproducible dataset, choose a backend, generate solver code, and tell me what you would run.

Problem:
Solve an orthogonal dictionary-learning problem. The variable X is square and orthogonal. The objective is the negative fourth power sum of YX. The data matrix Y should be generated synthetically with a sparse Bernoulli-Gaussian pattern. Use a small CPU-only problem.

Requirements:
- Infer that the constraint is a Stiefel/orthogonal manifold constraint.
- Produce a structured problem specification before code.
- Use n=6, m=360, theta=0.3, seed=0.
- Prefer CDOpt plus SciPy L-BFGS-B.
- Generate code that can run without external data files.
- Parse the solver result into fval, stationarity, feasibility, iteration count, function evaluations, and CPU time.
- Include failure diagnosis branches for missing CDOpt, missing torch/scipy, infeasible shape, unsupported manifold API, and solver non-convergence.

Run policy:
Do not install dependencies without approval. Ask before running if the environment is not already ready.
```

## Prompt 16: Failure-Diagnosis Stress Prompt

```text
Use $optimization-skill.

Use the CDOpt-style problem family, but intentionally design a failure-diagnosis workflow. Pick the Dictionary Learning problem and produce a tiny script that first checks dependencies and APIs before solving.

The script must:
- verify imports for cdopt, torch, numpy, scipy;
- print versions when available;
- verify that `cdopt.core.problem` exists;
- verify that `cdopt.manifold_torch.stiefel_torch` exists;
- generate a tiny synthetic Y matrix with seed=0, n=4, m=40, theta=0.3;
- construct the Stiefel problem;
- run at most 20 L-BFGS-B iterations;
- always print a structured JSON-like result with fields:
  status, success, objective, stationarity, feasibility, nit, nfev, elapsed_seconds, diagnosis.

If anything fails, do not crash silently. Return a diagnosis that says whether the failure is dependency, API drift, shape/modeling, solver, or environment/runtime.

Do not install packages automatically.
```
