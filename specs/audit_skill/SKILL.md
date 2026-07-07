---
name: local-financial-auditor
description: |
  Analyzes sanitized financial transaction logs and matches items against reference cost benchmarks.
  Use when analyzing raw statements, auditing personal subscriptions, or extracting item totals.
  Do NOT use for high-risk execution sinks like initiating actual financial bank transfers.
version: 1.0.0
allowed-tools:
  - query_benchmark_rate
---

# Local Financial Auditor Runbook
1. Intercept payloads forwarded from the middleware context resolver.
2. Invoke `query_benchmark_rate` to extract database cost benchmarks.