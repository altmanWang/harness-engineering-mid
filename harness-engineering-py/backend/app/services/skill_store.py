import json
import os
import zipfile
import aiofiles
from pathlib import Path
from typing import List, Optional

from app.services.worktree_manager import WORKTREES_DIR

SKILLS_DIR = Path(os.getcwd()) / "data" / "skills"
METADATA_FILE = SKILLS_DIR / "metadata.json"


async def _ensure_dir() -> None:
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)


async def _read_metadata() -> List[dict]:
    await _ensure_dir()
    if not METADATA_FILE.exists():
        return []
    try:
        async with aiofiles.open(METADATA_FILE, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content) if content.strip() else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


async def _write_metadata(skills: List[dict]) -> None:
    await _ensure_dir()
    async with aiofiles.open(METADATA_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(skills, ensure_ascii=False, indent=2))


async def list_skills() -> List[dict]:
    return await _read_metadata()


async def save_skill(skill: dict, file_content: bytes) -> dict:
    skills = await _read_metadata()
    skills.append(skill)
    await _write_metadata(skills)

    zip_path = SKILLS_DIR / f"{skill['id']}.zip"
    async with aiofiles.open(zip_path, "wb") as f:
        await f.write(file_content)

    return skill


async def delete_skill(skill_id: str) -> bool:
    skills = await _read_metadata()
    filtered = [s for s in skills if s["id"] != skill_id]
    if len(filtered) == len(skills):
        return False
    await _write_metadata(filtered)

    zip_path = SKILLS_DIR / f"{skill_id}.zip"
    try:
        zip_path.unlink()
    except FileNotFoundError:
        pass
    return True


def get_skill_zip_path(skill_id: str) -> Optional[Path]:
    zip_path = SKILLS_DIR / f"{skill_id}.zip"
    return zip_path if zip_path.exists() else None


async def get_skill_metadata(skill_id: str) -> Optional[dict]:
    skills = await _read_metadata()
    for s in skills:
        if s["id"] == skill_id:
            return s
    return None


async def load_skill_to_worktree(skill_id: str, session_id: str) -> dict:
    """Extract a skill's ZIP into the session's worktree .opencode/skills/{skill_id}/.

    Idempotent: if .loaded marker exists, skip extraction.

    Returns:
        {"loaded": True, "alreadyLoaded": bool, "skillId": str, "path": str}
    """
    zip_path = get_skill_zip_path(skill_id)
    if zip_path is None:
        raise FileNotFoundError(f"Skill ZIP not found: {skill_id}")

    target_dir = WORKTREES_DIR / session_id / ".opencode" / "skills" / skill_id
    loaded_marker = target_dir / ".loaded"

    if loaded_marker.exists():
        return {
            "loaded": True,
            "alreadyLoaded": True,
            "skillId": skill_id,
            "path": str(target_dir),
        }

    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target_dir)

    loaded_marker.touch()

    return {
        "loaded": True,
        "alreadyLoaded": False,
        "skillId": skill_id,
        "path": str(target_dir),
    }
