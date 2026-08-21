# Releasing

Maintainer notes for publishing `praxicraft` to PyPI. Integrators should ignore this file — see the [README](README.md).

## How publish works

[`.github/workflows/publish.yml`](.github/workflows/publish.yml) runs on pushes to **`main`** when key files change:

- `src/**`
- `pyproject.toml`
- `CHANGELOG.md`
- `.github/workflows/publish.yml`

Flow:

1. Run the test matrix (Python 3.10–3.12).
2. Read `version` from `pyproject.toml` and require it to match `__version__` in `src/praxicraft/__init__.py`.
3. If git tag `v{version}` **already exists** → skip publish (safe no-op).
4. If the tag is **new** → create annotated tag `v{version}`, push it, build, upload to PyPI via **Trusted Publishing (OIDC)**.

You do **not** push tags by hand for normal releases.

## Cut a release

1. Bump `version` in `pyproject.toml`.
2. Bump `__version__` in `src/praxicraft/__init__.py` to the same value.
3. Update `CHANGELOG.md`.
4. Merge to `main` (with changes under the path filters above).

CI tags and publishes automatically when that version has never been tagged.

## Idempotency

- Same version pushed again (docs-only or code without a version bump) → workflow may still run, but publish is skipped because the tag exists.
- To ship again, bump the version (e.g. `0.1.0` → `0.1.1`).

## One-time Trusted Publishing setup

1. Create a GitHub Environment named **`pypi`** on `praxicraft-platform/praxicraft-python` (optional required reviewers).
2. On [pypi.org](https://pypi.org) → project / pending publisher → **Publishing** → add trusted publisher:
   - Owner: `praxicraft-platform`
   - Repository: `praxicraft-python`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
3. Ensure the default branch is `main` and the `github-actions` bot can push tags (`contents: write` is set on the publish job).
4. Merge a version bump to `main` to cut the first release.

## GitHub Release

The Publish workflow also creates a **GitHub Release** for tag `v{version}` (with generated notes and package assets where applicable).

You can run **Actions → Publish → Run workflow** manually (`workflow_dispatch`) after bumping the version on `main`.

## Auto-bump

Pushes to `main` that change package source auto-bump the patch version, update `CHANGELOG.md`, commit `chore(release): vX.Y.Z`, tag, create a **GitHub Release**, and publish to the language registry when credentials are configured.

Skip with `[skip release]` in the commit message.
