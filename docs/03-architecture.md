# ClauseCheck architecture decision log (Day 3)

## Decision 1: model
| Option | Quality signal | p50 / p95 latency | Cost per contract | Chosen? |
|---|---|---|---|---|
| gemini-3.5-flash-lite | | | | |
| gemini-3.5-flash | | | | |

## Decision 2: whole contract in the prompt, or retrieval?
<!-- Paste the two cost rows from results/cost_model.md. Decide, and say what would change your mind. -->

## Decision 3: build, buy or fine-tune
<!-- Buy: an off-the-shelf contract review / CLM AI tool. Build: this. Fine-tune: a model on CUAD. One paragraph each, then the call. -->

## Decision 4: data handling
<!-- Free tier prompts may be used to improve Google's products. What does that mean for real client contracts? What would production need? -->

## Hardware constraint
<!-- 12 GB laptop: what fits in memory, what you chose not to run locally. -->

## Dependency risks
<!-- e.g. Google's docs now label generate_content as "Legacy". What's your exposure? -->
