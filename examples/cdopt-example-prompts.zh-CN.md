# CDOpt 示例 Prompts

[English](cdopt-example-prompts.md) | 简体中文

这些 prompts 是用于测试 `$optimization-skill` 处理 CDOpt 风格优化任务的示例用户请求。

它们是应用级 examples，不是 CDOpt 安装测试。对于 CDOpt 路由，agent 应该先运行或提出运行 `skills/optimization-skill/references/solver_catalog.md` 中描述的安装后 manifold smoke test，然后再使用这里的某个 prompt 测试具体问题 workflow。

使用方式：在 Skill 已安装且可发现之后，把一个完整的 `text` 代码块复制到新的 agent 会话中。

## Prompt 0：提取 CDOpt Example Map

```text
使用 $optimization-skill。

我想把一组 CDOpt 风格的优化 examples 用作这个 Skill 的问题陈述。请把 problem map 提取成三组：

1. 通过 SciPy 做优化
2. 通过 PyTorch 训练带流形约束的神经网络
3. 通过 JAX 和 FLAX 训练带流形约束的神经网络

对每个 example，请报告：
- 问题标题；
- 使用的优化/流形概念；
- 需要的后端包；
- 运行规模类别：light、medium、heavy 或 distributed；
- 数据是 synthetic、代码生成、下载得到，还是没有数据。

不要安装包，也不要运行代码。最后推荐我应该最先手动尝试的两个 examples，并说明原因。
```

## Prompt 1：SciPy / Dictionary Learning

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Dictionary Learning" 问题。

目标：
构建并可选运行一个小规模 CPU 版的正交 dictionary learning 问题。使用 Stiefel 约束，并用 SciPy 优化器求解 CDOpt constraint-dissolving objective。

问题：
给定 Y in R^(m x n)，求解
minimize_X  -sum((Y X)^4)
subject to X^T X = I_n.
把 X 视为一个 n x n Stiefel 变量。

数据：
- 使用代码生成的 synthetic Bernoulli-Gaussian 风格数据。
- 快速运行使用 seed=0, n=6, m=10*n^2, theta=0.3, dtype float64, CPU only。
- 按照问题设置的精神生成 Y：normal quantile samples，并用 theta 控制的 sparsity pattern 做 mask。
- 不要假设存在任何外部数据文件。

实现要求：
- 检查 cdopt、torch、numpy、scipy 是否可用。
- 如果依赖缺失，停止并告诉我需要的精确安装命令，但不要在未批准时安装。
- 在 `.local/cdopt-runs/dictionary_learning_torch_scipy/` 下生成本地脚本。
- 使用 `cdopt.manifold_torch.stiefel_torch((n, n), device=cpu, dtype=torch.float64)`。
- 创建 `cdopt.core.problem(M, obj_fun, beta='auto')`。
- 先路由到 SciPy L-BFGS-B；如果开销很小，可以可选比较 CG。
- 报告 fval、迭代数、函数评估次数、gradient norm/stationarity、通过 manifold feasibility evaluator 得到的 feasibility，以及 CPU time。

运行策略：
先生成 model summary 和脚本。安装依赖或运行超过 tiny CPU run 的任务前，请先问我。
```

## Prompt 2：SciPy / Dictionary Learning Accelerated by JAX JIT

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Dictionary Learning Accelerated by JIT" 问题。

目标：
把同一个 dictionary-learning 模型路由到 CDOpt 的 JAX 后端，并比较 JIT 与 non-JIT 的 gradient evaluation。

问题：
给定 Y in R^(m x n)，求解
minimize_X  -sum((Y X)^4)
subject to X^T X = I_n,
其中 X 是 n x n Stiefel 变量。

数据：
- 只使用 synthetic data。
- 快速 CPU 运行使用 seed=0, n=6, m=10*n^2, theta=0.3。
- 用 JAX/NumPy 生成 Bernoulli-Gaussian 风格的 Y，并转换为 jax.numpy。
- 如果可用，启用 JAX 64-bit mode。

实现要求：
- 检查 cdopt、jax、jaxlib、numpy、scipy 是否可用。
- 如果 JAX 或 CDOpt 缺失，不要自动安装；说明依赖缺口。
- 在 `.local/cdopt-runs/dictionary_learning_jax_jit/` 下生成本地脚本。
- 使用 `cdopt.manifold_jax.stiefel_jax((n, n))`。
- 构建两个 CDOpt problems：一个 `enable_jit=True`，一个 `enable_jit=False`，使用相同 beta。
- 计时前先 warm up JIT。
- 在相同初始点上比较两个版本的 gradient evaluation time。
- 如果依赖存在，再用 JIT-enabled problem 跑一个 tiny L-BFGS-B run。

报告：
- 模型和数据摘要；
- JIT vs non-JIT timing；
- solver status、fval、stationarity、feasibility、CPU time；
- 如果 JAX version、cdopt API、64-bit mode 或 scipy bridge 失败，请做 failure diagnosis。

运行策略：
安装依赖前先问我。如果依赖存在，只运行 tiny CPU version。
```

