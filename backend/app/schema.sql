-- 知卷 · 数据库结构（SQLite）
PRAGMA foreign_keys = ON;

-- 知识点树
CREATE TABLE IF NOT EXISTS knowledge_points (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  code        TEXT UNIQUE NOT NULL,
  name        TEXT NOT NULL,
  parent_code TEXT REFERENCES knowledge_points(code),
  level       INTEGER NOT NULL,
  sort        INTEGER NOT NULL DEFAULT 0,
  subject     TEXT NOT NULL DEFAULT 'math'
);

-- 题目
CREATE TABLE IF NOT EXISTS questions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  qtype       TEXT NOT NULL,              -- single | multi | blank | solve
  stem        TEXT NOT NULL,
  options     TEXT,                       -- JSON: ["A. ..","B. .."]
  answer      TEXT NOT NULL,
  analysis    TEXT,
  score       REAL NOT NULL DEFAULT 5,
  difficulty  REAL NOT NULL,              -- 难度系数 0~1（得分率，越大越容易）
  cognitive   TEXT NOT NULL,              -- understand | apply | analyze
  knowledge_code TEXT NOT NULL,
  source      TEXT,
  year        INTEGER,
  region      TEXT,
  time_min    REAL,
  tags        TEXT,                       -- JSON
  usage_count INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_q_kp   ON questions(knowledge_code);
CREATE INDEX IF NOT EXISTS idx_q_type ON questions(qtype);

-- 细目表模板
CREATE TABLE IF NOT EXISTS blueprints (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  name          TEXT NOT NULL,
  subject       TEXT NOT NULL DEFAULT 'math',
  paper_type    TEXT,
  total_score   REAL NOT NULL,
  duration_min  INTEGER NOT NULL,
  target_difficulty REAL NOT NULL,
  sections      TEXT NOT NULL,            -- JSON
  cells         TEXT NOT NULL,            -- JSON
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 试卷
CREATE TABLE IF NOT EXISTS papers (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  title         TEXT NOT NULL,
  subject       TEXT NOT NULL DEFAULT 'math',
  blueprint_id  INTEGER REFERENCES blueprints(id),
  total_score   REAL NOT NULL,
  duration_min  INTEGER NOT NULL,
  target_difficulty REAL NOT NULL,
  difficulty    REAL,
  status        TEXT NOT NULL DEFAULT 'draft',
  constraints   TEXT,                     -- JSON: 生成参数
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 试卷题目
CREATE TABLE IF NOT EXISTS paper_items (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  paper_id    INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  question_id INTEGER NOT NULL REFERENCES questions(id),
  section     TEXT NOT NULL,
  position    INTEGER NOT NULL,
  score       REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pi_paper ON paper_items(paper_id);
