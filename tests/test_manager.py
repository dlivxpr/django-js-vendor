import json

import pytest
from httpx import Response

from django_js_vendor.core import VendorError, VendorManager
from django_js_vendor.utils import calculate_content_sha256


@pytest.fixture
def manager(mock_project_root):
    return VendorManager(project_root=mock_project_root)


@pytest.mark.asyncio
async def test_sync_happy_path(manager, mock_pyproject, respx_mock):
    # Setup Config
    content = """
[tool.django-js-vendor.dependencies]
test-lib = "1.0.0"
    """
    mock_pyproject(content)
    # Reload config
    manager.config = manager.config.from_toml(manager.config_path)

    # Mock Network
    # Note: Default logic resolves test-lib to unpkg.com/test-lib@1.0.0/test-lib.js
    # We mock the redirect and the final file

    # We mock the response
    js_content = b"console.log('hello')"

    # Mock the unpkg URL with redirect to simulate real unpkg behavior
    # This ensures filename is correctly resolved to .js
    respx_mock.get("https://unpkg.com/test-lib@1.0.0").mock(
        return_value=Response(
            302,
            headers={"Location": "https://unpkg.com/test-lib@1.0.0/dist/test-lib.js"},
        )
    )
    final_route = respx_mock.get(
        "https://unpkg.com/test-lib@1.0.0/dist/test-lib.js"
    ).mock(return_value=Response(200, content=js_content))

    # Run Sync
    await manager.sync()

    # Assertions
    assert final_route.call_count == 1
    dest_path = manager.project_root / "static/vendor/test-lib/test-lib.js"
    assert dest_path.exists()
    assert dest_path.read_bytes() == js_content

    # Verify Lockfile
    assert manager.lock_path.exists()
    lock_data = json.loads(manager.lock_path.read_text(encoding="utf-8"))
    assert "test-lib" in lock_data
    file_entry = lock_data["test-lib"]["files"][0]
    assert file_entry["path"] == "static/vendor/test-lib/test-lib.js"
    assert file_entry["integrity"] == f"sha256-{calculate_content_sha256(js_content)}"


@pytest.mark.asyncio
async def test_idempotency(manager, mock_pyproject, respx_mock):
    # Setup Config
    content = """
[tool.django-js-vendor.dependencies]
test-lib = "1.0.0"
    """
    mock_pyproject(content)
    manager.config = manager.config.from_toml(manager.config_path)

    js_content = b"console.log('hello')"

    redirect_route = respx_mock.get("https://unpkg.com/test-lib@1.0.0").mock(
        return_value=Response(
            302,
            headers={"Location": "https://unpkg.com/test-lib@1.0.0/dist/test-lib.js"},
        )
    )
    final_route = respx_mock.get(
        "https://unpkg.com/test-lib@1.0.0/dist/test-lib.js"
    ).mock(return_value=Response(200, content=js_content))

    # First Sync
    await manager.sync()
    assert final_route.call_count == 1

    # Second Sync
    await manager.sync()
    # Should not call again because file exists and hash matches lock
    assert final_route.call_count == 1
    assert redirect_route.call_count == 1


@pytest.mark.asyncio
async def test_integrity_check_failure(manager, mock_pyproject, respx_mock):
    # Setup Config
    content = """
[tool.django-js-vendor.dependencies]
bad-lib = "1.0.0"
    """
    mock_pyproject(content)
    manager.config = manager.config.from_toml(manager.config_path)

    # Create a fake lockfile with WRONG hash
    fake_hash = "sha256-wronghash123456"
    lock_data = {
        "bad-lib": {
            "files": [
                {
                    "url": "https://unpkg.com/bad-lib@1.0.0",
                    "path": "static/vendor/bad-lib/bad-lib.js",
                    "integrity": fake_hash,
                }
            ]
        }
    }
    manager.save_lockfile(lock_data)

    # Mock Network
    js_content = b"console.log('malicious')"
    respx_mock.get("https://unpkg.com/bad-lib@1.0.0").mock(
        return_value=Response(200, content=js_content)
    )

    # Run Sync - Expect Error
    with pytest.raises(VendorError, match="Integrity check failed"):
        await manager.sync()

    # Assert File Not Written
    dest_path = manager.project_root / "static/vendor/bad-lib/bad-lib.js"
    assert not dest_path.exists()


@pytest.mark.asyncio
async def test_network_failure(manager, mock_pyproject, respx_mock):
    content = """
[tool.django-js-vendor.dependencies]
missing-lib = "1.0.0"
    """
    mock_pyproject(content)
    manager.config = manager.config.from_toml(manager.config_path)

    respx_mock.get("https://unpkg.com/missing-lib@1.0.0").mock(
        return_value=Response(404)
    )

    # Run Sync - Expect Error
    # VendorManager doesn't catch the exception in sync(), it propagates
    # But download_task catches and raises?
    # No, download_task catches Exception, logs it, and re-raises.
    # sync() gathers results, so it will raise.
    with pytest.raises(Exception):  # VendorError or HTTPError
        await manager.sync()
