# Phase IIIB Archive

This archive captures the baseline for AETHER's Phase IIIB implementation.

## Rewrite strategies

- Docstring insertion for undocumented functions.
- TODO completion marker to surface handled TODOs.
- Function splitting which moves a function body into a helper and annotates the original wrapper.

Each rewrite writes mutations under `__aether_mutation__/` and emits a unified diff alongside the mutated file.
