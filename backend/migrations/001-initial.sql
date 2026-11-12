-- Schema is created from versioned SQLAlchemy metadata during demo seed.
-- Production rollout: generate reviewed ALTER migrations before changing existing tables.
-- Natural keys: users.email, candidate_datasets.name, score_policies.name, audit_reports.run_id.
CREATE INDEX IF NOT EXISTS ix_audit_runs_status ON audit_runs(status);

-- 固定名额复核（2026-11）：score_policies 增加可空列 quota。
-- 应用启动时 src.main.upgrade_schema 对历史库幂等执行等价的
-- ALTER TABLE score_policies ADD COLUMN quota INTEGER；
-- 旧方案 quota 为 NULL，仍按 threshold 统一分数线口径复核，历史结果不变。
