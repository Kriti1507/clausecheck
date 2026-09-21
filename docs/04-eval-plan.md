# ClauseCheck evaluation plan (Day 4, written before the build)

## What "good" means
<!-- Link each metric to an acceptance criterion in the PRD. -->

## Eval sets
| Set | Contracts | Used for | Rule |
|---|---|---|---|
| dev | 30 (c001-c030) | tuning chunking, prompts | look as often as you like |
| test | 20 (c031-c050) | final score | run on Day 7 and once on Day 8, never tuned against |

## Metrics
| Layer | Metric | How it's computed | Target |
|---|---|---|---|
| Retrieval | recall@k | a top-k chunk overlaps the lawyers' span | |
| Answer | precision, recall per question | vs CUAD present/absent | |
| Grounding | citation correct | cited excerpt overlaps the gold span | |
| Grounding | quote verbatim | quote found in excerpts | |
| Operations | p50/p95 latency, cost per contract | logged per call | |

## The accuracy trap
<!-- Which questions would an "always no" system score >85% on? Why does that make accuracy useless there? -->

## Sample size honesty
<!-- How many positives per question in test? What can and can't you conclude from 2 examples? -->

## Failure taxonomy (hypotheses before seeing results)
| Code | Failure type | Example of what it would look like | Likely cause | Likely fix |
|---|---|---|---|---|
| F1 | Retrieval miss | | | |
| F2 | | | | |
<!-- at least six -->

## Decision rules
<!-- What results would make you ship, iterate, or stop? Write them now so you can't move the goalposts later. -->
