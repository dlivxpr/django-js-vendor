import pytest
from httpx import Response

from django_js_vendor.core import VendorManager


@pytest.fixture
def manager(mock_project_root):
    return VendorManager(project_root=mock_project_root)


@pytest.mark.asyncio
async def test_add_dependency_autodetect(manager, mock_pyproject, respx_mock):
    # Setup: Empty pyproject.toml
    content = """
[tool.django-js-vendor]
destination = "static/vendor"
    """
    mock_pyproject(content)

    # Mock Network
    # HEAD request for version detection
    respx_mock.head("https://unpkg.com/new-lib").mock(
        return_value=Response(
            302,
            headers={"Location": "https://unpkg.com/new-lib@2.0.0/dist/new-lib.js"},
        )
    )
    # Mock the HEAD request to the redirected URL (since follow_redirects=True)
    respx_mock.head("https://unpkg.com/new-lib@2.0.0/dist/new-lib.js").mock(
        return_value=Response(200)
    )

    # GET request for install (via sync -> resolve_cdn_url -> download_task)
    # Note: add() calls sync(), which calls resolve_cdn_url.
    # resolve_cdn_url returns https://unpkg.com/new-lib@2.0.0, which also redirects
    respx_mock.get("https://unpkg.com/new-lib@2.0.0").mock(
        return_value=Response(
            302,
            headers={"Location": "https://unpkg.com/new-lib@2.0.0/dist/new-lib.js"},
        )
    )
    respx_mock.get("https://unpkg.com/new-lib@2.0.0/dist/new-lib.js").mock(
        return_value=Response(200, content=b"console.log('new lib')")
    )

    # Run Add
    await manager.add("new-lib")

    # Assert pyproject.toml updated
    assert manager.config_path.exists()
    content = manager.config_path.read_text(encoding="utf-8")
    assert 'new-lib = "2.0.0"' in content

    # Assert file installed
    dest_path = manager.project_root / "static/vendor/new-lib/new-lib.js"
    assert dest_path.exists()
    assert dest_path.read_bytes() == b"console.log('new lib')"


@pytest.mark.asyncio
async def test_remove_dependency(manager, mock_pyproject, respx_mock):
    # Setup: Existing dependency
    content = """
[tool.django-js-vendor.dependencies]
old-lib = "1.0.0"
    """
    mock_pyproject(content)

    # Create fake installed file
    dest_dir = manager.project_root / "static/vendor/old-lib"
    dest_dir.mkdir(parents=True)
    (dest_dir / "old-lib.js").write_text("content")

    # Create fake lock file
    lock_data = {
        "old-lib": {
            "files": [
                {
                    "url": "...",
                    "path": "static/vendor/old-lib/old-lib.js",
                    "integrity": "...",
                }
            ]
        }
    }
    manager.save_lockfile(lock_data)

    # Run Remove
    await manager.remove("old-lib")

    # Assert pyproject.toml updated
    content = manager.config_path.read_text(encoding="utf-8")
    assert "old-lib" not in content

    # Assert file removed
    assert not dest_dir.exists()

    # Assert lockfile updated
    lock_data = manager.load_lockfile()
    assert "old-lib" not in lock_data
