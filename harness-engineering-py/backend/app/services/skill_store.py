import json
import os
import aiofiles
from pathlib import Path
from typing import List, Optional

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
