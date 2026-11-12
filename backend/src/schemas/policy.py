from pydantic import BaseModel,Field,model_validator
class PolicyInput(BaseModel):
 name:str=Field(min_length=2,max_length=100)
 dataset_id:str
 threshold:float=Field(default=0,ge=0,le=100,allow_inf_nan=False)
 max_gap:float=Field(default=0.1,ge=0,le=1,allow_inf_nan=False)
 quota:int|None=Field(default=None,ge=1)
 @model_validator(mode="after")
 def mode(self):
  # 固定名额模式下 threshold 不作为录取口径，仅为历史分数线复核留档
  if self.quota is None and not (0<=self.threshold<=100):
   raise ValueError("分数线模式须提供0至100的阈值")
  return self
