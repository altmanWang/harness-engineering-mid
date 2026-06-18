import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

WORKTREES_DIR = Path(os.getcwd()) / "data" / "worktrees"


def ensure_worktree(session_id: str | None) -> Path:
    """Ensure a worktree directory exists for the given session.

    Creates {WORKTREES_DIR}/{session_id}/.opencode/skills/ if not present.

    Returns:
        Path to the worktree directory, or os.getcwd() as fallback.
    """
    if not session_id:
        return Path(os.getcwd())

    worktree_path = WORKTREES_DIR / session_id
    skills_path = worktree_path / ".opencode" / "skills"

    if skills_path.exists():
        return worktree_path

    try:
        skills_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created worktree: {worktree_path}")
        return worktree_path
    except OSError as exc:
        logger.warning(
            f"Failed to create worktree {worktree_path}: {exc}. "
            f"Falling back to cwd."
        )
        return Path(os.getcwd())
