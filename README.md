# 知卷 · 智能组卷工作台

面向高中教师的智能组卷 MVP：以「双向细目表」为核心，按高考结构生成整卷，并给出可解释的试卷体检报告，支持导出可编辑的 Word 试卷。

> 当前版本：v0.1（数学单科 · 教师端 · 演示题库 65 题）

---

## 1. 为什么不是「题库 + 购物车」

组卷的本质是**教育测量学**，不是把题目拖进购物车：

- **结构先行**：一张高考卷的题型顺序、分值分布、各题型时长是相对固定的，这是「细目表」而不是「清单」。
- **难度守恒**：整卷难度由单题难度加权得到，选题时必须以「整卷难度曲线」为目标，逐题贪心会得到锯齿状分布。
- **考点配额**：主干知识（函数、导数、解析几何、概率统计）必须按分值占比覆盖，不能碰运气。
- **可解释**：老师需要知道「这套卷为什么难」「哪里覆盖不足」，而不是一个黑盒结果。

本项目把这四点做成了数据结构和算法，而不是留给老师手工平衡。

---

## 2. 快速开始

### 环境要求

- Python 3.10+（依赖已随 `backend/vendor` 分发，**无需 pip install**）
- 现代浏览器（Chrome / Edge / Safari 最新版）

### 启动

```powershell
cd zujuan
.\run.ps1          # 等价于 cd backend; python run.py
```

打开浏览器访问 <http://127.0.0.1:8123>。首次启动会自动建库并写入演示题库（`data/zujuan.db`）。

如果命令行没有 `python`，可直接用完整路径：

```powershell
C:\Users\<你>\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe backend\run.py
```

### 依赖是怎么来的

本机 `pip install` 在受限沙箱下会失败（`[Errno 13] Permission denied ... .whl.metadata`）。因此依赖通过「Node 下载 wheel → Python 解压」的方式放进 `backend/vendor`，运行时由 `app/main.py` 把该目录插入 `sys.path`。要新增依赖：

```powershell
cd scripts
node install_deps.mjs .. fastapi uvicorn
python extract_wheels.py
```

---

## 3. 目录结构

```
zujuan/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 应用装配（含静态站点挂载）
│   │   ├── db.py              # SQLite 连接、建表
│   │   ├── schema.sql         # 表结构
│   │   ├── seed.py            # 知识点树 + 演示题库 + 细目表模板
│   │   ├── repository.py      # 数据访问层（所有 SQL 集中于此）
│   │   ├── schemas.py         # 请求/响应模型
│   │   ├── api/               # 路由：meta / knowledge / questions / blueprints / papers
│   │   └── services/
│   │       ├── assemble.py    # 组卷引擎（槽位展开 + 贪心 + 局部搜索）
│   │       ├── report.py      # 试卷体检报告与得分预测
│   │       └── export.py      # Word(.docx) 导出
│   ├── vendor/                # 预装 Python 依赖
│   └── run.py                 # 启动入口（默认 127.0.0.1:8123）
├── web/                       # 前端（原生 ES Module，无构建）
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── data/zujuan.db             # SQLite 数据库（运行时生成）
└── scripts/                   # 依赖安装与冒烟测试工具
```

---

## 4. 核心概念

### 4.1 知识点

两级树：`M1`（集合与常用逻辑用语）→ `M1.1`（集合的运算）。题目挂叶子节点，细目表配额可挂任一层级。

### 4.2 双向细目表

```json
{
  "name": "新高考 I 卷 · 数学",
  "total_score": 150,
  "duration_min": 120,
  "sections": [
    {"key": "single", "label": "一、单项选择题", "qtype": "single", "count": 8, "score": 5},
    {"key": "multi",  "label": "二、多项选择题", "qtype": "multi",  "count": 3, "score": 6},
    {"key": "blank",  "label": "三、填空题",     "qtype": "blank",  "count": 3, "score": 5},
    {"key": "solve",  "label": "四、解答题",     "qtype": "solve",  "count": 5, "score": "auto"}
  ],
  "cells": [
    {"knowledge_code": "M3.2", "score": 15, "weight": 15},
    {"knowledge_code": "M7.2", "score": 17, "weight": 17}
  ]
}
```

`cells` 是考点配额：目标分值按 `weight` 归一到总分。

### 4.3 难度口径

题目难度 = **预期得分率**（0.1 极难 ～ 0.9 极易），与教育测量学一致。整卷难度按分值加权。

若上游题库使用「难度系数 1=最难」，导入时需换算为得分率。

---

## 5. 组卷引擎（services/assemble.py）