## Prompt 3：SciPy / Discretized 1D Kohn-Sham Equation

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Discretized 1D Kohn-Sham Equation" 问题。

目标：
求解一个 NumPy/SciPy sparse-matrix Stiefel 问题，其中 agent 需要手动提供 objective、gradient 和 Hessian-vector product。

问题：
求解简化的 1D Kohn-Sham 模型
minimize_X  0.5 * tr(X^T L X) + alpha/4 * rho^T L^{-1} rho
subject to X^T X = I_p,
其中 rho = diag(X X^T)，L 是三对角矩阵，对角线为 2，副对角线为 -1。

数据：
- 无外部数据。
- 使用 scipy.sparse.diags 生成 L。
- 快速运行使用 n=120, p=4, alpha=1。较大规模使用 n=1000, p=10。

实现要求：
- 检查 cdopt、numpy、scipy 是否可用。
- 在 `.local/cdopt-runs/kohn_sham_1d/` 下生成本地脚本。
- 使用 `cdopt.manifold_np.stiefel_np((n, p))`。
- 使用 scipy sparse operations 和 `spsolve` 实现 objective、gradient 和 Hessian-vector product。
- 创建 `cdopt.core.problem(M, obj_fun, obj_grad=obj_grad, obj_hvp=obj_hvp, beta=30)`。
- 先路由到 SciPy L-BFGS-B；如果开销很小，比较 CG 和 trust-krylov/trust-ncg。
- 对快速本地运行使用紧凑但合理的 max iterations。

报告：
- objective 公式和约束；
- 生成的 sparse matrix shape 和 nnz；
- solver 表格：fval、nit、nfev、stationarity、feasibility、CPU time；
- 对 sparse solve、Hessian-vector product 或 trust-region 失败做诊断。

运行策略：
不要自动安装依赖。如果估计运行时间超过 tiny CPU run，请先问我。
```

## Prompt 4：SciPy / Low-Rank Nearest Correlation Estimation

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Low-Rank Nearest Correlation Estimation" 问题。

目标：
用生成的 symmetric target matrix 和 weight matrix 求解一个 Oblique-manifold formulation。

问题：
nearest correlation matrix 问题为
minimize_W  0.5 * || H o (W - G) ||_F^2
subject to diag(W)=1 and rank(W)<=p.
使用低秩分解 W = X X^T，求解
minimize_X  0.5 * || H o (X X^T - G) ||_F^2
subject to ||x_i||_2 = 1 for every row x_i.
把 X in R^(n x p) 视为 Oblique-manifold 变量。

数据：
- 无外部数据。
- 快速 CPU run 使用 seed=0, n=80, p=8。完整规模使用 n=1000, p=40。
- 生成 Y ~ N(0,1) in R^(n x p)，对 Y 做 row-normalize，设置 G = Y Y^T + 0.5 * noise，并设置 H 的元素均匀分布在 [0.5, 1]。
- 使用 torch float64 on CPU。

实现要求：
- 检查 cdopt、torch、numpy、scipy 是否可用。
- 在 `.local/cdopt-runs/nearest_correlation_oblique/` 下生成本地脚本。
- 使用 `cdopt.manifold_torch.oblique_torch((n, p), device=cpu, dtype=torch.float64)`。
- 创建 `cdopt.core.problem(M, obj_fun, beta='auto')`。
- 先路由到 SciPy L-BFGS-B；如果开销很小，可选比较 CG。

报告：
- factorized model，以及 row-normalized X 如何强制 diag(W)=1；
- 数据生成摘要；
- fval、nit、nfev、stationarity、feasibility、CPU time；
- 对 memory blow-up、dense matrix size 或 torch/scipy bridge 问题做 failure diagnosis。

运行策略：
安装依赖前先问我。除非我明确批准 full size，否则使用 tiny CPU size。
```

