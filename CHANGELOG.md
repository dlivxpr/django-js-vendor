# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-03

### Added
- Initial release of Django JS Vendor.
- Support for syncing dependencies from `pyproject.toml`.
- Support for `unpkg` as the default provider.
- Concurrent downloading using `httpx` and `asyncio`.
- CLI commands: `sync`, `add`, `update`, `remove`.
- Integrity checking with SHA256.
- `js-vendor.lock` for reproducible builds.
