# Development Notes

## Source of truth

- Runtime application code lives under `app/`.
- `run.py` is the primary entrypoint.
- `app.py` is only a compatibility launcher for older commands.
- Database schema changes should go through Alembic migrations in `migrations/`.

## Common commands

```powershell
# Run the app
python run.py

# Apply migrations
.\.venv\Scripts\flask.exe --app run.py db upgrade

# Create a new migration after model changes
$env:DB_AUTO_CREATE='0'
$env:DB_LEGACY_AUTO_REPAIR='0'
$env:RUN_STARTUP_TASKS='0'
.\.venv\Scripts\flask.exe --app run.py db migrate -m "describe change"
```

## Notes

- Keep `DB_AUTO_CREATE=1` only for local convenience. Production should rely on `flask db upgrade`.
- Keep `AUTO_CREATE_DEFAULT_ADMIN` disabled outside development.
- When running maintenance commands, set `RUN_STARTUP_TASKS=0` to avoid automatic backup side effects.
