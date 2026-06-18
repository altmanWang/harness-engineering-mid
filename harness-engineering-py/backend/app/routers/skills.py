import random
import string
import time
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from app.services import skill_store

router = APIRouter()

ALLOWED_TAGS = {"代码开发", "DSL", "悍马平台", "数据"}


def _gen_id() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"skill-{int(time.time() * 1000)}-{suffix}"


@router.get("/skills")
async def get_skills():
    skills = await skill_store.list_skills()
    return {"skills": skills}


@router.post("/skills")
async def create_skill(
    name: str = Form(...),
    description: str = Form(...),
    tags: str = Form(...),
    file: UploadFile = File(...),
):
    if not name.strip():
        raise HTTPException(status_code=400, detail="名称不能为空")
    if not description.strip():
        raise HTTPException(status_code=400, detail="描述不能为空")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    if not tag_list:
        raise HTTPException(status_code=400, detail="至少选择一个标签")
    for t in tag_list:
        if t not in ALLOWED_TAGS:
            raise HTTPException(status_code=400, detail=f"无效标签: {t}")

    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="只支持 .zip 文件")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件不能为空")

    from datetime import datetime, timezone

    skill = {
        "id": _gen_id(),
        "name": name.strip(),
        "description": description.strip(),
        "tags": tag_list,
        "fileName": file.filename,
        "fileSize": len(content),
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    await skill_store.save_skill(skill, content)
    return {"skill": skill}


@router.get("/skills/{skill_id}/download")
async def download_skill(skill_id: str):
    zip_path = skill_store.get_skill_zip_path(skill_id)
    if zip_path is None:
        raise HTTPException(status_code=404, detail="Skill 文件不存在")

    skills = await skill_store.list_skills()
    skill = next((s for s in skills if s["id"] == skill_id), None)
    filename = skill["fileName"] if skill else f"{skill_id}.zip"

    return FileResponse(
        path=str(zip_path),
        filename=filename,
        media_type="application/zip",
    )


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str):
    deleted = await skill_store.delete_skill(skill_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    return {"deleted": True}
