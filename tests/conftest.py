import os
import sys
from pathlib import Path

import django
import pytest
from django.conf import settings

# 将项目根目录添加到 sys.path，解决 ModuleNotFoundError
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure():
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django_js_vendor",
            ],
            SECRET_KEY="test",
            STATIC_URL="/static/",
        )
        django.setup()


@pytest.fixture
def mock_project_root(tmp_path):
    """
    提供一个临时的项目根目录。
    """
    # 切换当前工作目录到 tmp_path，确保测试隔离
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)


@pytest.fixture
def mock_pyproject(mock_project_root):
    """
    创建一个临时的 pyproject.toml 文件。
    """

    def _create(content: str):
        path = mock_project_root / "pyproject.toml"
        path.write_text(content, encoding="utf-8")
        return path

    return _create
