# CDOpt Official Examples

Use this reference for CDOpt implementation-template notes after the model and solver route are reviewed. For official problem statements and corresponding solving code, read `few_shots/cdopt_official_pairs.md`.

Sources:

- Official examples directory: https://github.com/cdopt/cdopt.github.io/tree/main/docs/examples
- Official source artifacts: https://github.com/cdopt/cdopt.github.io/tree/main/docs/_sources/examples
- Rendered examples: https://cdopt.github.io/examples/example_scipy.html

## How To Use

Keep two files separate:

1. **Problem-Code Pairs:** read the matched pair in `few_shots/cdopt_official_pairs.md`.
2. **Implementation Templates:** use official code structure as an implementation reference after the model is reviewed.

Do not treat a template as proof that the model is correct. Use this as an implementation template, not as an automatically approved model.

For rendered documentation pages, prefer `docs/_sources/examples/<name>.ipynb` or `.md` as the paired source artifact.

## Official Example Index

| HTML file | Title | Primary use |
| --- | --- | --- |
| `example_scipy.html` | Optimization via SciPy | Category overview |
| `dictionary_learning.html` | Dictionary Learning | Problem-code pair plus Stiefel/Torch/SciPy template |
| `dictionary_learning_jax.html` | Dictionary Learning Accelerated by JIT | Problem-code pair plus Stiefel/JAX/JIT template |
| `nonlinear_eigenvalue.html` | Discretized 1D Kohn-Sham Equation | Problem-code pair plus Stiefel/NumPy/manual-derivative template |
| `nearest_correlation_estimation.html` | Low-Rank Nearest Correlation Estimation | Problem-code pair plus Oblique/Torch/SciPy template |
| `bose_einstein_condensates.html` | Bose-Einstein Condensates | Problem-code pair plus Sphere/NumPy template |
| `symplectic_eigenvalue.html` | Symplectic Eigenvalue Problem | Problem-code pair plus Symplectic-Stiefel/Torch template |
| `example_torch.html` | Training Neural Networks with Manifold Constraints via PyTorch | Category overview |
| `LeNet_orth.html` | Training LeNet with Constrained Convolution Kernels | PyTorch constrained convolution template |
| `rnn_single_layer.html` | Training Single-Layer RNN with Constrained Weights | PyTorch constrained RNN template |
| `rnn_multi_layer.html` | Training Multi-Layer RNN with Constrained Weights | PyTorch constrained RNN template |
| `rnn_lstm.html` | Training LSTM with Constrained Weights | PyTorch constrained LSTM template |
| `sine_sequence.html` | Time Sequence Prediction with Orthogonality Constrained LSTM | PyTorch sequence-training template |
| `distributed_linear_basic.html` | Distributed Training for A Simple Network by Distributed RPC Framework | Distributed PyTorch template |
| `distributed_rnn_basic.html` | Distributed Training for RNN with Constrained Weights | Distributed PyTorch RNN template |
| `example_jax.html` | Training Neural Networks with Manifold Constraints via JAX and FLAX | Category overview |
| `LeNet_orth_jax.html` | Training LeNet with Constrained Convolution Kernels by JAX and FLAX | JAX/FLAX constrained convolution template |

## Implementation Templates

### Template: SciPy Wrapper Around CDOpt Problem

Use for `dictionary_learning.html`, `nearest_correlation_estimation.html`, `bose_einstein_condensates.html`, and `symplectic_eigenvalue.html`.

```python
import time

import cdopt
import numpy as np
import scipy as sp

# Choose one manifold constructor from the official example:
# cdopt.manifold_torch.stiefel_torch(...)
# cdopt.manifold_torch.oblique_torch(...)
# cdopt.manifold_np.sphere_np(...)
# cdopt.manifold_torch.symp_stiefel_torch(...)
M = build_manifold()

def obj_fun(X):
    return objective_value_from_reviewed_model(X)

problem_obj = cdopt.core.problem(M, obj_fun, beta="auto")
cdf_fun_np = problem_obj.cdf_fun_vec_np
cdf_grad_np = problem_obj.cdf_grad_vec_np
x0 = problem_obj.Xinit_vec_np

started = time.time()
result = sp.optimize.minimize(
    cdf_fun_np,
    x0,
    jac=cdf_grad_np,
    method="L-BFGS-B",
    options={"maxiter": 50, "gtol": 1e-6},
)
elapsed_seconds = time.time() - started
```

