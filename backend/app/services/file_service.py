import os
import shutil
from typing import List, Dict, Any, Optional
from git import Repo
from pathlib import Path

class FileService:
    def __init__(self, storage_dir: str = "storage/codebases"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_repo_path(self, codebase_id: str) -> Path:
        return self.storage_dir / codebase_id

    def ensure_repo_exists(self, codebase_id: str, repo_url: str) -> bool:
        """Clones the repo if it doesn't exist."""
        repo_path = self._get_repo_path(codebase_id)
        
        if repo_path.exists():
            # In a real app, we might want to git pull here
            return True
            
        try:
            print(f"Cloning {repo_url} to {repo_path}...")
            Repo.clone_from(repo_url, repo_path, depth=1)
            return True
        except Exception as e:
            print(f"Failed to clone repo: {e}")
            return False

    def list_files(self, codebase_id: str, subdir: str = "") -> List[Dict[str, Any]]:
        """Lists files and directories in a specific subdirectory."""
        repo_path = self._get_repo_path(codebase_id)
        target_dir = repo_path / subdir
        
        # Security check to prevent directory traversal
        try:
            target_dir.relative_to(repo_path)
        except ValueError:
            raise ValueError("Invalid path")

        if not target_dir.exists() or not target_dir.is_dir():
            return []

        items = []
        try:
            # Sort: directories first, then files
            with os.scandir(target_dir) as entries:
                sorted_entries = sorted(entries, key=lambda e: (not e.is_dir(), e.name.lower()))
                
                for entry in sorted_entries:
                    if entry.name.startswith('.git'):
                        continue
                        
                    items.append({
                        "name": entry.name,
                        "path": str(Path(subdir) / entry.name).replace('\\', '/'),
                        "type": "dir" if entry.is_dir() else "file",
                        "size": entry.stat().st_size if entry.is_file() else 0
                    })
        except Exception as e:
            print(f"Error reading directory: {e}")
            return []
            
        return items

    def get_file_content(self, codebase_id: str, file_path: str) -> Optional[str]:
        """Reads the content of a file."""
        repo_path = self._get_repo_path(codebase_id)
        target_file = repo_path / file_path
        
        try:
            target_file.relative_to(repo_path)
        except ValueError:
            raise ValueError("Invalid path")

        if not target_file.exists() or not target_file.is_file():
            return None

        try:
            # Try UTF-8 first
            return target_file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1 for some mixed content, or generally binary
                # For code viewer, we might simply say "Binary file"
                return "<Binary file or non-UTF-8 content>"
            except Exception:
                return None

file_service = FileService()