## Prompt 5：SciPy / Bose-Einstein Condensates

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Bose-Einstein Condensates" 问题。

目标：
求解一个 sphere-constrained nonlinear eigenvalue-style optimization problem。

问题：
使用真实的简化 BEC 模型
minimize_x  0.5 * x^T A x + alpha * sum(x_i^4)
subject to ||x||_2 = 1.
把 x 视为 sphere 上的向量。

数据：
- 无外部数据。
- 快速 CPU run 使用 seed=0, n=200, alpha=1。较大规模使用 n=1000。
- 使用 A = ones((n, n)) 以匹配简单数据构造，除非你找到更稳定的 tiny variant 并解释原因。

实现要求：
- 检查 cdopt、numpy、scipy、autograd 是否可用。
- 在 `.local/cdopt-runs/bose_einstein_sphere/` 下生成本地脚本。
- 使用 `cdopt.manifold_np.sphere_np((n, 1))`。
- 构建 `cdopt.core.problem(M, obj_fun, beta='auto')`。
- 路由到 SciPy L-BFGS-B，并可选比较 CG。

报告：
- objective 和 sphere constraint；
- CDOpt 是否使用 autograd，还是需要手动 derivatives；
- solver status、fval、stationarity、feasibility、CPU time；
- 对 autograd、shape 或 sphere feasibility 问题做诊断。

运行策略：
安装依赖前先问我。如果依赖已存在，只运行 tiny CPU version。
```

## Prompt 6：SciPy / Symplectic Eigenvalue Problem

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Symplectic Eigenvalue Problem" 问题。

目标：
识别并路由一个 symplectic Stiefel-manifold optimization problem。

问题：
给定 positive definite matrix L，求解
minimize_X  0.5 * tr(X^T L X)
subject to X^T Q_m X = Q_p,
其中 Q_k 是 canonical symplectic matrix。
使用 CDOpt 的 symplectic Stiefel manifold implementation，不要手写约束。

数据：
- 无外部数据。
- 快速 CPU run 使用 seed=0, n=80, p=4。较大规模使用 n=1000, p=10。
- 按照问题设置的构造，生成 diagonal 为 3、off-diagonal 为 -1 的 tridiagonal sparse matrix L。
- 使用 torch float64 on CPU。

实现要求：
- 检查 cdopt、torch、numpy、scipy 是否可用。
- 在 `.local/cdopt-runs/symplectic_eigenvalue/` 下生成本地脚本。
- 使用 `cdopt.manifold_torch.symp_stiefel_torch((n, p), device=cpu, dtype=torch.float64)`。
- 构建 `cdopt.core.problem(M, obj_fun, beta='auto')`。
- 先路由到 SciPy L-BFGS-B；只有在 Hessian-vector products 稳定时，才可选比较 trust-region solver。

报告：
- symplectic constraint 的解释；
- sparse L 构造细节；
- solver 表格：fval、nit、nfev、stationarity、feasibility、CPU time；
- 对 torch sparse、symplectic manifold API 或 shape mismatch 失败做诊断。

运行策略：
除非我明确批准，不要使用 GPU。依赖安装或长运行前先问我。
```

## Prompt 7：PyTorch / LeNet with Constrained Convolution Kernels

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Training LeNet with Constrained Convolution Kernels" 问题。

