# Contributing

Thanks for helping improve the Praxicraft Python SDK.

## Local setup

```bash
git clone https://github.com/praxicraft-platform/praxicraft-python.git
cd praxicraft-python
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
```

## Guidelines

- This package is a thin wrapper around the [Assess Public API](https://docs.praxicraft.com). Prefer matching documented paths and error codes over inventing new abstractions.
- Keep HTTP mocked in tests (`pytest-httpx`). Do not call production from CI.
- Public exports live in `src/praxicraft/__init__.py` — update `__all__` when adding symbols.
- For release / PyPI steps, see [RELEASING.md](RELEASING.md).

## Pull requests

1. Open a PR against `main`.
2. Ensure `pytest -q` is green locally; CI runs on 3.10–3.12.
3. Describe the user-facing change briefly in the PR body.
