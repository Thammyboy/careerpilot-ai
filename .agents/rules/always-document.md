# Rule: Mandatory Change Documentation

Whenever you modify, add, or delete files (source code, configs, models, scrapers, CLI):

1. **User Documentation Sync**:
   - Update `README.md` if any CLI commands, arguments, setup steps, or environment parameters changed.
   - Update `profile/README.md` if profile models or file structures changed.
   - Update `.env.example` if any settings or environment variables were added/modified.

2. **Changelog Maintenance**:
   - Record the changes in `CHANGELOG.md` under `[Unreleased]`.
   - Categorize by `Added`, `Changed`, `Fixed`, `Removed`, or `Security`.

3. **Atomic Verification**:
   - Verify that tests pass (`.\.venv\Scripts\pytest -v`).
   - Ensure working tree is clean and documentation accurately reflects active code.