目标：
使用 CDOpt neural-network layers 和 quadratic penalty reporting，但默认不要求完整 MNIST training run。

Example concept：
在 MNIST 上训练 LeNet-style CNN，其中 convolution kernels 通过 CDOpt 的 Stiefel manifold support 加约束。loss 是 negative log-likelihood 加 `get_quad_penalty(model)`。

数据：
- 问题设置会用 torchvision 下载 MNIST。
- 第一次运行不要下载数据。使用 synthetic one-batch smoke run：
  - seed=1
  - batch_size=8
  - images shape `(8, 1, 28, 28)`
  - labels shape `(8,)`，整数类别 0..9。
- 只把真实 MNIST 5-epoch run 作为需要批准的可选 follow-up。

实现要求：
- 检查 cdopt、torch、torchvision 是否可用。
- 在 `.local/cdopt-runs/lenet_constrained_conv/` 下生成本地脚本。
- 使用 `Conv2d_cdopt(..., manifold_class=stiefel_torch, penalty_param=0.05)` 构建 LeNet-like model with constrained convolution layers。
- 同时提到另一个可选模式：对普通 `nn.Conv2d` weights 使用 `set_constraint_dissolving`，但只实现其中一种路径。
- 如果依赖存在，正好在 synthetic data 上运行一次 forward/backward/optimizer step。
- 默认使用 CPU。

报告：
- model architecture summary；
- 如果运行了，报告 synthetic batch loss before/after one optimizer step；
- `get_quad_penalty(model)` 以及可用时的 per-layer penalty；
- feasibility/penalty interpretation；
- 对 missing cdopt.nn modules、API drift、torchvision 或 CUDA assumptions 做诊断。

运行策略：
除非我批准，不要下载 MNIST 或运行 5 epochs。不要自动安装依赖。
```

## Prompt 8：PyTorch / Single-Layer RNN with Constrained Weights

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Training Single-Layer RNN with Constrained Weights" 问题。

目标：
通过 `RNN_cdopt` 使用 constrained recurrent layer，并体现 Skill 能把较重的 MNIST training notebook 降级成安全的 one-batch problem-solving request。

Example concept：
把 MNIST 行视为序列使用 RNN。使用 batch_size=64, input_size=28, hidden_size=150, output_size=10, `RNN_cdopt(..., manifold_class=stiefel_torch, penalty_param=0.2)`，CrossEntropy loss 加 `get_quad_penalty(model)`。

数据：
- 第一次运行不要下载 MNIST。
- 使用 synthetic image-row data：
  - seed=1234
  - batch_size=8
  - input tensor shape `(8, 28, 28)`
  - labels shape `(8,)`，整数类别 0..9。

实现要求：
- 检查 cdopt、torch、numpy 是否可用。
- 在 `.local/cdopt-runs/rnn_single_layer/` 下生成本地脚本。
- 构建一个 `VanillaRNN_MNIST` 风格模型，使用 `RNN_cdopt`。
- 如果依赖存在，在 CPU 上运行一次 forward/backward/Adam step。
- 把 penalty 纳入 loss。

报告：
- 28x28 图像作为序列的解释；
- output shape 和 hidden state shape；
- loss、penalty 和 one-step status；
- 对 RNN_cdopt API drift、hidden-state shape errors 或 missing torch 做诊断。

运行策略：
不要下载 MNIST 或训练 epochs，除非我批准。不要自动安装依赖。
```

## Prompt 9：PyTorch / Multi-Layer RNN with Constrained Weights

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Training Multi-Layer RNN with Constrained Weights" 问题。

目标：
构建更深的 constrained recurrent model，并验证 Skill 能把它和更轻的 single-layer smoke run 区分开。

Example concept：
使用 `RNN_cdopt(input_size, hidden_size, layer_size, batch_first=True, nonlinearity='tanh' or 'relu', manifold_class=stiefel_torch, penalty_param=0.2)`，后接 linear classifier。问题设置在 MNIST 上训练。

数据：
- 默认不要下载 MNIST。
- 使用 synthetic data：
  - seed=1234
  - batch_size=8
  - input_size=28
  - sequence length=28
  - hidden_size=32 for quick run
  - layer_size=2
  - output_size=10
  - labels shape `(8,)`。

