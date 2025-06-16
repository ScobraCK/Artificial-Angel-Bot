from fastapi import APIRouter, HTTPException, Request, Depends

from api.schemas.skills import get_skill_id
from common.schemas import APIResponse
from api.utils.deps import SessionDep, language_parameter
from api.utils.masterdata import MasterData
from api.utils.transformer import Transformer
from common import schemas
from common.enums import Language

from api.utils.logger import get_logger
logger = get_logger(__name__)

router = APIRouter()

@router.get(
    '/skill/{skill_id}',
    summary='Skill',
    description='Returns skill data',
    response_model=APIResponse[schemas.ActiveSkill|schemas.PassiveSkill]
)
async def skill_req(
    session: SessionDep,
    request: Request,
    skill_id: int,
    language: Language = Depends(language_parameter)
    ):
    md: MasterData = request.app.state.md
    tf = Transformer(session, language)
    skill = await tf.transform(await get_skill_id(md, skill_id))
    return APIResponse[schemas.ActiveSkill|schemas.PassiveSkill].create(request, skill)