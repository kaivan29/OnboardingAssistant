import os
import shutil
from pathlib import Path
from git import Repo

def migrate():
    # Old location (relative to backend root, where this script runs)
    # We assume we run from 'backend/'
    old_dir = Path("storage/codebases/rocksdb").resolve()

    # New location
    new_dir = Path(os.path.expanduser("~/xHack/rocksdb")).resolve()

    print(f"Checking locations:")
    print(f"  Old: {old_dir}")
    print(f"  New: {new_dir}")

    if new_dir.exists():
        print("✅ Repository already exists at new location.")
        # Check if it has content
        if not (new_dir / ".git").exists():
            print("⚠️ Directory exists but looks empty/invalid. Re-cloning...")
            shutil.rmtree(new_dir)
        else:
            return

    # Create parent dir
    new_dir.parent.mkdir(parents=True, exist_ok=True)

    if old_dir.exists() and (old_dir / ".git").exists():
        print(f"🚚 Moving repository from {old_dir} to {new_dir}...")
        try:
            shutil.move(str(old_dir), str(new_dir))
            print("✅ Migration successful.")
            return
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            print("Falling back to clone...")
    
    print(f"⬇️ Cloning RocksDB to {new_dir}...")
    try:
        Repo.clone_from("https://github.com/facebook/rocksdb", new_dir, depth=1)
        print("✅ Clone successful.")
    except Exception as e:
        print(f"❌ Clone failed: {e}")

if __name__ == "__main__":
    migrate()
