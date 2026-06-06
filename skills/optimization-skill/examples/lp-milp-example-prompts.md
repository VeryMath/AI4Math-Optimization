# LP/MILP Example Prompts

English | [简体中文](lp-milp-example-prompts.zh-CN.md)

These prompts are example user requests for exercising `$optimization-skill` on classic operations-research problems such as LP, MILP, transportation, assignment, set cover, network flow, and facility location.

They are few-shot prompts for modeling and solver-route selection. Current generated code support is strongest for SDPT3 and CDOpt; LP/MILP prompts should ask the agent to produce a reviewed model and recommend CVXPY, Pyomo, YALMIP, CVX, or a repository-native route before any executable adapter is generated.

Use pattern: copy one complete `text` block into a fresh agent session after the Skill is installed and discoverable.

## Prompt 0: Extract LP/MILP Example Map

```text
Use $optimization-skill.

I want to use classic LP/MILP operations-research examples as problem statements for this Skill. Extract the problem map into these groups:

1. Linear programming examples suitable for CVXPY or direct LP solvers
2. Mixed-integer programming examples suitable for Pyomo or YALMIP
3. Repository-native examples where existing code should be preserved

For each example, report:
- problem title;
- variables and domains;
- objective type;
- core constraints;
- recommended modeling layer or solver route;
- whether current automatic code generation is available or should stop at a reviewed modeling checkpoint.

Do not install packages or run code. End by recommending the first two examples I should use as few-shot tests and why.
```

## Prompt 1: Transportation Linear Program

```text
Use $optimization-skill.

Model a transportation linear program.

Problem:
There are m warehouses and n customers. Warehouse i has supply supply[i]. Customer j has demand demand[j]. Shipping one unit from i to j costs cost[i,j]. Decide shipment x[i,j] >= 0 to minimize total shipping cost while respecting warehouse supply and customer demand.

Requirements:
- Write the mathematical model first.
- Identify variables, objective, constraints, dimensions, and data.
- Produce a schema-compatible problem.yaml draft.
- Recommend a CVXPY or repository-native LP route, but do not claim current automatic LP codegen unless the Skill actually supports it.
- Ask for confirmation before generating or running any code.
```

## Prompt 2: Assignment MILP

```text
Use $optimization-skill.

Model a binary assignment problem.

Problem:
There are n workers and n jobs. Assign each worker to exactly one job and each job to exactly one worker. Binary variable x[i,j] is 1 when worker i is assigned to job j. Assignment cost is cost[i,j]. Minimize total cost.

Requirements:
- Write the MILP model with binary variables.
- Identify whether this can be solved as a classic assignment problem or as a generic MILP.
- Produce a schema-compatible problem.yaml draft.
- Recommend Pyomo, YALMIP, or repository-native solver route.
- Do not run code until I approve the model and execution plan.
```

## Prompt 3: Set Cover MILP

```text
Use $optimization-skill.

Model a weighted set cover problem.

Problem:
There is a universe U of required elements and a collection of candidate sets S_k. Choosing set k costs c[k]. Binary variable y[k] is 1 if set k is selected. Every element must be covered by at least one selected set. Minimize total selected cost.

Requirements:
- Write the MILP model.
- Make the coverage matrix explicit as data a[e,k] in {0,1}.
- Produce a schema-compatible problem.yaml draft.
- Recommend a Pyomo or YALMIP route and list candidate MILP solvers such as HiGHS, GLPK, CBC, Gurobi, or SCIP if available.
- Do not install dependencies or run code without approval.
```

## Prompt 4: Capacitated Facility Location MILP

```text
Use $optimization-skill.

Model a capacitated facility location problem.

Problem:
Potential facilities f have fixed opening cost fixed_cost[f] and capacity capacity[f]. Customers c have demand demand[c]. Serving customer c from facility f costs ship_cost[f,c] per unit. Binary y[f] opens a facility. Continuous x[f,c] ships demand from facility f to customer c. Minimize fixed opening cost plus shipping cost.

Requirements:
- Write the MILP with binary facility decisions and continuous shipment variables.
- Include demand satisfaction, capacity, and linking constraints.
- Produce a schema-compatible problem.yaml draft.
- Recommend Pyomo or repository-native MILP route.
- Identify numerical or modeling risks such as big-M/linking constraints and missing capacity data.
```

## Prompt 5: Minimum-Cost Network Flow LP

```text
Use $optimization-skill.

Model a minimum-cost network flow problem.

Problem:
Given directed graph G=(V,E), each arc (i,j) has unit cost c[i,j] and capacity u[i,j]. Each node v has balance b[v], positive for supply and negative for demand. Choose flow x[i,j] to minimize total cost while satisfying flow balance and arc capacity.

Requirements:
- Write the LP model.
- Clarify sign conventions for node balance.
- Produce a schema-compatible problem.yaml draft.
- Recommend CVXPY, scipy/HiGHS, or repository-native route depending on available data.
- Do not generate executable code until the model is confirmed.
```

## Prompt 6: Single-Machine Scheduling MILP

```text
Use $optimization-skill.

Model a small single-machine scheduling MILP.

Problem:
There are jobs J. Each job j has processing time p[j] and due date d[j]. Sequence all jobs on one machine without overlap. Minimize total tardiness. Use binary precedence variables y[i,j] and completion time variables C[j].

Requirements:
- Write a MILP model and explain the big-M constraints.
- Identify data needed for a safe M value.
- Produce a schema-compatible problem.yaml draft.
- Recommend Pyomo or YALMIP route.
- Stop at a modeling checkpoint if the big-M value cannot be justified.
```

## Prompt 7: Natural-Language To LP/MILP Spec Stress Prompt

```text
Use $optimization-skill.

I will describe an operations-research problem in natural language. Convert it into a reviewed LP/MILP modeling checkpoint and a schema-compatible problem.yaml draft. Do not run code.

Problem:
A company chooses which projects to fund. Project k has profit p[k], budget cost b[k], and uses engineering hours h[k]. Some projects require others: if project 4 is selected, project 1 must also be selected. The total budget and engineering hours are limited. Select projects to maximize total profit.

Requirements:
- Infer binary decision variables.
- Write objective and constraints.
- Include dependency constraints.
- Recommend a Pyomo or MILP route.
- List ambiguities and ask for confirmation before any code generation.
```
