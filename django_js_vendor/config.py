from dataclasses import dataclass, field
from pathlib import Path

import tomlkit


@dataclass
class DependencyConfig:
    """单个依赖的配置"""

    name: str
    version: str | None = None
    url: str | None = None
    filename: str | None = None
    files: list[str] = field(default_factory=list)


@dataclass
class VendorConfig:
    """全局配置"""

    destination: str
    default_provider: str
    dependencies: dict[str, DependencyConfig]

    @classmethod
    def from_toml(cls, path: Path = Path("pyproject.toml")) -> "VendorConfig":
        """
        从 pyproject.toml 加载配置。

        :param path: pyproject.toml 的路径
        :return: VendorConfig 实例
        """
        if not path.exists():
            # 默认配置
            return cls(
                destination="static/vendor", default_provider="unpkg", dependencies={}
            )

        with open(path, "r", encoding="utf-8") as f:
            data = tomlkit.load(f)

        tool_config = data.get("tool", {}).get("django-js-vendor", {})

        destination = tool_config.get("destination", "static/vendor")
        default_provider = tool_config.get("default_provider", "unpkg")
        raw_deps = tool_config.get("dependencies", {})

        dependencies = {}
        for name, value in raw_deps.items():
            if isinstance(value, str):
                # 简写模式: htmx = "1.9.10"
                dependencies[name] = DependencyConfig(name=name, version=value)
            elif isinstance(value, dict):
                # 详细模式
                dependencies[name] = DependencyConfig(
                    name=name,
                    version=value.get("version"),
                    url=value.get("url"),
                    filename=value.get("filename"),
                    files=value.get("files", []),
                )

        return cls(
            destination=destination,
            default_provider=default_provider,
            dependencies=dependencies,
        )

    @staticmethod
    def add_dependency_to_toml(path: Path, name: str, version: str) -> None:
        """
        使用 tomlkit 安全地添加依赖到 pyproject.toml。

        :param path: 文件路径
        :param name: 包名
        :param version: 版本号
        """
        if not path.exists():
            # Create new file if not exists? Or raise?
            # Usually pyproject.toml exists. If not, create minimal.
            doc = tomlkit.document()
        else:
            with open(path, "r", encoding="utf-8") as f:
                doc = tomlkit.load(f)

        # Ensure table structure
        if "tool" not in doc:
            doc["tool"] = tomlkit.table()
        if "django-js-vendor" not in doc["tool"]:
            doc["tool"]["django-js-vendor"] = tomlkit.table()
        if "dependencies" not in doc["tool"]["django-js-vendor"]:
            doc["tool"]["django-js-vendor"]["dependencies"] = tomlkit.table()

        # Add dependency
        doc["tool"]["django-js-vendor"]["dependencies"][name] = version

        with open(path, "w", encoding="utf-8") as f:
            tomlkit.dump(doc, f)

    @staticmethod
    def remove_dependency_from_toml(path: Path, name: str) -> None:
        """
        使用 tomlkit 安全地移除依赖。

        :param path: 文件路径
        :param name: 包名
        """
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            doc = tomlkit.load(f)

        try:
            deps = doc["tool"]["django-js-vendor"]["dependencies"]
            if name in deps:
                del deps[name]
                with open(path, "w", encoding="utf-8") as f:
                    tomlkit.dump(doc, f)
        except KeyError:
            pass
