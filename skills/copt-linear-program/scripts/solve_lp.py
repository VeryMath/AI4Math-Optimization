"""
用 coptpy 求解标准形 LP：min/max c^T x，s.t. A_ub x <= b_ub，A_eq x == b_eq，变量界 bounds。

依赖：numpy、coptpy（及已配置的 COPT 授权）。
"""

from __future__ import annotations

import numpy as np
import coptpy as cp
from coptpy import COPT


def solve_lp(
    c,
    A_ub=None,
    b_ub=None,
    A_eq=None,
    b_eq=None,
    bounds=None,
    sense="min",
    time_limit=None,
):
    """
    c: (n,)
    A_ub, b_ub: Ax <= b，A_ub 形状 (m_ub, n)
    A_eq, b_eq: Ax == b，A_eq 形状 (m_eq, n)
    bounds: 长度 n 的 [(lb, ub), ...]；None 表示每个变量 (-inf, +inf)
    sense: "min" 或 "max"
    """
    c = np.asarray(c, dtype=float).ravel()
    n = c.shape[0]

    if bounds is None:
        bounds = [(-COPT.INFINITY, COPT.INFINITY) for _ in range(n)]

    def _norm_bound(val, default_value):
        if val is None:
            return default_value
        if isinstance(val, str) and val.lower() == "null":
            return default_value
        return float(val)

    if A_ub is not None:
        A_ub = np.asarray(A_ub, dtype=float)
        if A_ub.shape[1] != n:
            raise ValueError(f"A_ub 列数 {A_ub.shape[1]} 与 c 长度 {n} 不匹配")
        if b_ub is None:
            raise ValueError("提供 A_ub 时必须同时提供 b_ub")
        b_ub = np.asarray(b_ub, dtype=float).ravel()
        if len(b_ub) != A_ub.shape[0]:
            raise ValueError(f"b_ub 长度 {len(b_ub)} 与 A_ub 行数 {A_ub.shape[0]} 不匹配")

    if A_eq is not None:
        A_eq = np.asarray(A_eq, dtype=float)
        if A_eq.shape[1] != n:
            raise ValueError(f"A_eq 列数 {A_eq.shape[1]} 与 c 长度 {n} 不匹配")
        if b_eq is None:
            raise ValueError("提供 A_eq 时必须同时提供 b_eq")
        b_eq = np.asarray(b_eq, dtype=float).ravel()
        if len(b_eq) != A_eq.shape[0]:
            raise ValueError(f"b_eq 长度 {len(b_eq)} 与 A_eq 行数 {A_eq.shape[0]} 不匹配")

    if b_ub is not None and A_ub is None:
        raise ValueError("提供 b_ub 时必须同时提供 A_ub")
    if b_eq is not None and A_eq is None:
        raise ValueError("提供 b_eq 时必须同时提供 A_eq")

    env = cp.Envr()
    model = env.createModel("lp")

    x = [
        model.addVar(
            lb=_norm_bound(bounds[j][0], -COPT.INFINITY),
            ub=_norm_bound(bounds[j][1], COPT.INFINITY),
            name=f"x{j}",
        )
        for j in range(n)
    ]

    if A_ub is not None:
        for i in range(A_ub.shape[0]):
            model.addConstr(
                cp.quicksum(A_ub[i, j] * x[j] for j in range(n)) <= float(b_ub[i]),
                name=f"ub_row{i}",
            )

    if A_eq is not None:
        for i in range(A_eq.shape[0]):
            model.addConstr(
                cp.quicksum(A_eq[i, j] * x[j] for j in range(n)) == float(b_eq[i]),
                name=f"eq_row{i}",
            )

    obj = cp.quicksum(c[j] * x[j] for j in range(n))
    model.setObjective(
        obj,
        sense=COPT.MINIMIZE if sense.lower().startswith("min") else COPT.MAXIMIZE,
    )

    if time_limit is not None:
        model.setParam(COPT.Param.TimeLimit, float(time_limit))

    model.solve()

    # COPT 状态码：1=OPTIMAL, 2=INFEASIBLE, 3=UNBOUNDED
    OPTIMAL = 1
    INFEASIBLE = 2
    UNBOUNDED = 3

    status_name = {
        OPTIMAL: "OPTIMAL",
        INFEASIBLE: "INFEASIBLE",
        UNBOUNDED: "UNBOUNDED",
    }.get(model.status, f"STATUS_{model.status}")

    if model.status == OPTIMAL:
        return {
            "status": status_name,
            "obj": model.objval,
            "x": np.array([v.x for v in x]),
        }
    return {
        "status": status_name,
        "obj": None,
        "x": None,
    }


if __name__ == "__main__":
    # 与 SKILL 中「两产品」示例一致，便于快速冒烟（需有效 license）
    out = solve_lp(
        c=[3, 5],
        A_ub=[[1, 2], [2, 1]],
        b_ub=[100, 120],
        bounds=[(0, None), (0, None)],
        sense="max",
    )
    print(out)
