from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List

from api.schemas.skills import get_skills_char, get_skill_id, ActiveSkill, PassiveSkill
from api.schemas.api_models import APIResponse
from api.utils.enums import Language
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/skill/{skill_id}',
    summary='Skill',
    description='Returns skill data',
    response_model=APIResponse[ActiveSkill|PassiveSkill]
)
async def skill_req(
    session: SessionDep,
    request: Request,
    skill_id: int,
    language: Language = Depends(language_parameter)
    ):
    md: MasterData = request.app.state.md
    skill = get_skill_id(md, skill_id)
    return APIResponse[ActiveSkill|PassiveSkill].create(request, skill.model_dump(context={'db': session, 'language': language}))