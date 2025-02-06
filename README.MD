## Heuristics:

heuristic_time(): Simply prunes path where time runs out.

heuristic_axe(): Prioritizes paths with building the most efficient axe as possible.

heuristic_gather(): Prioritize gathering wood with best possible tool.

heuristic_count_tasks(): Prune paths which redundantly builds expensive items multiple times. 

heuristic_tiers(): Prioritize paths with efficient tool tier progression. 