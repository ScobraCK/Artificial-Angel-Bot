from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base

class GachaPickupORM(Base):
    __tablename__ = 'gacha'

    id: Mapped[int] = mapped_column(primary_key=True)
    start: Mapped[int] = mapped_column(BigInteger) # unix timestamp
    end: Mapped[int] = mapped_column(BigInteger)  # unix timestamp
    select_list_type: Mapped[int]
    char_id: Mapped[int]
