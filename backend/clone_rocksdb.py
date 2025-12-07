import sys
import os
sys.path.append(os.getcwd())

from app.services.file_service import file_service

def clone():
    print("🚀 Cloning RocksDB for file browsing...")
    # This might take a minute
    success = file_service.ensure_repo_exists(
        'rocksdb', 
        'https://github.com/facebook/rocksdb'
    )
    if success:
        print("✅ Cloned successfully to storage/codebases/rocksdb")
    else:
        print("❌ Failed to clone")

if __name__ == "__main__":
    clone()
