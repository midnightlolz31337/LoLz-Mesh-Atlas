# LoLz Mesh Atlas

A public, exportable catalogue of LoLz projects and their verified maturity. This is a discovery index, not a runtime authority or mandatory service.

## Current catalogue

`catalogue/projects.yaml` is the source catalogue. Each record includes a stable ID, repository URL, maturity status, role, public visibility, and a dated verification level.

The current verification level `repository-exists` means only that the public repository was checked to exist on the recorded date. It does not certify source quality, security, functionality, independence, or release readiness. Higher levels require evidence and reproducible checks.

Private projects and private Think Tank records must never be placed in this public catalogue.

## Validate locally

```bash
python -m pip install -r requirements.txt
python -m atlas_catalogue.validator
python -m unittest discover -s tests -v
```

Validation is offline. It checks the catalogue against the JSON Schema, rejects duplicate YAML mapping keys, duplicate project IDs, duplicate repository URLs, non-HTTPS URLs, and private visibility records. It does not fetch repository URLs or independently verify their current status.

## Design principles

- No mandatory LoLz-hosted service.
- Multiple independent indexes and direct repository discovery remain possible.
- Public records only; private architecture and research remain private.
- Status describes project maturity, not trustworthiness.
- Verification levels must be evidence-backed and dated.
- Catalogue records are portable and forkable.

## Status vocabulary

- `planned`: proposed, not yet bootstrapped.
- `bootstrap`: repository and initial structure exist.
- `experimental`: implementation exists but is not production-ready.
- `active`: maintained project with current verified functionality.
- `maintenance`: limited feature development; maintenance focus.
- `archived`: no longer actively maintained.
- `unverified`: status or source state has not been checked.

## Verification levels

- `repository-exists`: public repository existence checked.
- `source-reviewed`: source files reviewed for a stated scope.
- `ci-verified`: named CI suite passed on an exact commit.
- `independently-reproduced`: a separate operator reproduced a stated result.

A higher level is not a blanket security certification. Every claim must name its scope, date, revision, and evidence.
