from pydantic import (
    BaseModel, Field, AliasPath,
    FieldSerializationInfo, field_serializer,
    ValidationInfo, field_validator, model_validator,
)
from typing import List, Optional, Literal, Union, Any

from api.crud.string_keys import read_string_key_language
from api.utils.error import APIError
from api.utils.masterdata import MasterData
from api.schemas.equipment import search_uw_info
from api.schemas.items import ItemCount
import api.schemas.validators as validators
import api.schemas.serializers as serializers
import api.utils.enums as enums

class _Character(BaseModel):
    char_id: int = Field(..., validation_alias='Id')
    name: str = Field(..., validation_alias='NameKey')
    title: Optional[str] = Field(..., validation_alias='Name2Key')
    element: enums.Element = Field(..., validation_alias='ElementType')
    rarity: enums.CharacterRarity = Field(..., validation_alias='RarityFlags')
    job: enums.Job = Field(..., validation_alias='JobFlags')
    speed: int = Field(..., validation_alias=AliasPath('InitialBattleParameter', 'Speed'))
    uw: Optional[str] = Field(...)
    attack_type: enums.NormalSkill = Field(..., validation_alias='NormalSkillId')
    actives: List[int] = Field(..., validation_alias='ActiveSkillIds')
    passives: List[int] = Field(..., validation_alias='PassiveSkillIds')

    _serialize_str = field_serializer('name', 'title', 'uw')(serializers.serialize_str)
    _serialize_enum = field_serializer('element', 'rarity', 'job', 'attack_type')(serializers.serialize_enum)

class _Profile(BaseModel):
    char_id: int = Field(..., validation_alias='Id')
    birthday: int = Field(..., validation_alias='Birthday')
    height: int = Field(..., validation_alias='Height')
    weight: int = Field(..., validation_alias='Weight')
    blood_type: enums.BloodType = Field(..., validation_alias='BloodType')
    gacha_message: Optional[str] = Field(..., validation_alias='GachaResultMessage2Key')
    voiceJP: str = Field(..., validation_alias='CharacterVoiceJPKey')
    voiceUS: Optional[str] = Field(..., validation_alias='CharacterVoiceUSKey')
    vocalJP: str = Field(..., validation_alias='VocalJPKey')
    vocalUS: Optional[str] = Field(..., validation_alias='VocalUSKey')

    @model_validator(mode='after')
    def fill_US_va(self)->Any:
        if self.voiceUS is None:
            self.voiceUS = f'[CharacterProfileVoiceUS{self.char_id}]'
        
        if self.vocalUS is None:
            self.vocalUS = f'[CharacterProfileVocalUS{self.char_id}]'

        return self

    _serialize_str = field_serializer('gacha_message', 'voiceJP', 'voiceUS', 'vocalJP', 'vocalUS')(serializers.serialize_str)

class Character(BaseModel):
    char_id: int = Field(..., )
    name: str = Field(..., )
    title: Optional[str] = Field(..., )
    element: str = Field(..., )
    rarity: str = Field(..., )
    job: str = Field(..., )
    speed: int = Field(..., )
    uw: Optional[str] = Field(..., )
    attack_type: str = Field(..., )
    actives: List[int] = Field(..., )
    passives: List[int] = Field(..., )

class Profile(BaseModel):
    char_id: int = Field(..., )
    birthday: int = Field(..., )
    height: int = Field(..., )
    weight: int = Field(..., )
    blood_type: str = Field(..., )
    gacha_message: Optional[str] = Field(..., )
    voiceJP: str = Field(...)
    voiceUS: Optional[str] = Field(...)
    vocalJP: str = Field(...)
    vocalUS: Optional[str] = Field(...)

