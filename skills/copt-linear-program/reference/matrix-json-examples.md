# 矩阵 JSON 补充示例

主规范见 [SKILL.md](../SKILL.md)。以下为**仅矩阵形式**的调用示例，便于复现与自动化脚本。

## 示例 1：最大化 `c^T x`（不等式约束 + 非负变量）

```text
/copt-linear-program
{
  "sense": "max",
  "c": [1, 2, 3],
  "A_ub": [[1,0,2],[0,1,1]],
  "b_ub": [10, 7],
  "bounds": [[0, null], [0, null], [0, null]]
}
```

## 示例 2：最小化 `c^T x`（等式约束 + 非负变量）

```text
/copt-linear-program
{
  "sense": "min",
  "c": [5, 8, 2, 4, 7],
  "A_eq": [
    [1, 0, 2, 1, 3],
    [0, 1, 1, 2, 1],
    [3, 2, 0, 1, 0],
    [1, 1, 1, 1, 1]
  ],
  "b_eq": [200, 150, 250, 100],
  "bounds": [[0, null], [0, null], [0, null], [0, null], [0, null]]
}
```
