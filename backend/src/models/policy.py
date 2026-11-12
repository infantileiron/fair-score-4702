from sqlalchemy import String,Float,Integer,JSON,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class ScorePolicy(Base):
 __tablename__="score_policies"
 id:Mapped[str]=mapped_column(String,primary_key=True)
 name:Mapped[str]=mapped_column(String,unique=True)
 threshold:Mapped[float]=mapped_column(Float)
 dataset_id:Mapped[str]=mapped_column(ForeignKey("candidate_datasets.id"))
 max_gap:Mapped[float]=mapped_column(Float)
 # 固定名额（可空）：非空时按分数从高到低录满名额，threshold 仅作分数线兼容留档
 quota:Mapped[int]=mapped_column(Integer,nullable=True)
 created_at:Mapped[str]=mapped_column(String)