实现要求：
- 检查 cdopt、torch、numpy 是否可用。
- 在 `.local/cdopt-runs/rnn_multi_layer/` 下生成本地脚本。
- 构建一个 `MultilayerRNN_MNIST` 风格模型，使用 `RNN_cdopt`。
- 如果依赖存在，在 CPU 上运行一次 forward/backward/Adam step。
- 把 `get_quad_penalty(model)` 纳入 loss。

报告：
- 为什么这是 medium integration run，而不是 first smoke run；
- output shape、loss、penalty 和 one-step status；
- 对 batch_first、hidden-state shape、layer count 和 penalty 问题做诊断。

运行策略：
不要下载 MNIST 或 multi-epoch training，除非我批准。没有批准不要安装依赖。
```

## Prompt 10：PyTorch / LSTM with Constrained Weights

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Training LSTM with Constrained Weights" 问题。

目标：
使用 `LSTM_cdopt` 处理 constrained recurrent weights，包括 bidirectional hidden/cell state shape handling。

Example concept：
使用 MNIST row sequences、bidirectional multi-layer LSTM，以及 CrossEntropy loss 加 `get_quad_penalty(model)`。它包含 full training 前的 one-pass batch check。

数据：
- 默认不要下载 MNIST。
- 使用 synthetic one-batch data：
  - seed=1234
  - batch_size=8
  - input tensor shape `(8, 28, 28)`
  - labels shape `(8,)`
  - input_size=28
  - hidden_size=32 for quick run
  - layer_size=2
  - output_size=10
  - bidirectional=True。

实现要求：
- 检查 cdopt、torch、numpy 是否可用。
- 在 `.local/cdopt-runs/lstm_constrained_weights/` 下生成本地脚本。
- 使用 `LSTM_cdopt(..., batch_first=True, bidirectional=True, manifold_class=stiefel_torch, penalty_param=0.5)` 构建 `LSTM_MNIST` 风格模型。
- 如果依赖存在，在 CPU 上运行一次 forward/backward/Adam step。
- 把 `get_quad_penalty(model)` 纳入 loss。

报告：
- hidden state 和 cell state shapes；
- output shape；
- loss 和 penalty；
- one-step optimizer result；
- 对 bidirectional dimension mismatch、CDOpt LSTM API drift 或 missing torch 做诊断。

运行策略：
不要下载 MNIST 或训练所有 images，除非我批准。不要自动安装依赖。
```

## Prompt 11：PyTorch / Sine Sequence Prediction with Orthogonality-Constrained LSTM

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Time Sequence Prediction with Orthogonality Constrained LSTM" 问题。

目标：
使用 `LSTMCell_cdopt` 求解一个完全 synthetic 的 sequence-prediction task，包含 tiny training loop 和 result parsing。

Example concept：
生成带随机 phase offsets 的 sine waves。训练两个 constrained LSTMCell layers 来预测下一个 sine value，并可选预测 future values。使用 T=20, L=1000, N=100, hidden size 51, total_steps=15, LBFGS，以及 MSE 加 `get_quad_penalty(seq)`。

数据：
- 无外部数据。
- 使用 seed=2。
- 快速运行使用 T=20, L=120, N=20, hidden_size=16, total_steps=3, future=40。
- 通过给 range(L) 添加 random phase offsets 生成 `x`，然后 `data = sin(x / T)`。

实现要求：
- 检查 cdopt、torch、numpy、matplotlib 是否可用。Matplotlib 是可选的；不可用时不要失败。
- 在 `.local/cdopt-runs/sine_sequence_lstmcell/` 下生成本地脚本。
- 构建一个 `Sequence` model，包含两个使用 `stiefel_torch` 和 penalty_param=0.01 的 `LSTMCell_cdopt` layers，后接 linear output layer。
- 在 CPU 上用 double precision 训练。
- 如果稳定，使用 LBFGS；如果 LBFGS closure 失败，则 fallback 到 Adam 做 smoke run，并诊断 fallback。

