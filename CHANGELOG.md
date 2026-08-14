# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-08-14

### Added

- Initial `praxicraft` Python SDK for the Assess Public API.
- `Client` with Bearer API-key auth (`PRAXICRAFT_API_KEY` / `PRAXICRAFT_API_BASE_URL`).
- Typed errors mapped from the Public API `{ "error": { "code", "message" } }` envelope.
- Resources: `assessments` (list / retrieve / create / update / activate / cases), `invites`, `results`, `org`, `webhooks` (CRUD + test), `pipelines` (list / enroll).
- Local webhook helper `verify_signature` for `X-Praxicraft-Signature`.
- CI on Python 3.10–3.12 and tag-triggered PyPI publish via Trusted Publishing.
