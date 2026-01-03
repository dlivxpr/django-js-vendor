import json
from pathlib import Path

from django_js_vendor.templatetags.vendor_tags import render_vendor_assets


def test_render_vendor_assets_empty(mock_project_root):
    """Test rendering when no config or lockfile exists."""
    output = render_vendor_assets()
    assert output == ""


def test_render_vendor_assets_basic(mock_project_root, mock_pyproject):
    """Test basic rendering with JS files."""
    # settings.STATIC_URL is set in conftest.py

    # 1. Setup pyproject.toml
    mock_pyproject("""
[tool.django-js-vendor]
dependencies = { htmx = "1.0", alpine = "3.0" }
    """)

    # 2. Setup js-vendor.lock
    lock_data = {
        "htmx": {
            "files": [
                {
                    "path": "static/vendor/htmx/htmx.js",
                    "url": "...",
                    "integrity": "...",
                }
            ]
        },
        "alpine": {
            "files": [
                {
                    "path": "static/vendor/alpine/alpine.js",
                    "url": "...",
                    "integrity": "...",
                }
            ]
        },
    }
    (mock_project_root / "js-vendor.lock").write_text(
        json.dumps(lock_data), encoding="utf-8"
    )

    # 3. Call tag
    output = render_vendor_assets()

    assert '<script src="/static/vendor/htmx/htmx.js" defer></script>' in output
    assert '<script src="/static/vendor/alpine/alpine.js" defer></script>' in output

    # Check order: htmx then alpine (as in pyproject.toml)
    assert output.index("htmx.js") < output.index("alpine.js")


def test_render_vendor_assets_args(mock_project_root, mock_pyproject):
    """Test rendering with specific arguments."""

    mock_pyproject("""
[tool.django-js-vendor]
dependencies = { htmx = "1.0", alpine = "3.0" }
    """)

    lock_data = {
        "htmx": {"files": [{"path": "static/vendor/htmx/htmx.js"}]},
        "alpine": {"files": [{"path": "static/vendor/alpine/alpine.js"}]},
    }
    (mock_project_root / "js-vendor.lock").write_text(
        json.dumps(lock_data), encoding="utf-8"
    )

    output = render_vendor_assets("alpine")

    assert "alpine.js" in output
    assert "htmx.js" not in output


def test_render_vendor_assets_css(mock_project_root, mock_pyproject):
    """Test rendering with CSS files."""

    mock_pyproject("""
[tool.django-js-vendor]
dependencies = { bootstrap = "5.0" }
    """)

    lock_data = {
        "bootstrap": {"files": [{"path": "static/vendor/bootstrap/bootstrap.css"}]}
    }
    (mock_project_root / "js-vendor.lock").write_text(
        json.dumps(lock_data), encoding="utf-8"
    )

    output = render_vendor_assets()

    assert '<link rel="stylesheet" href="/static/vendor/bootstrap/bootstrap.css">' in output


def test_render_vendor_assets_path_stripping(mock_project_root, mock_pyproject):
    """Test that 'static/' prefix is stripped from paths."""

    mock_pyproject("""
[tool.django-js-vendor]
dependencies = { foo = "1.0" }
    """)

    lock_data = {
        "foo": {"files": [{"path": "static/vendor/foo/foo.js"}]}
    }
    (mock_project_root / "js-vendor.lock").write_text(
        json.dumps(lock_data), encoding="utf-8"
    )

    output = render_vendor_assets()
    # path in lock: static/vendor/foo/foo.js
    # stripped: vendor/foo/foo.js
    # static url: /static/vendor/foo/foo.js
    assert 'src="/static/vendor/foo/foo.js"' in output


def test_render_vendor_assets_non_static_path(
    mock_project_root, mock_pyproject
):
    """Test that paths not starting with 'static/' are preserved."""

    mock_pyproject("""
[tool.django-js-vendor]
dependencies = { foo = "1.0" }
    """)

    lock_data = {
        "foo": {"files": [{"path": "assets/vendor/foo/foo.js"}]}
    }
    (mock_project_root / "js-vendor.lock").write_text(
        json.dumps(lock_data), encoding="utf-8"
    )

    output = render_vendor_assets()
    # path in lock: assets/vendor/foo/foo.js
    # not stripped
    # static url: /static/assets/vendor/foo/foo.js
    assert 'src="/static/assets/vendor/foo/foo.js"' in output
