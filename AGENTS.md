# Repository Guidelines

## Project Structure & Module Organization
- `radarr_extractor/`: app code
  - `main.py`: Flask webhook + watchdog runner
  - `core.py`: extraction logic and Radarr API notify
  - `config.py`: env vars, logging, paths
  - `tracker.py`: de-dup tracking of processed files
- `tests/`: unit tests (pytest/unittest), e.g., `test_core.py`
- `docker/`: container assets (e.g., `entrypoint.sh`)
- `Dockerfile`, `docker-compose.yml`: container build/run
- `docs/`, `build/`: supplementary docs and artifacts

## Build, Test, and Development Commands
- Create env: `python3 -m venv venv && source venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run app (local): `python -m radarr_extractor.main`
- Run tests: `python -m pytest tests/`
- Docker (compose): `docker-compose up -d`
- Docker (build): `docker build -t radarr-extractor:dev .` or `./docker-build.sh`

## Coding Style & Naming Conventions
- Python 3.9+ recommended; follow PEP 8 with 4-space indents.
- Names: modules/files/functions `snake_case`; classes `PascalCase`; tests `test_*.py`.
- Use type hints and docstrings for new/changed functions.
- Logging: use `config.logger` instead of `print` (keep messages actionable).
- Side effects (filesystem, network) behind small, testable helpers.

## Testing Guidelines
- Framework: `pytest` executing `unittest`-style tests.
- Place tests under `tests/`; name files `test_*.py` and mirror module names when possible.
- Mock external IO (`requests`, `rarfile`, filesystem) and use temp dirs; see `tests/test_core.py` for patterns (e.g., patch `EXTRACTED_DIR`).
- Run focused tests: `pytest tests/test_core.py -q`. Aim to cover new code paths and error handling.

## Commit & Pull Request Guidelines
- Commits: imperative, concise subject (<72 chars). Use tags when helpful: `feat:`, `fix:`, `refactor:`.
- Reference issues (`#123`) and summarize user impact; include logs or repro steps when fixing.
- PRs: clear description of what/why, how tested (commands/logs), config or Docker changes, and any doc updates. Keep diffs minimal and scoped.

## Security & Configuration Tips
- Never commit secrets. Provide `RADARR_API_KEY`, `RADARR_URL`, `DOWNLOAD_DIR`, `WEBHOOK_PORT` via env or `.env` (local only).
- Ensure `DOWNLOAD_DIR` is readable/writable; `EXTRACTED_DIR` is created automatically.
- For webhooks, expose port `9898` and verify Radarr Connect settings.