1. **槽位展开**：把 `sections` 展开成 N 个槽位，按题序给出目标难度，形成从易到难的**难度斜坡**（RAMP = 0.16）。
2. **贪心填充**：每个槽位在候选池中按 `0.44×难度贴合 + 0.34×考点紧缺度 + 0.10×低使用率 - 重复惩罚 - 答案分布惩罚` 选优。
3. **局部搜索**：随机交换 + 爬山 1500 轮，目标函数 `1.6×难度贴合 + 1.0×考点覆盖 + 0.25×答案均衡 - 重复惩罚`。
4. **多次重启**：默认 6 次不同随机种子，取最优解。

> 生产环境建议换成 OR-Tools CP-SAT 做整数规划（约束：题型数量、考点分值下界、难度区间、答案均衡、题目不重复），20 题规模可毫秒级求解。

---

## 6. 试卷体检报告（services/report.py）

| 指标 | 含义 |
| --- | --- |
| health（0-100） | 难度 30 + 覆盖 30 + 结构 20 + 答案均衡 10 + 用时 10 |
| difficulty / target | 加权难度 vs 目标难度 |
| coverage | 每个考点的目标分值与实际分值，比值 < 1 即配额未满 |
| curve | 逐题难度与目标难度，看整卷是否呈平滑上升 |
| prediction | 1PL 模型 `b = ln((1-d)/d)`，估计各能力水平考生的期望得分与及格概率 |
| difficulty_ceiling | 当前题库能支撑的最高整卷难度；目标高于它时直接给出提示，而不是假装能组出来 |
| warnings | 中文提示（难度不可达、覆盖不足、用时失衡、考点扎堆） |

这部分是**老师最愿意付费**的地方：它把「凭感觉」变成「有据可查」。

---

## 7. API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/meta | 学科、题型、认知层次、难度分档 |
| GET | /api/knowledge | 知识点树（含题目数） |
| GET | /api/questions | 题目检索（qtype/knowledge/difficulty_min/difficulty_max/keyword/page/size） |
| GET | /api/questions/{id} | 题目详情 |
| GET | /api/blueprints | 细目表列表 |
| GET | /api/blueprints/{id} | 细目表详情 |
| POST | /api/papers/assemble | 组卷：{blueprint_id, title?, target_difficulty?, restarts?} |
| GET | /api/papers | 试卷列表 |
| GET | /api/papers/{id} | 试卷详情 + 体检报告 |
| DELETE | /api/papers/{id} | 删除试卷 |
| POST | /api/papers/{id}/items/{item_id}/swap | 换题：{question_id} |
| GET | /api/papers/{id}/alternatives?item_id= | 同槽位候选题（按难度接近度排序） |
| GET | /api/papers/{id}/export.docx | 导出 Word |
| GET | /api/stats | 题库 / 试卷统计 |

交互式文档：<http://127.0.0.1:8123/docs>

---

## 8. 已知限制（MVP 边界）

- **题库仅 65 道演示题**，覆盖 33 个考点；题量不足时部分细目表会出现覆盖缺额（体检报告会提示）。
- 仅数学单科；多选题、解答题的「步骤分」尚未建模。
- 难度为人工标注，未做 IRT 校准；prediction 是 1PL 近似，非真实考生数据拟合。
- 无用户体系与权限控制（单机单进程 SQLite）。
- Word 导出为可直接编辑的初稿，公式为纯文本（x^2、sqrt(3) 形式），未用 OMML 排版。

## 9. 下一步路线

1. **题库工程**：接入真题（按年份/地区分科），去重、公式结构化（LaTeX/OMML）、知识点自动打标。
2. **难度校准**：用真实作答数据估计 IRT 参数（2PL/3PL），替换人工标注。
3. **组卷升级**：OR-Tools CP-SAT 精确求解，支持「指定必考」「排除某题」「同题不重复」等硬约束。
4. **教师工作流**：班级管理、成绩录入、逐题得分率回流、试卷复用与变式改编。
5. **学生端**：错题本、自适应练习、个性化组卷。
6. **排版**：LaTeX/MathML 渲染、OMML 导出、答题卡与双向细目表附表。

---

## 10. 开发自检

服务启动后（默认 8123 端口），可跑三个脚本验证：

```powershell
node scripts\smoke.mjs      # API 冒烟：组卷、换题、导出、静态页
node scripts\ui_check.mjs   # 无头 DOM：渲染答卷、换题弹窗、题库分页
node scripts\ui_check2.mjs  # 完整流程：填表 → 生成 → 打开试卷库
```

`ui_check*` 依赖 `scripts/node_modules/jsdom`（用 `--cache .npm-cache` 装在本地）。
