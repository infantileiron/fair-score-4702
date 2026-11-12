from contextlib import asynccontextmanager
import logging
import redis
from fastapi import FastAPI
from sqlalchemy import text,inspect
from src.config.database import engine
from src.config.settings import REDIS_URL,SEED_DEMO
from src.middlewares.errors import ErrorMiddleware
from src.middlewares.audit import AuditMiddleware
from src.routes import auth,datasets,policies,runs,reviews,reports,audit
def upgrade_schema():
 # 轻量在线升级：为历史库补齐固定名额复核所需列，旧数据 quota 为 NULL，
 # 原有分数线方案与结果不受影响，仍可按原分数线复核。
 inspector=inspect(engine)
 existing={c["name"] for c in inspector.get_columns("score_policies")}
 with engine.begin() as db:
  if "quota" not in existing:
   db.execute(text("ALTER TABLE score_policies ADD COLUMN quota INTEGER"))
@asynccontextmanager
async def lifespan(app):
 upgrade_schema()
 if SEED_DEMO:
  try:
   from scripts.seed_demo import seed
   seed()
  except Exception: logging.exception("demo seed failed")
 yield
app=FastAPI(title="衡尺 · 筛选公平复核",lifespan=lifespan)
app.add_middleware(AuditMiddleware)
app.add_middleware(ErrorMiddleware)
for module in (auth,datasets,policies,runs,reviews,reports,audit): app.include_router(module.router)
@app.get("/health")
def health():
 with engine.connect() as db: db.execute(text("SELECT 1"))
 redis.Redis.from_url(REDIS_URL).ping()
 return {"status":"ok"}
