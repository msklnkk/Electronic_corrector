from fastapi import APIRouter, Depends, HTTPException, Query

from project.api.depends import database, document_repo, get_current_user
from project.core.rule_store import list_available_rulesets
from project.core.semantic_gost_pipeline import SemanticGostPipeline

router = APIRouter(prefix="/semantic-check")


@router.get("/rulesets")
async def get_available_rulesets(
    current_user=Depends(get_current_user),
):
    return {
        "rulesets": list_available_rulesets()
    }


@router.post("/{document_id}")
async def semantic_check_document(
    document_id: int,
    ruleset_code: str = Query(...),
    current_user=Depends(get_current_user),
):
    async with database.session() as session:
        document = await document_repo.get_document_by_id(session, document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")

        if not current_user.is_admin and document.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Нет доступа")

    try:
        pipeline = SemanticGostPipeline(ruleset_code=ruleset_code)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    result = await pipeline.run(file_path=document.filepath)

    return {
        "document_id": document_id,
        "filename": document.filename,
        "ruleset_code": ruleset_code,
        "document_kind": result.get("document_kind", "document"),
        "total_pages": result.get("total_pages"),
        "rules_count": result.get("rules_count"),
        "overall_score": result.get("overall_score"),
        "score_label": result.get("score_label"),
        "status": result.get("status"),
        "short_recommendation": result.get("short_recommendation"),
        "summary": result.get("summary", {}),
        "findings": result.get("findings", []),
    }