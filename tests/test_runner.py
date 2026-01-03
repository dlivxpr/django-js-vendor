import asyncio
import logging
from pathlib import Path

from django_js_vendor.core import VendorManager

# Configure logging
logging.basicConfig(level=logging.INFO)


async def main():
    print("=" * 50)
    print("DJANGO JS VENDOR TEST RUNNER")
    print("=" * 50)

    manager = VendorManager()

    # 1. Show Config
    print("\n[1] Configuration (from pyproject.toml):")
    for name, dep in manager.config.dependencies.items():
        print(f"  - {name}: {dep}")

    # 2. Run Sync
    print("\n[2] Running sync()...")
    try:
        await manager.sync()
        print("  -> Sync successful.")
    except Exception as e:
        print(f"  -> Sync failed: {e}")
        return

    # 3. Verify Files
    print("\n[3] Verifying installed files in 'static/vendor':")
    vendor_dir = Path("static/vendor")
    if vendor_dir.exists():
        for path in vendor_dir.rglob("*"):
            if path.is_file():
                print(f"  - {path}")
    else:
        print("  -> static/vendor directory not found!")

    # 4. Show Lock File
    print("\n[4] Content of js-vendor.lock:")
    lock_file = Path("js-vendor.lock")
    if lock_file.exists():
        with open(lock_file, "r") as f:
            print(f.read())
    else:
        print("  -> Lock file not found.")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
