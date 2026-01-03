from io import StringIO
from unittest.mock import AsyncMock

from django.core.management import call_command


def test_command_sync(mocker):
    """测试 vendor sync 命令"""
    # Mock VendorManager
    mock_manager_cls = mocker.patch(
        "django_js_vendor.management.commands.vendor.VendorManager"
    )
    mock_instance = mock_manager_cls.return_value
    mock_instance.sync = AsyncMock()

    out = StringIO()
    call_command("vendor", "sync", stdout=out)

    mock_instance.sync.assert_called_once()
    assert "Dependencies synced successfully" in out.getvalue()


def test_command_add(mocker):
    """测试 vendor add 命令"""
    mock_manager_cls = mocker.patch(
        "django_js_vendor.management.commands.vendor.VendorManager"
    )
    mock_instance = mock_manager_cls.return_value
    mock_instance.add = AsyncMock()

    out = StringIO()
    call_command("vendor", "add", "htmx", "1.9.10", stdout=out)

    mock_instance.add.assert_called_with("htmx", "1.9.10")
    assert "Added htmx" in out.getvalue()


def test_command_remove(mocker):
    """测试 vendor remove 命令"""
    mock_manager_cls = mocker.patch(
        "django_js_vendor.management.commands.vendor.VendorManager"
    )
    mock_instance = mock_manager_cls.return_value
    mock_instance.remove = AsyncMock()

    out = StringIO()
    call_command("vendor", "remove", "htmx", stdout=out)

    mock_instance.remove.assert_called_with("htmx")
    assert "Removed htmx" in out.getvalue()
