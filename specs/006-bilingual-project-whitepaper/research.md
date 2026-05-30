# Research: Bilingual Project Whitepaper

## Canonical Document Location

**Decision**: Use root-level `WHITEPAPER.md`.

**Rationale**: The page is discoverable from the repository root, easy to link from
README, and independent of any one feature spec.

**Alternatives considered**:
- Expand README indefinitely: keeps the entry page noisy and harder to scan.
- Place the manual under one active spec: makes long-lived guidance appear feature-local.
- Split English and Vietnamese into separate files: increases drift risk.

## Bilingual Structure

**Decision**: Pair English and Vietnamese subsections inside each major section.

**Rationale**: Readers can jump to one topic and see equivalent guidance without
cross-referencing a second document.

## Governance Propagation

**Decision**: Add a living operational documentation principle to the constitution and
reinforce it in both agent guides plus the Speckit tasks template.

**Rationale**: The whitepaper is only useful if every future feature explicitly checks
whether commands, parameters, architecture, logs, optimization guidance, or user-facing
behavior changed.
