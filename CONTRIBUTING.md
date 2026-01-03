# Contributing to Django JS Vendor

Thank you for your interest in contributing to Django JS Vendor! We welcome contributions from everyone.

## Development Setup

This project uses `uv` for dependency management.

1.  **Clone the repository**

    ```bash
    git clone https://github.com/dlivxpr/django-js-vendor.git
    cd django-js-vendor
    ```

2.  **Install dependencies**

    ```bash
    uv sync
    ```

3.  **Run tests**

    ```bash
    uv run pytest
    ```

## Coding Standards

*   **Python Version**: We support Python 3.10+.
*   **Formatting**: We use `ruff` for linting and formatting.
*   **Type Hints**: Please use type hints for all function arguments and return values.

## Pull Request Process

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Add tests for your changes.
4.  Ensure all tests pass.
5.  Submit a Pull Request.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
