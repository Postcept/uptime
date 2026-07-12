# Postcept uptime

Independent uptime history for the Postcept API.

The checks in `.github/workflows/probe.yml` run on GitHub's hosted runners every
15 minutes. Those runners are outside the Render and Supabase accounts that run
production, so this is a separate vantage point rather than Postcept checking
itself. Each run records the HTTP status and response time for three endpoints
and appends one line per check to `history/YYYY-MM.jsonl`. The files are
append-only and never rewritten.

Endpoints probed:

- `GET /readyz` reports readiness
- `GET /v1/signing-key` returns the receipt signing key
- `GET /v1/transparency/sth` returns the transparency log signed tree head

## What this is and isn't

This is raw measurement from one external location, not a service level
agreement. A failed check can mean the API was down, the runner had a network
problem, or the API was cold-starting on a free tier. Read the raw history and
draw your own conclusions.
