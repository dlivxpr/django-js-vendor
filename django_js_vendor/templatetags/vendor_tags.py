"""
Vendor template tags for Django.
"""
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from django_js_vendor.core import VendorManager

register = template.Library()


@register.simple_tag
def render_vendor_assets(*args: str) -> str:
    """
    Render HTML tags for vendor assets.

    :param args: Optional package names to include. If empty, include all.
    :return: HTML string containing <script> and <link> tags.
    """
    # Try to find project root from settings, fallback to CWD
    project_root = getattr(settings, "BASE_DIR", Path("."))

    manager = VendorManager(project_root=project_root)
    lock_data = manager.load_lockfile()

    if not lock_data:
        return ""

    # Get dependencies from config to maintain order
    deps_order = list(manager.config.dependencies.keys())

    # Filter dependencies if args provided
    if args:
        target_deps = [name for name in deps_order if name in args]
    else:
        target_deps = deps_order

    html_parts: list[str] = []

    for name in target_deps:
        if name not in lock_data:
            continue

        pkg_data = lock_data[name]
        files = pkg_data.get("files", [])

        for file_info in files:
            path_str = file_info.get("path")
            if not path_str:
                continue

            # Heuristic to convert file path to static path
            # Lock file paths are POSIX (forward slashes)
            # If path starts with "static/", strip it
            # This assumes default configuration where destination is "static/vendor"
            # and STATIC_URL maps to "static" directory content.
            if path_str.startswith("static/"):
                static_path = path_str[7:]
            else:
                static_path = path_str

            url = static(static_path)

            if static_path.endswith(".js"):
                html_parts.append(f'<script src="{url}" defer></script>')
            elif static_path.endswith(".css"):
                html_parts.append(f'<link rel="stylesheet" href="{url}">')

    return mark_safe("\n".join(html_parts))
