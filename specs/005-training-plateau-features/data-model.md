# Data Model: Improve Training Plateau Signals

## Line Window Metrics

- `open_single_windows`: count of length-three windows with one placed value and two empties
- `open_pair_windows`: count of length-three windows with two equal values and one empty
- `blocked_windows`: count of length-three windows with at least two conflicting values
- `multi_line_completion_cells`: count of unique empty cells completing at least two lines

## Plateau Diagnostics

- `unique_chromosome_count`: number of distinct serialized gene matrices
- `chromosome_diversity_ratio`: unique count divided by population size
- `active_gene_count_min`: minimum active genes across chromosomes
- `active_gene_count_average`: average active genes across chromosomes
- `active_gene_count_max`: maximum active genes across chromosomes
- `no_improvement_generations`: consecutive generations without a new global best
- `adaptive_mutation_surge`: whether the next evolution step uses the surge rate

## Normalized Chromosome

Each phase gene list must match the active feature count. Legacy lists are extended with
`mask=0` and `weight=0.0`; oversized lists are invalid.
