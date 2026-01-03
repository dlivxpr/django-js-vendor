import asyncio
import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from tqdm import tqdm

from .config import DependencyConfig, VendorConfig
from .utils import calculate_content_sha256

logger = logging.getLogger(__name__)


class VendorError(Exception):
    """Base exception for vendor errors."""

    pass


class VendorManager:
    """核心依赖管理逻辑"""

    def __init__(self, project_root: Path = Path(".")):
        self.project_root = project_root
        self.config_path = project_root / "pyproject.toml"
        self.lock_path = project_root / "js-vendor.lock"
        self.config = VendorConfig.from_toml(self.config_path)

    def load_lockfile(self) -> dict[str, Any]:
        """读取 Lock 文件"""
        if not self.lock_path.exists():
            return {}
        try:
            with open(self.lock_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Lock file is corrupted. Ignoring.")
            return {}

    def save_lockfile(self, lock_data: dict[str, Any]) -> None:
        """保存 Lock 文件"""
        with open(self.lock_path, "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2, sort_keys=True)

    async def download_file(
        self,
        client: httpx.AsyncClient,
        url: str,
        dest_path: Path,
        expected_hash: str | None = None,
    ) -> str:
        """
        异步下载文件并校验 Hash。

        :param client: HTTPX 客户端
        :param url: 下载链接
        :param dest_path: 本地目标路径
        :param expected_hash: 期望的 SHA256 哈希值
        """
        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            content = response.content
        except httpx.HTTPError as e:
            raise VendorError(f"Failed to download {url}: {e}")

        # Hash Check
        content_hash = calculate_content_sha256(content)
        if expected_hash and content_hash != expected_hash:
            raise VendorError(
                f"Hash mismatch for {url}. Expected {expected_hash}, got {content_hash}"
            )

        # Save file
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(content)

        return content_hash

    def resolve_cdn_url(self, dep: DependencyConfig) -> list[tuple[str, str]]:
        """
        将依赖配置解析为 (URL, 相对路径) 的列表。

        :param dep: 依赖配置对象
        """
        urls = []

        # 1. 显式 URL
        if dep.url:
            filename = dep.filename or Path(urlparse(dep.url).path).name
            urls.append((dep.url, filename))
            return urls

        # 2. Files 列表 (通常配合 unpkg)
        if dep.files:
            version_part = f"@{dep.version}" if dep.version else ""
            base_url = f"https://unpkg.com/{dep.name}{version_part}"
            for file_rel_path in dep.files:
                # unpkg 路径拼接
                url = f"{base_url}/{file_rel_path}"
                urls.append((url, file_rel_path))
            return urls

        # 3. 默认推导 (Main file from unpkg)
        # 如果没有指定 files，我们假设用户想要这个包的主文件
        # 这对于像 htmx 这样的单文件库很有用
        # 但对于多文件库，这可能不够准确。
        # 简单起见，我们尝试获取 `https://unpkg.com/{name}@{version}`
        # 注意：unpkg 会重定向到主文件。我们需要在下载时处理重定向并确定文件名。
        version_part = f"@{dep.version}" if dep.version else ""
        url = f"https://unpkg.com/{dep.name}{version_part}"
        # 文件名暂时未知，下载时决定，或者默认为 name.js
        # 这里我们标记文件名为空，下载器需要处理
        urls.append((url, f"{dep.name}.js"))
        return urls

    async def sync(self) -> None:
        """同步所有依赖"""
        lock_data = self.load_lockfile()
        new_lock_data = {}

        tasks = []
        timeout = httpx.Timeout(30.0, connect=60.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for name, dep in self.config.dependencies.items():
                resolved_items = self.resolve_cdn_url(dep)

                for url, filename in resolved_items:
                    # 确定目标路径
                    # 如果是默认推导的 url (unpkg root)，我们需要先 HEAD 请求获取真实 URL 吗？
                    # 为了并发效率，直接 GET 并 follow redirects 是最简单的。

                    # 检查 Lock 文件中是否有此 URL
                    expected_hash = None
                    if name in lock_data:
                        files = lock_data[name].get("files", [])
                        for f in files:
                            if f.get("url") == url:
                                expected_hash = f.get("integrity")
                                # 如果在 lock 文件中找到，使用 lock 中的路径作为目标路径
                                # 这样可以确保幂等性检查时使用的是正确的文件名（处理过重定向后的）
                                lock_path = f.get("path")
                                if lock_path:
                                    # lock_path 是相对路径，转换为绝对路径
                                    filename = Path(lock_path).name
                                break

                    dest_dir = self.project_root / self.config.destination / name
                    dest_path = dest_dir / filename

                    # 创建下载任务
                    tasks.append(
                        self.download_task(client, name, url, dest_path, expected_hash)
                    )

            # 执行所有下载任务
            print(f"Downloading {len(tasks)} files...")
            results = []
            for f in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
                results.append(await f)

            # 构建新的 lock 数据
            for res in results:
                name, url, dest_rel, integrity = res
                if name not in new_lock_data:
                    new_lock_data[name] = {"files": []}
                new_lock_data[name]["files"].append(
                    {"url": url, "path": dest_rel.as_posix(), "integrity": integrity}
                )

        self.save_lockfile(new_lock_data)
        print("Sync completed. Lock file updated.")

    async def download_task(
        self,
        client: httpx.AsyncClient,
        name: str,
        url: str,
        dest_path: Path,
        expected_hash: str | None = None,
    ) -> tuple[str, str, Path, str]:
        """
        单个下载任务封装。

        :param client: HTTPX 客户端
        :param name: 包名
        :param url: 下载链接
        :param dest_path: 本地目标路径
        :param expected_hash: 期望的 SHA256 哈希值
        """
        # 特殊处理：如果 URL 是 unpkg 根目录 (如 https://unpkg.com/htmx)，
        # httpx follow_redirects 会带我们去真实路径。
        # 我们需要更新 dest_path 的文件名，如果是默认的 name.js 的话。

        try:
            # Idempotency Check
            if dest_path.exists() and expected_hash:
                # Check if we should verify integrity of existing file
                existing_hash = calculate_content_sha256(dest_path.read_bytes())
                existing_integrity = f"sha256-{existing_hash}"
                if existing_integrity == expected_hash:
                    # Log or print skipping?
                    # logger.info(f"Skipping {name} (already installed)")
                    rel_path = dest_path.relative_to(self.project_root)
                    return name, url, rel_path, expected_hash

            # Retry logic
            response = None
            last_error = None
            success = False
            for attempt in range(3):
                try:
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()
                    success = True
                    break
                except httpx.HTTPError as e:
                    last_error = e
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue

            if not success:
                raise last_error or VendorError(f"Failed to download {url}")

            # 如果是默认文件名，尝试从 URL 推断
            if dest_path.name == f"{name}.js":
                real_filename = Path(urlparse(str(response.url)).path).name
                dest_path = dest_path.with_name(real_filename)

            content = response.content
            integrity = calculate_content_sha256(content)
            integrity_str = f"sha256-{integrity}"

            if expected_hash and integrity_str != expected_hash:
                raise VendorError(
                    f"Integrity check failed for {name}. "
                    f"Expected {expected_hash}, got {integrity_str}"
                )

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(content)

            # 返回相对路径
            rel_path = dest_path.relative_to(self.project_root)
            # 使用原始 URL (requested URL) 而不是 response.url
            # 这样 lock 文件中存储的是 pyproject.toml 解析出的 URL
            # 下次 install 时才能正确匹配
            return name, url, rel_path, integrity_str

        except Exception as e:
            logger.error(f"Error downloading {name} from {url}: {e}")
            raise

    # Alias for backward compatibility or clarity if needed
    install = sync

    async def add(self, package_name: str, version: str | None = None) -> None:
        """
        添加新依赖。

        :param package_name: 包名
        :param version: 版本号
        """
        # 1. 简单检查包是否存在 (通过请求 unpkg)
        async with httpx.AsyncClient() as client:
            url = f"https://unpkg.com/{package_name}"
            if version:
                url += f"@{version}"

            try:
                resp = await client.head(url, follow_redirects=True)
                if resp.status_code != 200:
                    # Try GET if HEAD fails
                    resp = await client.get(url, follow_redirects=True)
                    if resp.status_code != 200:
                        raise VendorError(
                            f"Package '{package_name}' not found on unpkg."
                        )
            except httpx.HTTPError as e:
                raise VendorError(f"Network error checking package: {e}")

            # 获取真实版本号
            if not version:
                # e.g. https://unpkg.com/jquery@3.7.1/dist/jquery.js
                path = urlparse(str(resp.url)).path
                # match @version in path
                match = re.search(r"@([\d\.]+[-\w\.]*)", path)
                if match:
                    version = match.group(1)
                else:
                    logger.warning(
                        f"Could not auto-detect version for {package_name}, using '*'"
                    )
                    version = "*"

        # 2. 更新 pyproject.toml
        VendorConfig.add_dependency_to_toml(self.config_path, package_name, version)
        print(f"Added {package_name} ({version}) to pyproject.toml")

        # 3. 重新加载配置并安装
        self.config = VendorConfig.from_toml(self.config_path)
        await self.install()

    async def remove(self, package_name: str) -> None:
        """
        移除依赖。

        :param package_name: 包名
        """
        # 1. Remove from pyproject.toml
        VendorConfig.remove_dependency_from_toml(self.config_path, package_name)
        print(f"Removed {package_name} from pyproject.toml")

        # 2. Remove files
        # 使用当前配置确定路径
        dest_dir = self.project_root / self.config.destination / package_name
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
            print(f"Removed directory {dest_dir}")

        # 3. Update Lock file
        lock_data = self.load_lockfile()
        if package_name in lock_data:
            del lock_data[package_name]
            self.save_lockfile(lock_data)
            print("Updated lock file.")

        # Reload config
        self.config = VendorConfig.from_toml(self.config_path)

    async def update(self, package_name: str | None = None) -> None:
        """更新依赖"""
        # 简化逻辑：直接运行 install，因为 CDN URL 如果没有锁死版本，会自动获取最新
        # 如果需要升级版本号，需要解析 toml 并修改 version 字段
        # 这里暂时只实现重装
        print("Updating dependencies...")
        await self.install()
