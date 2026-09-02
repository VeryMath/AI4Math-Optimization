# OptSkills

OptSkills is a standalone thin entrypoint to 103 released OptSkills
problem-archetype cards. It helps an agent select a card, formulate the
user's actual operations-research problem, solve it when the environment
permits, and report what was checked.

## Source selection

The library contains 93 NanoCO cards and 10 learned-only cards. It includes no
cluster duplicate and no `ingredients.json`. The selected cards and their
relative paths are listed in `skill_library/index.json`.

## Installation

Clone `VeryMath/AI4Math-Optimization`, then link only `skills/optskills` into
the agent's skill directory:

```bash
git clone https://github.com/VeryMath/AI4Math-Optimization.git
cd AI4Math-Optimization
mkdir -p ~/.codex/skills
ln -s "$PWD/skills/optskills" ~/.codex/skills/optskills
```

## Quick start

Use this prompt:

> Read `SKILL.md`, select the relevant OptSkills cards through
> `skill_library/index.json`, formulate my problem, solve it if possible, and
> check the key constraints.

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