class Lament(BaseModel):
    char_id: int = Field(validation_alias='Id')
    nameJP: str = Field(..., validation_alias='LamentJPKey')
    nameUS: str = Field(..., validation_alias='LamentUSKey')
    youtubeJP: str = Field(..., validation_alias=AliasPath('MovieJpUrl', 'jaJP'))
    youtubeUS: str = Field(..., validation_alias=AliasPath('MovieUsUrl', 'enUS'))
    lyricsJP: str = Field(..., validation_alias='LyricsJPKey')
    lyricsJP_translated: Optional[str] = Field(..., validation_alias='LyricsJPKey')
    lyricsUS: str = Field(..., validation_alias='LyricsUSKey')

    _serialize_str = field_serializer('nameJP', 'nameUS', 'lyricsUS')(serializers.serialize_str)
    
    @field_serializer('lyricsJP')
    def get_jp_lyrics(self, v: str, info: FieldSerializationInfo):
        context = info.context
        if isinstance(context, dict):
            session = context.get('db')
            if session is None:
                raise ValueError('DB session could not be found')
            return read_string_key_language(session, v, enums.Language.jajp)
        return v

    @field_serializer('lyricsJP_translated')
    def get_jp_tl_lyrics(self, v: str, info: FieldSerializationInfo):
        context = info.context
        if isinstance(context, dict):
            session = context.get('db')
            lang = context.get('language')
            if session is None:
                raise ValueError('DB session could not be found')
            if lang == enums.Language.jajp:
                return None
            return read_string_key_language(session, v, lang)
        return v
    
    class Config:
        populate_by_name = True

class _Voiceline(BaseModel):
    category: enums.VoiceCategory = Field(..., validation_alias='CharacterVoiceCategory')
    unlock: enums.VoiceUnlock = Field(..., validation_alias='UnlockCondition')
    unlock_quest: int = Field(..., validation_alias='UnlockQuestId')
    sort_order: int = Field(..., validation_alias='SortOrder')
    subtitle: Optional[str] = Field(..., validation_alias='SubtitleKey')
    button_text: str = Field(..., validation_alias='UnlockedVoiceButtonTextKey')

    _serialize_str = field_serializer('subtitle', 'button_text')(serializers.serialize_str)
    _serialize_enum = field_serializer('category', 'unlock')(serializers.serialize_enum)

class Voiceline(BaseModel):
    category: str = Field(...,)
    unlock: Optional[str] = Field(...,)
    unlock_quest: int = Field(...,)
    sort_order: int = Field(...,)
    subtitle: Optional[str] = Field(...,)
    button_text: str = Field(...,)

class _CharacterVoicelines(BaseModel):
    char_id: int = Field(...,)
    voicelines: List[_Voiceline]

class CharacterVoicelines(BaseModel):
    char_id: int = Field(...,)
    voicelines: List[Voiceline] = Field(...,)

class _Memory(BaseModel):
    episode_id: int = Field(..., validation_alias='EpisodeId') 
    level: int = Field(..., validation_alias='Level')
    rarity: enums.CharacterRarity = Field(..., validation_alias='RarityFlags')
    reward: List[ItemCount] = Field(..., validation_alias='RewardItemList')
    title: str = Field(..., validation_alias='TitleKey')
    text: str = Field(..., validation_alias='TextKey')
    
    _serialize_str = field_serializer('title', 'text')(serializers.serialize_str)
    _serialize_enum = field_serializer('rarity')(serializers.serialize_enum)

class Memory(BaseModel):
    episode_id: int
    level: int
    rarity: str
    reward: List[ItemCount]
    title: str
    text: str

class _CharacterMemories(BaseModel):
    char_id: int
    memories: List[_Memory]

class CharacterMemories(BaseModel):
    char_id: int
    memories: List[Memory]
    

async def get_character(md: MasterData, id: int) -> _Character:
    char_data = await md.search_id(id, 'CharacterMB')
    uw_data = await search_uw_info(md, id)
    uw = uw_data.get('NameKey') if uw_data else None
    if char_data is None:
        raise APIError(f'Could not find character info with id {id}')
    return _Character(**char_data, uw=uw)

async def get_profile(md: MasterData, id: int) -> _Profile:
    profile_data = await md.search_id(id, 'CharacterProfileMB')
    if profile_data is None:
        raise APIError(f'Could not find character profile with id {id}')
    return _Profile(**profile_data)

async def get_lament(md: MasterData, id: int):
    profile_data = await md.search_id(id, 'CharacterProfileMB')
    if profile_data is None:
        raise APIError(f'Could not find lament info with id {id}')
    return Lament(**profile_data)

async def get_voicelines(md: MasterData, id: int):
    voicelines = list(await md.search_filter('CharacterDetailVoiceMB', CharacterId=id))
    if not voicelines:
        raise APIError(f'Could not find voiceline info with id {id}')
    return _CharacterVoicelines(char_id=id, voicelines=voicelines)

async def get_memories(md: MasterData, id: int):
    memories = list(await md.search_filter('CharacterStoryMB', CharacterId=id))
    if not memories:
        raise APIError(f'Could not find memory info with id {id}')
    return _CharacterMemories(char_id=id, memories=memories)
