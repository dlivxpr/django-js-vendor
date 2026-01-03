from django_js_vendor.config import VendorConfig


def test_config_defaults(mock_project_root):
    """测试默认配置（无 pyproject.toml）"""
    # 确保没有 pyproject.toml
    config_path = mock_project_root / "pyproject.toml"
    if config_path.exists():
        config_path.unlink()

    config = VendorConfig.from_toml()
    assert config.destination == "static/vendor"
    assert config.default_provider == "unpkg"
    assert config.dependencies == {}


def test_valid_config(mock_pyproject):
    """测试有效的配置解析"""
    content = """
[tool.django-js-vendor]
destination = "my_static/libs"
default_provider = "cdnjs"

[tool.django-js-vendor.dependencies]
htmx = "1.9.10"
jquery = { version = "3.7.1", files = ["dist/jquery.min.js"] }
    """
    mock_pyproject(content)
    config = VendorConfig.from_toml()

    assert config.destination == "my_static/libs"
    assert config.default_provider == "cdnjs"
    assert "htmx" in config.dependencies
    assert config.dependencies["htmx"].version == "1.9.10"
    assert "jquery" in config.dependencies
    assert config.dependencies["jquery"].version == "3.7.1"
    assert config.dependencies["jquery"].files == ["dist/jquery.min.js"]


def test_missing_section(mock_pyproject):
    """测试 pyproject.toml 存在但缺少 django-js-vendor 部分"""
    content = """
[tool.other-tool]
foo = "bar"
    """
    mock_pyproject(content)
    config = VendorConfig.from_toml()
    # 应该回退到默认值
    assert config.destination == "static/vendor"
    assert config.dependencies == {}
