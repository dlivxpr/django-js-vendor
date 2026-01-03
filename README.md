# Django JS Vendor

Django JS Vendor 是一个轻量级的前端依赖管理工具，旨在为 Django 项目提供类似 `cargo` 或 `pnpm` 的体验，无需引入 Node.js 环境。

## 特性

- **轻量级**: 纯 Python 实现，无 Node.js 依赖。
- **声明式配置**: 使用 `pyproject.toml` 管理依赖。
- **版本锁定**: 自动生成 `js-vendor.lock` 确保生产环境一致性。
- **并发下载**: 使用 `httpx` 和 `asyncio` 快速并发下载。
- **CDN 支持**: 默认支持 `unpkg`，可扩展。

## 安装

### 使用 uv (推荐)

```bash
uv add django-js-vendor
```

### 使用 pip

```bash
pip install django-js-vendor
```

将 `django_js_vendor` 添加到 `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django_js_vendor",
]
```

## 配置

在项目的 `pyproject.toml` 中添加 `[tool.django-js-vendor]`：

```toml
[tool.django-js-vendor]
# 下载目录 (默认为 static/vendor)
destination = "static/vendor"
# 默认 CDN (目前支持 unpkg)
default_provider = "unpkg"

[tool.django-js-vendor.dependencies]
# 简写模式 (自动获取最新版或指定版本)
"htmx.org" = "1.9.10"
alpinejs = "3.13.3"

# 详细模式
jquery = { version = "3.7.1", files = ["dist/jquery.min.js", "dist/jquery.min.map"] }
```

## 使用命令

### 同步依赖

下载 `pyproject.toml` 中定义的所有依赖，并生成/更新 `js-vendor.lock`。

```bash
python manage.py vendor sync
```

### 添加依赖

添加新包到配置并下载。

```bash
python manage.py vendor add htmx.org
python manage.py vendor add alpinejs 3.13.0
```

### 更新依赖

更新依赖并刷新 lock 文件。

```bash
python manage.py vendor update
```

## 开发指南

本项目使用 `uv` 进行依赖管理和任务执行。

### 1. 获取代码

```bash
git clone https://github.com/dlivxpr/django-js-vendor.git
cd django-js-vendor
```

### 2. 安装环境

使用 `uv sync` 安装项目依赖（包括开发依赖）：

```bash
uv sync
```

### 3. 运行测试

使用 `uv run` 执行测试套件：

```bash
uv run pytest
```

### 4. 代码检查

```bash
uv run ruff check .
```
