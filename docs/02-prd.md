# ClauseCheck PRD v1 (Day 2)

**Owner:** Kriti · **Status:** Draft · **Last updated:**

## Problem and user
<!-- Two sentences, from 01-problem.md. -->

## Goals
<!-- Outcome goals with numbers, e.g. "cut first-pass review from X to Y minutes". -->

## Non-goals
<!-- At least four. What ClauseCheck will not do, even if asked. -->

## Scope: v1
| In | Out (and why) |
|---|---|
| | |

## Error costs
| Question | Cost of a missed clause (false negative) | Cost of a false alarm (false positive) | Severity |
|---|---|---|---|
| Q1 Liability cap | | | |
<!-- one row per question -->

## Acceptance criteria
<!-- Non-deterministic system: criteria are rates on a named eval set, with floors per slice. -->
| # | Criterion | Measured on | Threshold | Why this number |
|---|---|---|---|---|
| AC1 | Recall on severity-3 questions | test split, 20 contracts | ≥ | |
| AC2 | Precision, all questions | | ≥ | |
| AC3 | Citation correct when a clause is found | | ≥ | |
| AC4 | No answer without a verbatim quote | every answer | 100% | |
| AC5 | p95 time for 10 checks | | ≤ | |
| AC6 | Cost per contract (paid tier) | | ≤ | |

## Success metrics after launch
<!-- Leading (adoption, override rate) and lagging (counsel spend, cycle time). -->

## Risks and open questions
