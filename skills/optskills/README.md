# OptSkills

[中文](README.zh-CN.md)

OptSkills is a standalone thin entrypoint to 103 released OptSkills
problem-archetype cards. It helps an agent select a card, formulate the
user's actual operations-research problem, solve it when the environment
permits, and report what was checked.

## Source selection

The library contains 93 NanoCO cards and 10 learned-only cards. It includes no
cluster duplicate and no `ingredients.json`. The selected cards and their
relative paths are listed in `skill_library/index.json`.

## Install with a coding agent

Give this prompt to your coding agent:

> Install `skills/optskills` from the GitHub repository
> `VeryMath/AI4Math-Optimization`. Install only this standalone Skill. Detect
> the skill directory used by the current coding agent, link or copy the
> package there, and verify that `optskills` is discoverable. Report the
> installed path, whether a restart is needed, and one test prompt.

The coding agent should clone or update the repository, locate the correct
skill directory for its environment, install the package, and verify
discovery. The user does not need to choose a local directory first.

## Quick start

Use this prompt:

> Read `SKILL.md`, select the relevant OptSkills cards through
> `skill_library/index.json`, formulate my problem, solve it if possible, and
> check the key constraints.

See [Solving an assignment problem with OptSkills](assignment-problem-example.md)
for a complete walkthrough.

## Updates

Use this prompt only when an upstream update is wanted:

> Update this standalone OptSkills package from the official upstream. Read `UPDATE.md`, report proposed changes first, and wait for approval before editing.

## Boundaries

Raw cards may contain placeholders or unverified examples. Being installed,
loaded, solved, and checked are different claims; report each state separately.
Normal use is package-local and does not call sibling skills or require the
upstream training, agent, chat, or embedding system.

## License and sources

See [SOURCES.md](SOURCES.md) for upstream attribution and [LICENSE](LICENSE)
for licensing information.