### Template: NumPy Stiefel With Manual Derivatives

Use for `nonlinear_eigenvalue.html`, where objective, gradient, and Hessian-vector products are part of the reference pattern.

```python
import cdopt
import numpy as np
import scipy as sp

M = cdopt.manifold_np.stiefel_np((n, p))

def obj_fun(X):
    return reviewed_objective_value(X)

def obj_grad(X):
    return reviewed_euclidean_gradient(X)

def obj_hvp(X, D):
    return reviewed_hessian_vector_product(X, D)

problem_obj = cdopt.core.problem(
    M,
    obj_fun,
    obj_grad=obj_grad,
    obj_hvp=obj_hvp,
    beta=30,
)
```

### Template: JAX Stiefel With JIT Comparison

Use for `dictionary_learning_jax.html`.

```python
import cdopt
import jax
import jax.numpy as jnp
import scipy as sp

jax.config.update("jax_enable_x64", True)
M = cdopt.manifold_jax.stiefel_jax((n, n))

def obj_fun(X):
    return reviewed_jax_objective(X)

problem_jit = cdopt.core.problem(M, obj_fun, beta="auto", enable_jit=True)
problem_nojit = cdopt.core.problem(M, obj_fun, beta="auto", enable_jit=False)

x0 = M.init_point()
_ = problem_jit.grad(x0.reshape(-1))  # warm up before timing
```

### Template: PyTorch Neural Network With Constrained Layers

Use for `LeNet_orth.html`, `rnn_single_layer.html`, `rnn_multi_layer.html`, `rnn_lstm.html`, and `sine_sequence.html`.

```python
import cdopt
import torch
import torch.nn as nn
import torch.nn.functional as F

from cdopt.manifold_torch import stiefel_torch
from cdopt.nn.modules import Conv2d_cdopt, Linear_cdopt, get_quad_penalty

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        # Pass the manifold CLASS (not an instance) plus a penalty_param that
        # weights the constraint-dissolving quadratic penalty.
        self.conv1 = Conv2d_cdopt(1, 6, 5, manifold_class=stiefel_torch, penalty_param=0.05)
        self.conv2 = Conv2d_cdopt(6, 16, 5, manifold_class=stiefel_torch, penalty_param=0.05)
        self.fc = nn.Linear(256, 10)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.conv1(x)), 2)
        x = F.max_pool2d(F.relu(self.conv2(x)), 2)
        x = torch.flatten(x, 1)
        return F.log_softmax(self.fc(x), dim=1)

model = Net()
# Add the aggregated quadratic penalty across all constrained layers.
loss = F.nll_loss(model(batch_x), batch_y) + get_quad_penalty(model)
```

The official examples expose concrete CDOpt layer wrappers such as
`Conv2d_cdopt`, `Linear_cdopt`, and `RNN_cdopt`. An alternative is to wrap a
plain `nn.Conv2d`/`nn.Linear` with
`cdopt.nn.utils.set_constraints.set_constraint_dissolving(layer, 'weight', manifold_class=stiefel_torch, penalty_param=0.05)`.
`get_quad_penalty(model)` sums each constrained layer's `quad_penalty()`, which
also serves as a feasibility proxy.

### Template: PyTorch Constrained RNN/LSTM

Use for `rnn_single_layer.html`, `rnn_multi_layer.html`, `rnn_lstm.html`, and
`sine_sequence.html`.

