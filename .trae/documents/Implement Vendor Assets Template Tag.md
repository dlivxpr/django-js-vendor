I have completed the improvements based on the suggestions.

### Summary of Changes

1. **Enhanced Configuration Management**:

   * Introduced `tomlkit` to safely read and modify `pyproject.toml` without losing comments or formatting.

   * Refactored `VendorConfig` to support programmatic `add` and `remove` operations.

2. **Improved** **`add`** **Command**:

   * Now automatically detects the latest version from `unpkg` redirects if no version is specified (e.g., `vendor add htmx` -> `htmx = "1.9.10"`).

   * Uses `tomlkit` to insert the dependency into `pyproject.toml` safely.

3. **Implemented** **`remove`** **Command**:

   * Added `python manage.py vendor remove <package_name>` command.

   * It removes the dependency from `pyproject.toml`.

   * Deletes the downloaded files from `static/vendor`.

   * Updates `js-vendor.lock` to remove the entry.

4. **Verification**:

   * Added new tests in `tests/test_manager_advanced.py` covering version autodetection and dependency removal.

   * All 11 tests passed.

You can now use:

```bash
python manage.py vendor add htmx          # Auto-detects version
python manage.py vendor remove htmx       # Removes config and files
```

