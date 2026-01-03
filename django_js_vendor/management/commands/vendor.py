import asyncio

from django.core.management.base import BaseCommand, CommandError

from django_js_vendor.core import VendorError, VendorManager


class Command(BaseCommand):
    help = "Manage frontend dependencies (install, add, update)"

    def add_arguments(self, parser):
        """
        添加命令行参数。

        :param parser: 参数解析器
        """
        subparsers = parser.add_subparsers(dest="subcommand", required=True)

        # sync
        subparsers.add_parser(
            "sync", help="Sync dependencies from pyproject.toml and lock file"
        )

        # add
        add_parser = subparsers.add_parser("add", help="Add a new dependency")
        add_parser.add_argument("package_name", help="Name of the package (e.g. htmx)")
        add_parser.add_argument("version", nargs="?", help="Optional version specifier")

        # update
        update_parser = subparsers.add_parser("update", help="Update dependencies")
        update_parser.add_argument(
            "package_name", nargs="?", help="Optional package to update"
        )

        # remove
        remove_parser = subparsers.add_parser("remove", help="Remove a dependency")
        remove_parser.add_argument("package_name", help="Name of the package to remove")

    def handle(self, *args, **options):
        """
        命令入口点。

        :param args: 位置参数
        :param options: 关键字参数
        """
        # Wrapper to run async logic
        try:
            asyncio.run(self.handle_async(**options))
        except VendorError as e:
            raise CommandError(str(e))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Unexpected error: {e}"))
            raise

    async def handle_async(self, subcommand, **options):
        """
        异步处理逻辑。

        :param subcommand: 子命令
        :param options: 其他选项
        """
        manager = VendorManager()

        self.stdout.write(f"Running vendor {subcommand}...")

        if subcommand == "sync":
            await manager.sync()
            self.stdout.write(self.style.SUCCESS("Dependencies synced successfully."))

        elif subcommand == "add":
            package_name = options["package_name"]
            version = options.get("version")
            await manager.add(package_name, version)
            self.stdout.write(self.style.SUCCESS(f"Added {package_name}."))

        elif subcommand == "update":
            package_name = options.get("package_name")
            await manager.update(package_name)
            self.stdout.write(self.style.SUCCESS("Dependencies updated."))

        elif subcommand == "remove":
            package_name = options["package_name"]
            await manager.remove(package_name)
            self.stdout.write(self.style.SUCCESS(f"Removed {package_name}."))
