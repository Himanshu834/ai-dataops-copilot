# Project Plan

This is the concise, evolving milestone tracker. A phase is complete only when its behavior is implemented and its relevant tests pass. Keep this file and `PROJECT_CONTEXT.md` current as decisions or results change. The repository and tests are the source of truth.

## Phase 0: Foundation and Ingestion

- [x] Implement local Parquet ingestion, batch IDs, SHA-256, row-count manifest, atomic output, idempotency, and CLI. Last recorded checks: 8 tests passed and CLI help worked.
- [ ] Run a real-data smoke test with an official monthly NYC Yellow Taxi Parquet file; inspect its manifest and schema. Keep raw data out of Git.

## Phase 1: Silver Processing

- [ ] Inspect the real input schema and choose a local processing approach before adding heavyweight Spark/Delta dependencies.
- [ ] Build a repeatable Silver transformation while leaving Bronze input unchanged.
- [ ] Standardize relevant types and timestamps; define handling for nulls, invalid values, and duplicates based on the observed schema.
- [ ] Test representative valid and malformed rows, output schema and counts, reruns, and Bronze immutability.

## Phase 2: Data Quality

- [ ] Add configurable checks for nulls, uniqueness, ranges, schema drift, and row-count changes.
- [ ] Test controlled failures, including DQ001-DQ006 scenarios where applicable.

## Phase 3: Anomaly Detection

- [ ] Start with statistical baselines, then consider ML if it adds value.
- [ ] Test known normal and injected-anomaly cases; measure results before reporting metrics.

## Phase 4: Evidence and Copilot

- [ ] Capture operational evidence and add retrieval with grounded explanations.
- [ ] Test evidence references, uncertainty, and unsupported-claim behavior.

## Phase 5: Operations and Product

- [ ] Add run status/retries and operational APIs or UI as justified.
- [ ] Test failures and reruns; require human approval for consequential actions.

## Phase 6: Evaluation and Portfolio

- [ ] Create reproducible evaluation cases and measure quality, retrieval, and answer behavior.
- [ ] Document limitations and cost/performance trade-offs, then prepare the demo.

## Testing Cadence

- Add or update focused tests with each behavior change; run the narrow tests first.
- Run the full test suite at milestone boundaries and record the actual result here.
- Keep real datasets and generated pipeline output untracked; do not claim metrics or capabilities that have not been verified.
- Adjust later phases as the implementation and learning goals evolve.
