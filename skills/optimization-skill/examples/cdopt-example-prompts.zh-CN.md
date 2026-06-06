# CDOpt 本地 Problem Description Cards

[English](cdopt-example-prompts.md) | 简体中文

这些 prompts 用本地 Markdown cards 测试 `$optimization-skill`。这些 cards 来自
CDOpt 官方 examples 的 Problem Description。coding agent 的主流程应该先读本地
card；官方 URL 只作为来源标记，不作为主要 prompt 入口。

使用模板：

```text
使用 $optimization-skill。

读取这个本地 Problem Description card：
examples/cdopt/problem-descriptions/<card-name>.md

把 card 里的 `## Prompt Body` 当成官方 Problem Description prompt。手动测试时，
可以把这个本地 Problem Description card 里的 Prompt Body 复制进会话。

先建立 modeling checkpoint。模型 review 之后，才使用对应的 Implementation
Template reference：
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. 未经批准，不要安装依赖或运行代码。
```

本地 cards 是 prompt materials。实现模板单独放在
`skills/optimization-skill/references/cdopt_official_examples.md`。

## Prompt 0：本地 Card Map

```text
使用 $optimization-skill。

读取这里的 CDOpt 本地 Problem Description cards：
examples/cdopt/problem-descriptions/

每张 card 的 `## Prompt Body` 是独立建模测试 prompt；`## Expected Modeling
Signals` 只用于 review。没有本地 card 的页面，要归类为 Implementation Template
examples，而不是 prompt examples。

Do not copy the official code verbatim. 不要安装包，不要运行代码。
```

## Prompt 1：Dictionary Learning

本地 card：
`examples/cdopt/problem-descriptions/dictionary-learning.md`

来源：
https://cdopt.github.io/examples/dictionary_learning.html#problem-description

```text
使用 $optimization-skill。

读取这个本地 Problem Description card：
examples/cdopt/problem-descriptions/dictionary-learning.md

把 `## Prompt Body` 当成官方 Problem Description prompt。先建立 modeling
checkpoint，再选择 CDOpt / SciPy / L-BFGS-B 路线。

模型 review 之后，使用：
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. 未经批准，不要安装依赖或运行代码。
```

## Prompt 2：Dictionary Learning Accelerated By JIT

本地 card：
`examples/cdopt/problem-descriptions/dictionary-learning-jax.md`

来源：
https://cdopt.github.io/examples/dictionary_learning_jax.html#problem-description

```text
使用 $optimization-skill。

读取这个本地 Problem Description card：
examples/cdopt/problem-descriptions/dictionary-learning-jax.md

把 `## Prompt Body` 当成官方 Problem Description prompt。先建立 modeling
checkpoint，再判断 JAX/JIT 是否适合这次 tiny run。

模型 review 之后，使用：
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. 未经批准，不要安装依赖或运行代码。
```

## Prompt 3：Discretized 1D Kohn-Sham Equation

本地 card：
`examples/cdopt/problem-descriptions/kohn-sham-1d.md`

来源：
https://cdopt.github.io/examples/nonlinear_eigenvalue.html#problem-description

```text
使用 $optimization-skill。

读取这个本地 Problem Description card：
examples/cdopt/problem-descriptions/kohn-sham-1d.md

把 `## Prompt Body` 当成官方 Problem Description prompt。先建立 modeling
checkpoint，再 review derivatives 或 solver code。

模型 review 之后，使用：
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. 未经批准，不要安装依赖或运行代码。
```

## Prompt 4：Low-Rank Nearest Correlation Estimation

本地 card：
`examples/cdopt/problem-descriptions/nearest-correlation.md`

来源：
https://cdopt.github.io/examples/nearest_correlation_estimation.html#problem-description

```text
使用 $optimization-skill。

读取这个本地 Problem Description card：
examples/cdopt/problem-descriptions/nearest-correlation.md

把 `## Prompt Body` 当成官方 Problem Description prompt。先建立 modeling
checkpoint，再选择 oblique-manifold 路线。

模型 review 之后，使用：
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. 未经批准，不要安装依赖或运行代码。
```

## Prompt 5：Bose-Einstein Condensates

本地 card：
`examples/cdopt/problem-descriptions/bose-einstein-condensates.md`

来源：
https://cdopt.github.io/examples/bose_einstein_condensates.html#problem-description

```text
使用 $optimization-skill。

读取这个本地 Problem Description card：
examples/cdopt/problem-descriptions/bose-einstein-condensates.md

把 `## Prompt Body` 当成官方 Problem Description prompt。先建立 modeling
checkpoint，再选择 sphere-manifold 路线。

模型 review 之后，使用：
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. 未经批准，不要安装依赖或运行代码。
```

## Prompt 6：Symplectic Eigenvalue Problem

本地 card：
`examples/cdopt/problem-descriptions/symplectic-eigenvalue.md`

来源：
https://cdopt.github.io/examples/symplectic_eigenvalue.html#problem-description

```text
使用 $optimization-skill。

读取这个本地 Problem Description card：
examples/cdopt/problem-descriptions/symplectic-eigenvalue.md

把 `## Prompt Body` 当成官方 Problem Description prompt。先建立 modeling
checkpoint，再选择 symplectic-Stiefel 路线。

模型 review 之后，使用：
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. 未经批准，不要安装依赖或运行代码。
```

## Prompt 7：PyTorch LeNet Template Check

来源：
https://cdopt.github.io/examples/LeNet_orth.html

```text
使用 $optimization-skill。

这个 CDOpt 官方页面没有独立的本地 Problem Description card：
https://cdopt.github.io/examples/LeNet_orth.html

请把它归类为 Implementation Template example。使用：
skills/optimization-skill/references/cdopt_official_examples.md

解释在改写 PyTorch constrained-layer code 之前，还需要什么单独的
modeling-test prompt。

Do not copy the official code verbatim. 未经批准，不要安装依赖、下载数据或训练。
```

## Prompt 8：JAX/FLAX LeNet Template Check

来源：
https://cdopt.github.io/examples/LeNet_orth_jax.html

```text
使用 $optimization-skill。

这个 CDOpt 官方页面没有独立的本地 Problem Description card：
https://cdopt.github.io/examples/LeNet_orth_jax.html

请把它归类为 Implementation Template example。使用：
skills/optimization-skill/references/cdopt_official_examples.md

解释在改写 JAX/FLAX constrained-layer code 之前，还需要什么单独的
modeling-test prompt。

Do not copy the official code verbatim. 未经批准，不要安装依赖、下载数据或训练。
```

## Prompt 9：RNN Template Check

来源：
- https://cdopt.github.io/examples/rnn_single_layer.html
- https://cdopt.github.io/examples/rnn_multi_layer.html
- https://cdopt.github.io/examples/rnn_lstm.html
- https://cdopt.github.io/examples/sine_sequence.html

```text
使用 $optimization-skill。

这些 CDOpt 官方页面是 implementation-template examples，不是独立的本地 Problem
Description cards：
- https://cdopt.github.io/examples/rnn_single_layer.html
- https://cdopt.github.io/examples/rnn_multi_layer.html
- https://cdopt.github.io/examples/rnn_lstm.html
- https://cdopt.github.io/examples/sine_sequence.html

使用 `skills/optimization-skill/references/cdopt_official_examples.md` 对
constrained recurrent-layer template 做分类。

解释在改写 PyTorch RNN/LSTM code 之前，还需要什么单独的 modeling-test prompt。

Do not copy the official code verbatim. 未经批准，不要安装依赖、下载数据或训练。
```
