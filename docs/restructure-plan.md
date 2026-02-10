# Floportop Restructure Plan

Created: 2026-02-07
Status: Draft (safe, incremental migration)

## Goals

1. Cleanly separate runtime code, deployment assets, and training/dev artifacts.
2. Reduce Docker build context and image bloat.
3. Keep deployment stable during migration (no big-bang moves).
4. Make file paths configurable so folder moves do not break runtime.

## Target Structure

```text
floportop/
├── apps/
│   ├── api/
│   └── frontend/
├── src/
│   └── floportop/
├── models/
│   └── manifests/
├── requirements/
│   ├── prod.in
│   ├── prod.lock
│   └── dev.txt
├── deploy/
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── .dockerignore
│   └── cloudbuild.yaml
├── scripts/
│   ├── build/
│   └── dev/
├── data/                 # local/dev only, not in production image
├── notebooks/            # local/dev only
├── docs/
├── .env.example
└── README.md
```

## Migration Strategy

Use phased migration with a working deployment after each phase.

### Phase 0: Baseline and Guardrails

- Snapshot current behavior:
  - `uvicorn api.app:app --reload`
  - `streamlit run frontend/app.py`
  - `docker build -t floportop:baseline .`
- Record expected health check response: `GET /` returns status online.
- Record current image size and cold start time.

Exit criteria:
- Local API and frontend work.
- Baseline Docker image builds successfully.

### Phase 1: Path Configuration (No Moves Yet)

- Add central path config module (for package and app roots).
- Replace hard-coded `Path(__file__).parent.parent / ...` usage in:
  - `floportop/movie_search.py`
  - `floportop/model.py`
  - `floportop/preprocessing.py`
- Add env overrides:
  - `FLOPORTOP_MODELS_DIR`
  - `FLOPORTOP_CACHE_DIR`
  - `FLOPORTOP_DATA_DIR`

Exit criteria:
- App works with default paths.
- App also works when dirs are provided via env vars.

### Phase 2: Dependency and Packaging Cleanup

- Move dependency files:
  - `requirements-prod.in` -> `requirements/prod.in`
  - `requirements-prod.lock` -> `requirements/prod.lock`
  - `requirements_dev.txt` -> `requirements/dev.txt`
- Update references in:
  - `Dockerfile`
  - `Makefile`
  - `setup.py` (or migrate to `pyproject.toml`)
- Keep temporary compatibility symlinks or fallback logic for one phase if needed.

Exit criteria:
- Install commands still work.
- Docker build uses `requirements/prod.lock`.

### Phase 3: Docker Hygiene (Before Structural Moves)

- Replace `.dockerignore` with allowlist approach.
- Remove broad `COPY . .` from Dockerfile.
- Use explicit `COPY` for runtime files only.
- Keep models policy explicit:
  - Small tracked artifacts in git.
  - Large binary artifacts from GCS/artifact storage.
- Decide CI engine:
  - If staying on Kaniko, avoid BuildKit-only syntax.
  - If using BuildKit, update `cloudbuild.yaml` accordingly.

Exit criteria:
- Docker context size reduced.
- Image builds in CI and locally.
- Runtime behavior unchanged.

### Phase 4: Deploy Assets Move

- Move:
  - `Dockerfile` -> `deploy/docker/Dockerfile`
  - `.dockerignore` -> `deploy/docker/.dockerignore`
  - `cloudbuild.yaml` -> `deploy/cloudbuild.yaml`
- Update build commands:
  - Local: `docker build -f deploy/docker/Dockerfile .`
  - GCP: `gcloud builds submit --config deploy/cloudbuild.yaml .`

Exit criteria:
- Build and deploy commands succeed with new paths.

### Phase 5: Code Layout Move

- Move:
  - `api/` -> `apps/api/`
  - `frontend/` -> `apps/frontend/`
  - `floportop/` -> `src/floportop/`
- Update imports and run commands:
  - API app module path
  - Streamlit entry path
  - `start.sh` process commands
- Remove `sys.path.insert(...)` hack from API after proper packaging.

Exit criteria:
- API and frontend run from new locations.
- No runtime import hacks needed.

### Phase 6: Training/Artifacts Separation

- Keep production runtime free of:
  - `data/`
  - `notebooks/`
  - generated logos/assets not needed by app
- Move dev/training helpers into `scripts/dev` and `scripts/build`.
- Add or update `.gitignore` and `.dockerignore` rules.

Exit criteria:
- Production image excludes non-runtime directories.
- Developer workflows still documented and reproducible.

### Phase 7: Documentation and Final Cleanup

- Update README structure and run instructions.
- Add a short deploy runbook in `docs/`.
- Remove temporary compatibility code/symlinks.
- Tag release after successful smoke tests.

Exit criteria:
- Docs match actual layout.
- No deprecated paths remain.

## Validation Matrix (Run After Each Phase)

1. `uvicorn <api_module>:app --host 0.0.0.0 --port 8080`
2. `curl http://localhost:8080/`
3. `streamlit run <frontend_entry> --server.port=8501`
4. `docker build -f <dockerfile_path> -t floportop:test .`
5. `docker run -p 8080:8080 -p 8501:8501 floportop:test`
6. `curl http://localhost:8080/`

## Risks and Mitigations

- Risk: Import breakage during `src/` migration.
  - Mitigation: Introduce path config first, then move code.
- Risk: CI build failure after Docker/deploy move.
  - Mitigation: Update `Makefile` and test `gcloud builds submit` immediately.
- Risk: Hidden notebook/script path dependencies.
  - Mitigation: Search and patch all path references with `rg`.
- Risk: Runtime missing model artifacts.
  - Mitigation: Validate model download paths and startup logs in container.

## Rollback Plan

1. Keep each phase in a separate commit.
2. If phase fails in CI or runtime smoke tests, revert only that phase commit.
3. Do not start next phase until previous phase exit criteria pass.

## Suggested Commit Sequence

1. `chore(paths): centralize model/cache/data path configuration`
2. `chore(deps): move dependency files under requirements/`
3. `chore(docker): allowlist docker context and explicit copy`
4. `chore(deploy): move Docker and Cloud Build files under deploy/`
5. `refactor(layout): move runtime code to apps/ and src/`
6. `chore(cleanup): finalize docs and remove compatibility shims`