```python
import torch
import torch.nn as nn

from cdopt.manifold_torch import stiefel_torch
from cdopt.nn import LSTM_cdopt, RNN_cdopt, get_quad_penalty

class VanillaRNN(nn.Module):
    def __init__(self, batch_size, input_size, hidden_size, output_size):
        super().__init__()
        self.batch_size = batch_size
        self.hidden_size = hidden_size
        self.rnn = RNN_cdopt(
            input_size,
            hidden_size,
            manifold_class=stiefel_torch,
            penalty_param=0.2,
        )
        self.head = nn.Linear(hidden_size, output_size)

    def forward(self, sequences):
        # sequences: (batch, seq_len, input_size) -> (seq_len, batch, input_size)
        x = sequences.permute(1, 0, 2)
        hidden = torch.zeros(1, self.batch_size, self.hidden_size, device=x.device, dtype=x.dtype)
        _, hidden = self.rnn(x, hidden)
        return self.head(hidden.squeeze(0))

class LSTMClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size, bidirectional=True):
        super().__init__()
        self.lstm = LSTM_cdopt(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True,
            bidirectional=bidirectional,
            manifold_class=stiefel_torch,
            penalty_param=0.5,
        )
        width = hidden_size * (2 if bidirectional else 1)
        self.head = nn.Linear(width, output_size)

    def forward(self, sequences):
        batch = sequences.size(0)
        layers = self.lstm.num_layers * (2 if self.lstm.bidirectional else 1)
        hidden = torch.zeros(layers, batch, self.lstm.hidden_size, device=sequences.device, dtype=sequences.dtype)
        cell = torch.zeros(layers, batch, self.lstm.hidden_size, device=sequences.device, dtype=sequences.dtype)
        output, _ = self.lstm(sequences, (hidden, cell))
        return self.head(output[:, -1, :])

# In the training loop:
# loss = criterion(logits, labels) + get_quad_penalty(model)
# feas = model.rnn.quad_penalty()  # or model.lstm.quad_penalty()
```

Multi-layer RNN and sine-sequence LSTM pages reuse the same pattern with
different depth or sequence-prediction heads. Distributed RPC examples are not
smoke tests.

### Template: JAX/FLAX Neural Network With Constrained Layers

Use for `LeNet_orth_jax.html`.

```python
import cdopt
import jax
import jax.numpy as jnp
from flax import linen as nn

from cdopt.manifold_jax import stiefel_jax
from cdopt.linen import Conv_cdopt, Dense_cdopt

class CNN(nn.Module):
    @nn.compact
    def __call__(self, x):
        # CDOpt linen layers take the manifold CLASS and return
        # (output, quad_penalty); thread the penalty out to the loss.
        x, quad_penalty = Conv_cdopt(
            features=32, kernel_size=(3, 3), manifold_class=stiefel_jax
        )(x)
        x = nn.relu(x)
        x = nn.avg_pool(x, window_shape=(2, 2), strides=(2, 2))
        x = x.reshape((x.shape[0], -1))
        x = nn.Dense(features=10)(x)
        return x, quad_penalty

# In the train step:
# logits, quad_penalty = CNN().apply({"params": params}, batch_x)
# loss = cross_entropy(logits, batch_y) + 0.05 * quad_penalty
```

### Template: Distributed PyTorch CDOpt

Use for `distributed_linear_basic.html` and `distributed_rnn_basic.html` only after the user explicitly asks for distributed execution.

```python
import torch
import torch.distributed as dist

from cdopt.manifold_torch import oblique_torch, stiefel_torch

def build_worker_model():
    stiefel = stiefel_torch((rows, cols), device=device, dtype=dtype)
    oblique = oblique_torch((rows, cols), device=device, dtype=dtype)
    return model_with_reviewed_constrained_layers(stiefel, oblique)

def train_worker(rank, world_size):
    dist.init_process_group("gloo", rank=rank, world_size=world_size)
    try:
        model = build_worker_model()
        train_with_approved_dataset(model)
    finally:
        dist.destroy_process_group()
```

Distributed templates are not smoke tests. They require a separate run plan, resource estimate, and approval.