报告：
- data shape 和 train/validation split；
- per-step validation loss；
- penalty contribution；
- future prediction 是否运行；
- 对 dtype、LBFGS closure、hidden-state 或 penalty 失败做诊断。

运行策略：
安装依赖前先问我。除非我批准 full settings，否则只使用 tiny synthetic run。
```

## Prompt 12：PyTorch Distributed / RNN with Constrained Weights

```text
使用 $optimization-skill。

请为 "Distributed Training for RNN with Constrained Weights" 问题分析并准备一个安全的 CDOpt run plan。

目标：
准备问题，但不要立即执行 distributed training。提取 solver/model pattern 并生成安全 run plan，因为这个 example 会启动 RPC workers 和 multiprocessing。

Example concept：
问题设置构建一个 distributed RNN model，包含 remote embedding/decoder modules 和 local `LSTM_cdopt` constrained recurrent layer。它使用 PyTorch RPC、distributed autograd 和 `DistributedOptimizer`。数据为 random token data。

数据：
- Synthetic random token data 由代码生成。
- Tiny shapes 包括 batch=5, ntoken=7, ninp=2, nhid=3, nindices=6, nlayers=4，以及包含 trainer 和 parameter server 的 2-process setup。

要求输出：
- 生成 modeling and execution checkpoint，而不是直接运行。
- 识别所有风险操作：multiprocessing、RPC initialization、ports、distributed autograd、backend compatibility 和 CUDA assumptions。
- 在 `.local/cdopt-runs/distributed_rnn_rpc/` 下生成本地脚本 proposal，但除非我批准，不要运行。
- 包含一个 one-process non-distributed smoke-run alternative，只验证 synthetic data 上的 `LSTM_cdopt` 加 `get_quad_penalty`。

报告：
- distributed architecture summary；
- 为什么这是 heavy integration run；
- proposed exact command 和 timeout；
- port conflict、RPC backend、process spawn、CUDA 和 API drift 的 failure diagnostics checklist。

运行策略：
没有明确批准，不要运行 distributed RPC。不要自动安装依赖。
```

## Prompt 13：PyTorch Distributed / Simple Network by RPC Framework

```text
使用 $optimization-skill。

请为 "Distributed Training for A Simple Network by Distributed RPC Framework" 问题分析并准备一个安全的 CDOpt run plan。

目标：
默认不执行，准备一个安全的问题 prompt，因为它组合了 DistributedDataParallel、RPC、multiprocessing 和 remote modules。

Example concept：
模型包含：
- parameter server 上通过 `RemoteModule` 管理的 sparse embedding component；
- 通过 DDP 在 trainers 上复制的 dense local component；
- 使用 `cdopt.nn.Linear_cdopt(16, 8, manifold_class=stiefel_torch, penalty_param=0.5)` 的 CDOpt constrained dense layer；
- CrossEntropy loss 加 `get_quad_penalty(model)`。

数据：
- Synthetic random embedding indices、offsets 和 random class targets。
- 常量包括 NUM_EMBEDDINGS=100 和 EMBEDDING_DIM=16。

要求输出：
- 生成 modeling and execution checkpoint，而不是直接运行。
- 解释 worker roles：trainers、master、parameter server。
- 识别风险：multiprocessing、`gloo` process group、RPC backend ports、CUDA `.cuda(rank)` assumptions、DDP availability 和 cleanup。
- 在 `.local/cdopt-runs/distributed_linear_rpc/` 下生成本地脚本 proposal，但除非我批准，不要运行。
- 另外生成一个 CPU-only single-process fallback smoke run，用 synthetic dense inputs 验证 `Linear_cdopt`。

报告：
- architecture summary；
- 如果批准，给出 exact proposed command 和 timeout；
- expected metrics 或 printed penalty；
- failure diagnosis checklist。

运行策略：
没有明确批准，不要启动 RPC/DDP processes。不要自动安装依赖。
```

## Prompt 14：JAX/FLAX / LeNet with Constrained Convolution Kernels

```text
使用 $optimization-skill。

