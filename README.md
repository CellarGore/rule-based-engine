# rule-based-engine

A config-driven underwriting engine. Business rules, eligibility questions, and
pricing logic are authored entirely in YAML (one directory per jurisdiction)
and served through a small FastAPI application. Adding a new state or changing
a rule is a YAML edit, not a code change.

The engine answers three questions for a given state, in order:

1. **What do we need to ask?** - `GET /api/questions`
2. **Given the answers, do we approve, decline, or refer?** - `POST /api/decision`
3. **If approved, what's the premium?** - also `POST /api/decision`

Everything runs in memory and config is read from disk on each request.

## Requirements

- Python 3.9 or later (developed and tested on 3.14)
- `pip` (ships with Python)

No other system dependencies. No database to provision.

## Setup

Clone the repo, then from the project root:

```bash
# 1. Create an isolated virtual environment (do this once)
python3 -m venv venv

# 2. Activate it (do this every time you open a new shell)
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate.bat       # Windows (cmd.exe)
venv\Scripts\Activate.ps1       # Windows (PowerShell)

# 3. Install dependencies into the venv
pip install -r requirements.txt
```

A virtual environment keeps this project's dependencies (FastAPI, Uvicorn,
PyYAML - see `requirements.txt`) isolated from whatever else is installed on
your machine. `pip install -r requirements.txt` reads that file and installs
exactly those packages, pinned to what's listed there. If you add a new
dependency, install it with `pip install <package>` and then update the file
with `pip freeze > requirements.txt` (or add the line by hand).

You'll know the venv is active because your shell prompt is prefixed with
`(venv)`. If you ever see `command not found: uvicorn` or `ModuleNotFoundError:
No module named 'fastapi'`, it almost always means the venv isn't activated -
re-run step 2, or invoke the binary directly with `venv/bin/uvicorn` /
`venv/bin/pip`.

To leave the venv: `deactivate`.

## Running the API

```bash
uvicorn app.main:app --reload
```

`--reload` restarts the server on code changes; drop it for anything
resembling a production run. The API is now listening on
`http://127.0.0.1:8000`.

FastAPI generates interactive API docs for free:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Raw OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

A snapshot of that schema is checked in at [`openapi.json`](openapi.json) and
can be imported directly into Postman (Import → File) to get a ready-made
collection for both endpoints.

## API

### `GET /api/questions?state={state}`

Returns the question set for a state, straight from
`config/{state}/questions.yaml`, JSON-encoded.

```bash
curl "http://127.0.0.1:8000/api/questions?state=california"
```

| Status | When |
|---|---|
| `200` | Questions returned |
| `400` | `state` query parameter missing |
| `404` | No config directory for that state |

### `POST /api/decision?state={state}`

Takes the client's answers, evaluates `rules.yaml` for that state, and - if
the outcome is `approve` - calculates a premium from `rating.yaml`.

```bash
curl -X POST "http://127.0.0.1:8000/api/decision?state=california" \
  -H "Content-Type: application/json" \
  -d '{
        "answers": {
          "business_type": "office",
          "annual_payroll": 200000,
          "employee_count": 12,
          "workers_comp_claims": 0,
          "safety_program": true
        }
      }'
```

```json
{ "status": "approve", "reason": null, "premium": 700.0 }
```

`status` is one of `approve` / `decline` / `refer`. `reason` is the `name` of
the deciding rule, and is `null` when `status` is `approve`. `premium` is only
populated when `status` is `approve`; otherwise it's `null`.

| Status | When |
|---|---|
| `200` | Decision (and premium, if approved) returned |
| `400` | `state` query parameter missing |
| `404` | No `rules.yaml` / `rating.yaml` for that state |
| `422` | Request body malformed, or the answers can't produce a premium (e.g. unknown `business_type`, non-numeric `annual_payroll`) |

## Configuration format

Each state gets its own directory under `config/`, e.g. `config/california/`,
containing three files:

**`questions.yaml`** - the question set returned as-is by `GET /api/questions`.

**`rules.yaml`** - an ordered list of eligibility rules:

```yaml
rules:
  - name: Roofing contractors are ineligible
    when:
      field: business_type
      operator: eq
      value: roofing_contractor
    decision: decline
```

`when` conditions can be a single `field` / `operator` / `value` leaf, or a
group combining sub-conditions with `all` (AND) / `any` (OR), nested as deep
as needed. Supported operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`,
`not_in`. Every rule whose condition is true "fires"; if more than one fires,
the most severe decision wins (`decline` > `refer` > `approve`), and the
`reason` returned is the `name` of the first rule that reached that severity.

**`rating.yaml`** - a base rate per `business_type`, plus optional
adjustments:

```yaml
base_rates:
  office: 0.35

adjustments:
  - name: Workers' compensation claims surcharge
    when:
      field: workers_comp_claims
      operator: gt
      value: 0
    action:
      type: multiplier
      value: 1.03
```

Premium is calculated as `base_rates[business_type] * (annual_payroll / 100)`,
then each matching adjustment's action is applied in order (currently only
`multiplier` is supported), rounded to 2 decimal places.

Adding a new state is purely additive: create `config/<state>/` with the same
three files and it's immediately servable - no code changes required.

## Architecture

```
app/
  main.py               FastAPI app instance, router registration
  schemas.py             Pydantic request/response models
  routers/                Thin HTTP controllers - validate input, call a
                          service, translate results/errors to responses
    questions.py
    decision.py
  services/               Framework-agnostic domain logic
    config_loader.py       Reads a state's YAML files from config/
    conditions.py          Shared `when`-clause evaluator (rules + rating
                            adjustments use the same condition schema)
    rules_engine.py         Applies rules.yaml -> decision + reason
    rating_engine.py        Applies rating.yaml -> premium
```

Routers own no business logic - they parse the request, delegate to a
service, and map service-level exceptions to HTTP status codes. Everything
under `services/` is plain Python and testable without spinning up FastAPI.

## Project status

No automated test suite yet - endpoints have been verified manually via
`curl` and the `/docs` UI. `texas` exists as an empty config directory,
reserved for a second state.
