from fastapi import APIRouter, HTTPException, Request, Depends

from api.crud.string_keys import translate_keys
from api.schemas.skills import get_skill_id
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData
from common import schemas
from common.enums import Language

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/skill/{skill_id}',
    summary='Skill',
    description='Returns skill data',
    response_model=schemas.APIResponse[schemas.ActiveSkill|schemas.PassiveSkill]
)
async def skill(
    session: SessionDep,
    request: Request,
    skill_id: int,
    language: Language = Depends(language_parameter)
    ):
    md: MasterData = request.app.state.md
    skill = await get_skill_id(md, skill_id)
    await translate_keys(skill, session, language)
    return schemas.APIResponse[schemas.ActiveSkill|schemas.PassiveSkill].create(request, skill)