请用 CDOpt 设置并求解 "Training LeNet with Constrained Convolution Kernels by JAX and FLAX" 问题。

目标：
使用 JAX/FLAX route 处理 neural-network constraints，同时默认避免完整 TFDS/MNIST training run。

Example concept：
构建一个 Flax CNN，其中第一个 convolution 使用 `Conv_cdopt(..., manifold_class=stiefel_jax)`，loss 包含 CDOpt quadratic penalty。问题设置通过 TensorFlow Datasets 加载 MNIST，使用 optax SGD、learning_rate=0.05、momentum=0.9、num_epochs=10、batch_size=64 训练。

数据：
- 默认不要下载 TFDS/MNIST。
- 使用 synthetic image data：
  - seed=0
  - batch_size=8
  - image shape `(8, 28, 28, 1)`
  - labels shape `(8,)`，类别 0..9。

实现要求：
- 检查 cdopt、jax、flax、optax 是否可用。
- 在 `.local/cdopt-runs/lenet_jax_flax_constrained_conv/` 下生成本地脚本。
- 构建一个 compact Flax CNN，包含一个 `Conv_cdopt` layer、一个 normal conv 或 dense layer，以及 classifier。
- 如果依赖存在，运行一个 JIT-compiled train step。
- 把 penalty 纳入 loss 并报告 metrics。

报告：
- model architecture 和 constrained layer；
- synthetic batch 的 loss、accuracy、penalty/feasibility metric；
- JIT compilation 是否成功；
- 对 missing flax/optax/tfds、API drift、device/CPU fallback 或 JAX shape issues 做诊断。

运行策略：
除非我批准，不要运行 TFDS download 或 10 epochs。不要自动安装依赖。
```

## Prompt 15：Natural-Language Model Extraction Stress Prompt

```text
使用 $optimization-skill。

我想要一个基于 CDOpt examples 的 natural-language-to-model 请求。我不会给你代码。请构建模型，生成 tiny reproducible dataset，选择后端，生成 solver code，并告诉我你会运行什么。

问题：
求解一个 orthogonal dictionary-learning problem。变量 X 是 square and orthogonal。目标函数是 YX 的 negative fourth power sum。数据矩阵 Y 应该使用 sparse Bernoulli-Gaussian pattern 合成。使用小规模 CPU-only 问题。

要求：
- 推断约束是 Stiefel/orthogonal manifold constraint。
- 在代码前先生成 structured problem specification。
- 使用 n=6, m=360, theta=0.3, seed=0。
- 优先使用 CDOpt plus SciPy L-BFGS-B。
- 生成可以在没有外部数据文件时运行的代码。
- 把 solver result 解析成 fval、stationarity、feasibility、iteration count、function evaluations 和 CPU time。
- 包含 missing CDOpt、missing torch/scipy、infeasible shape、unsupported manifold API 和 solver non-convergence 的 failure diagnosis branches。

运行策略：
没有批准不要安装依赖。如果环境尚未 ready，运行前先问我。
```

## Prompt 16：Failure-Diagnosis Stress Prompt

```text
使用 $optimization-skill。

使用 CDOpt 风格的问题族，但有意设计一个 failure-diagnosis workflow。选择 Dictionary Learning 问题，生成一个 tiny script，先检查依赖和 API，再求解。

脚本必须：
- verify imports for cdopt, torch, numpy, scipy；
- 在可用时打印版本；
- 验证 `cdopt.core.problem` 存在；
- 验证 `cdopt.manifold_torch.stiefel_torch` 存在；
- 使用 seed=0, n=4, m=40, theta=0.3 生成 tiny synthetic Y matrix；
- 构建 Stiefel problem；
- 运行至多 20 次 L-BFGS-B iterations；
- 始终打印一个结构化 JSON-like result，字段包括：
  status, success, objective, stationarity, feasibility, nit, nfev, elapsed_seconds, diagnosis。

如果任何步骤失败，不要静默崩溃。返回 diagnosis，说明失败属于 dependency、API drift、shape/modeling、solver，还是 environment/runtime。

不要自动安装包。
```
