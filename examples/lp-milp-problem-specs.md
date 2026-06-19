# LP/MILP Problem Spec Few-Shots

These examples show schema-compatible `problem.yaml` drafts for LP/MILP modeling. They are intended as few-shot references for `$optimization-modeling-skill` and future CVXPY/Pyomo codegen work.

Current helper scripts accept `solver_preferences.backend` values `auto`, `sdpt3`, `scipy`, or `existing`, so these examples use `backend: existing` and record the intended modeling layer separately. Future LP/MILP codegen can promote these patterns into dedicated `cvxpy` or `pyomo` backends.

## Transportation LP

```yaml
schema_version: 1
problem_id: transportation_lp
input_type: natural_language
problem_class: linear_program
domain:
  family: linear_optimization
  tags: [transportation, network_flow, lp]
objective:
  sense: minimize
  expression: sum_i_j cost[i,j] * x[i,j]
variables:
  - name: x
    type: matrix
    shape: [m, n]
    domain: nonnegative_continuous
    description: shipment quantity from warehouse i to customer j
constraints:
  - name: supply_capacity
    expression: sum_j x[i,j] <= supply[i] for all warehouses i
  - name: demand_satisfaction
    expression: sum_i x[i,j] >= demand[j] for all customers j
data:
  parameters:
    m: number of warehouses
    n: number of customers
    supply: nonnegative vector length m
    demand: nonnegative vector length n
    cost: nonnegative matrix shape [m, n]
solver_preferences:
  backend: existing
  modeling_layer: cvxpy
  timeout_seconds: 300
modeling_layer:
  language: python
  package: cvxpy
  notes: Future codegen target; current Skill should stop at a reviewed model or use repository-native code.
review:
  modeling_status: proposed
  execution_approval_required: true
metadata:
  source: few-shot transportation LP prompt
  notes: Check whether total supply can satisfy total demand and whether equality demand constraints are desired.
```

## Assignment MILP

```yaml
schema_version: 1
problem_id: assignment_milp
input_type: natural_language
problem_class: mixed_integer_linear_program
domain:
  family: integer_optimization
  tags: [assignment, bipartite_matching, milp]
objective:
  sense: minimize
  expression: sum_i_j cost[i,j] * x[i,j]
variables:
  - name: x
    type: binary_matrix
    shape: [n, n]
    domain: binary
    description: x[i,j] is 1 when worker i is assigned to job j
constraints:
  - name: one_job_per_worker
    expression: sum_j x[i,j] == 1 for all workers i
  - name: one_worker_per_job
    expression: sum_i x[i,j] == 1 for all jobs j
data:
  parameters:
    n: number of workers and jobs
    cost: matrix shape [n, n]
solver_preferences:
  backend: existing
  modeling_layer: pyomo
  timeout_seconds: 300
modeling_layer:
  language: python
  package: pyomo
  candidate_solvers: [highs, glpk, cbc, gurobi, scip]
review:
  modeling_status: proposed
  execution_approval_required: true
metadata:
  source: few-shot assignment MILP prompt
  notes: This problem also has specialized assignment algorithms; choose generic MILP only when useful for extension.
```

## Weighted Set Cover MILP

```yaml
schema_version: 1
problem_id: weighted_set_cover_milp
input_type: natural_language
problem_class: mixed_integer_linear_program
domain:
  family: integer_optimization
  tags: [set_cover, binary_selection, milp]
objective:
  sense: minimize
  expression: sum_k cost[k] * y[k]
variables:
  - name: y
    type: binary_vector
    shape: [num_sets]
    domain: binary
    description: y[k] is 1 when candidate set k is selected
constraints:
  - name: cover_each_element
    expression: sum_k cover[e,k] * y[k] >= 1 for all elements e
data:
  parameters:
    num_elements: universe size
    num_sets: number of candidate sets
    cost: nonnegative vector length num_sets
    cover: binary matrix shape [num_elements, num_sets]
solver_preferences:
  backend: existing
  modeling_layer: pyomo
  timeout_seconds: 300
modeling_layer:
  language: python
  package: pyomo
  candidate_solvers: [highs, glpk, cbc, gurobi, scip]
review:
  modeling_status: proposed
  execution_approval_required: true
metadata:
  source: few-shot weighted set cover prompt
  notes: Confirm every required element has at least one covering set before execution.
```

## Capacitated Facility Location MILP

```yaml
schema_version: 1
problem_id: capacitated_facility_location_milp
input_type: natural_language
problem_class: mixed_integer_linear_program
domain:
  family: integer_optimization
  tags: [facility_location, fixed_charge, capacity, milp]
objective:
  sense: minimize
  expression: sum_f fixed_cost[f] * y[f] + sum_f_c ship_cost[f,c] * x[f,c]
variables:
  - name: y
    type: binary_vector
    shape: [num_facilities]
    domain: binary
    description: y[f] is 1 when facility f is opened
  - name: x
    type: matrix
    shape: [num_facilities, num_customers]
    domain: nonnegative_continuous
    description: shipment quantity from facility f to customer c
constraints:
  - name: demand_satisfaction
    expression: sum_f x[f,c] == demand[c] for all customers c
  - name: facility_capacity
    expression: sum_c x[f,c] <= capacity[f] * y[f] for all facilities f
data:
  parameters:
    num_facilities: number of candidate facilities
    num_customers: number of customers
    fixed_cost: nonnegative vector length num_facilities
    capacity: nonnegative vector length num_facilities
    demand: nonnegative vector length num_customers
    ship_cost: nonnegative matrix shape [num_facilities, num_customers]
solver_preferences:
  backend: existing
  modeling_layer: pyomo
  timeout_seconds: 600
modeling_layer:
  language: python
  package: pyomo
  candidate_solvers: [highs, cbc, gurobi, scip]
review:
  modeling_status: proposed
  execution_approval_required: true
metadata:
  source: few-shot capacitated facility location prompt
  notes: The capacity-linking constraint avoids a separate arbitrary big-M if capacity is valid.
```
