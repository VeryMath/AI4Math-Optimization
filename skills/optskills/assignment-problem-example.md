# Solving an assignment problem with OptSkills

[中文](assignment-problem-example.zh-CN.md)

This walkthrough shows one complete OptSkills use: ask a coding agent to
install the standalone Skill, describe an optimization problem in natural
language, select a released archetype card, formulate and solve the model, and
check the returned objective and constraints.

## Ask a coding agent to install it

Give this prompt to Codex, Claude Code, OpenCode, or another coding agent that
supports Skills:

```text
Install skills/optskills from the GitHub repository
VeryMath/AI4Math-Optimization. Install only this standalone Skill. Detect the
skill directory used by the current coding agent, link or copy the package,
and verify that a new session can discover optskills. Report:
1. where the repository is stored;
2. where the Skill is installed;
3. whether discovery was verified;
4. whether a restart or new conversation is needed;
5. one prompt I can use to test it.
If the destination already exists, do not overwrite it immediately. First
check whether it comes from the same repository and explain what should happen.
```

The coding agent chooses the installation location from the discovery rules of
its current environment. Installation means more than copying files: it should
also confirm that a new session can see a Skill named `optskills`.

## Submit the problem

After installation, start a new conversation and enter:

```text
Use OptSkills to solve this assignment problem.

Five virtual machines must be assigned to five physical servers. Every virtual
machine must use exactly one server, and every server must receive exactly one
virtual machine. Rows in this cost matrix are virtual machines and columns are
servers:

[[28, 15, 51, 19, 72],
 [46, 44, 24, 14, 55],
 [14, 18, 35, 61, 30],
 [34, 41, 26, 50, 37],
 [40, 53, 15, 62, 15]]

Minimize the total assignment cost. Report the selected Skill, mathematical
model, solver status, assignment, objective, and constraint checks. If no
solver is available, identify the missing dependency instead of claiming that
the problem was solved.
```

The data come from the public OptSkills record `AP_easy_1`.

## How OptSkills handles it

The agent first makes the package's lightweight upstream commit comparison. A
matching version is silent. A failed lookup or newer version produces one short
note and does not download the full upstream project during this task.

The agent then reads `skill_library/index.json`. The one-to-one assignment,
linear cost objective, and two families of exact-one constraints lead it to:

```text
skill_id: assignment_problem_solver
path: skill_library/assignment_problem_solver.md
```

It loads this relevant card rather than all 103 cards.

## Formulate the model

Let the virtual-machine and server sets be

$$
I=J=\{1,2,3,4,5\}.
$$

Set $x_{ij}=1$ when virtual machine $i$ is assigned to server $j$, and set it
to zero otherwise. Let $c_{ij}$ be the corresponding cost. The model is

$$
\min \sum_{i\in I}\sum_{j\in J}c_{ij}x_{ij},
$$

subject to

$$
\sum_{j\in J}x_{ij}=1\qquad \forall i\in I,
$$

$$
\sum_{i\in I}x_{ij}=1\qquad \forall j\in J,
$$

and

$$
x_{ij}\in\{0,1\}.
$$

The first constraints assign every virtual machine exactly once. The second
constraints use every server exactly once.

## Solver result

In the OR-Tools CP-SAT environment used for repository validation, the solver
returned `OPTIMAL` with this assignment:

| Virtual machine | Server | Cost |
| --- | --- | ---: |
| 1 | 2 | 15 |
| 2 | 4 | 14 |
| 3 | 1 | 14 |
| 4 | 3 | 26 |
| 5 | 5 | 15 |

The total cost is

$$
15+14+14+26+15=84.
$$

## Check the result

The agent should independently check the returned assignment instead of only
repeating the solver's objective field:

- solver status is `OPTIMAL`;
- all five virtual-machine assignment counts equal 1;
- all five server usage counts equal 1;
- the recomputed total cost is 84;
- the recomputed result equals the solver objective.

Only after these checks can it report that this instance was solved and its
constraints were verified.

## If no solver is available

OptSkills does not bundle OR-Tools, Pyomo, HiGHS, or a commercial solver. If a
suitable solver is absent, the agent can still report the selected card,
mathematical model, and solver code. It must distinguish “model formulated”
from “solver executed” and ask before installing a new dependency.

## Try another problem

After one installation, a new conversation can use prompts such as:

```text
Use OptSkills to formulate a minimum-cost flow problem with arc capacities and
unit transportation costs. After solving it, check every node balance and arc
capacity.
```

```text
Use OptSkills to formulate a flow-shop scheduling problem for multiple jobs and
machines. Minimize makespan and check operation order and machine non-overlap.
```

For each task, report the selected card, formulated model, whether a solver was
actually executed, objective check, constraint check, and remaining limitations
as separate results.
