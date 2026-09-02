# Sources and attribution

This package provides a thin, standalone entrypoint to released optimization
skill cards from [OptSkills](https://github.com/fujiwaranoM0kou/OptSkills).

Upstream snapshot commit: d9e14300df4b499529c74ea1981e2c1aba0628b8

Paper: *OptSkills: Learning Generalizable Optimization Skills from Problem
Archetypes via Cluster-Based Distillation*, arXiv:2605.29829.

Paper authors: Haochen Yang, Ke Zhao, Mengyuan Ma, Xingyu Lu, Xiangfeng Wang,
and Hong Qian.

## Included material

- all 93 Markdown cards from `skill_library_nanoco_learned`;
- the 10 `skill_library_learned` cards whose `skill_id` is absent from NanoCO;
- the selected entries from the two upstream `index.json` files.

The Markdown card bodies and selected index fields are kept as published
upstream. VeryMath adds only the standalone entrypoint, combined index, human
documentation, and reviewed update instructions.

## Excluded material

The OptSkills training, clustering, self-learning, trajectory, evaluation,
agent, LLM, embedding, dataset, and `ingredients.json` components are not part
of this package and are not runtime dependencies.

The included upstream material is distributed under the MIT license in
`LICENSE`. Consult the source repository and paper for the original project.
