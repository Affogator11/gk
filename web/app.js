const $ = (sel, root) => (root || document).querySelector(sel);
const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

const state = {
  meta: null,
  blueprints: [],
  knowledge: [],
  stats: { questions: 0, blueprints: 0, papers: 0 },
  bpId: null,
  paper: null,
  report: null,
  bank: { qtype: "", knowledge: "", band: "", keyword: "", page: 1, size: 20, total: 0 },
  modalBusy: false,
};

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

async function api(path, opts) {
  const res = await fetch("/api" + path, Object.assign({
    headers: { "Content-Type": "application/json" },
  }, opts));
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (e) { data = text; }
  if (!res.ok) {
    const d = data && data.detail;
    throw new Error(typeof d === "string" ? d : (d ? JSON.stringify(d) : "请求失败 (" + res.status + ")"));
  }
  return data;
}

let toastTimer;
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 2600);
}

function bandOf(d) { return d >= 0.7 ? "easy" : (d >= 0.4 ? "mid" : "hard"); }
function bandLabel(d) { return d >= 0.7 ? "易" : (d >= 0.4 ? "中" : "难"); }

/* ---------------------------------------------------------------- 工作台 */
function bpCard(b) {
  const chips = b.sections.map((s) =>
    '<span class="chip">' + esc(s.label.replace(/^[一二三四五六七八九十]+、/, "")) +
    " " + s.count + " 题</span>"
  ).join("");
  const nCell = b.cells.length;
  return '<div class="bp-card' + (b.id === state.bpId ? " on" : "") + '" data-bp="' + b.id + '">' +
    '<span class="tick"></span>' +
    "<h3>" + esc(b.name) + "</h3>" +
    '<div class="sub">' + b.total_score + " 分 · " + b.duration_min + " 分钟 · 覆盖 " + nCell + " 个考点</div>" +
    '<div class="chips">' + chips +
    '<span class="chip acc">基准难度 ' + Number(b.target_difficulty).toFixed(2) + "</span></div></div>";
}

function renderWorkbench() {
  const v = $("#view");
  const bp = state.blueprints.find((b) => b.id === state.bpId);
  v.innerHTML =
    '<div class="page-head"><div><h1>组卷工作台</h1>' +
    "<p>选一套双向细目表，设定难度目标，生成符合高考结构的整卷</p></div>" +
    '<div><button class="btn ghost" id="btnReset">重新组卷</button></div></div>' +

    '<section class="panel"><div class="panel-head"><span class="step">1</span><h2>选择细目表</h2>' +
    '<span class="hint">决定题量、分值与考点配额</span></div>' +
    '<div class="bp-grid" id="bpGrid">' + state.blueprints.map(bpCard).join("") + "</div></section>" +

    '<section class="panel"><div class="panel-head"><span class="step">2</span><h2>设定目标</h2>' +
    '<span class="hint">难度即整卷预期得分率，0.55 接近高考常规难度</span></div>' +
    '<div class="form-row">' +
    '<div class="field"><label>试卷标题</label><input type="text" id="paperTitle" placeholder="留空则自动命名"></div>' +
    '<div class="field"><label>目标难度</label><div class="slider-wrap">' +
    '<input type="range" id="diffRange" min="30" max="80" value="55">' +
    '<span class="range-val" id="diffVal">0.55</span></div></div>' +
    '<button class="btn primary" id="btnAssemble">生成试卷</button></div></section>' +

    '<div id="result"></div>';

  if (bp) {
    const r = $("#diffRange");
    r.value = Math.round(Number(bp.target_difficulty) * 100);
    syncRange();
  }
  $("#btnReset").addEventListener("click", () => { state.paper = null; state.report = null; renderWorkbench(); });
  $("#diffRange").addEventListener("input", syncRange);
  $("#bpGrid").addEventListener("click", (e) => {
    const card = e.target.closest("[data-bp]");
    if (!card) return;
    state.bpId = Number(card.dataset.bp);
    $$("#bpGrid .bp-card").forEach((c) => c.classList.toggle("on", Number(c.dataset.bp) === state.bpId));
    const b = state.blueprints.find((x) => x.id === state.bpId);
    if (b) { $("#diffRange").value = Math.round(Number(b.target_difficulty) * 100); syncRange(); }
  });
  $("#btnAssemble").addEventListener("click", assemble);

  renderResult();
}

function syncRange() {
  const r = $("#diffRange");
  const v = Number(r.value) / 100;
  $("#diffVal").textContent = v.toFixed(2);
  r.style.setProperty("--fill", ((Number(r.value) - 30) / 50 * 100) + "%");
}

async function assemble() {
  const btn = $("#btnAssemble");
  const original = btn.textContent;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>组卷中…';
  try {
    const data = await api("/papers/assemble", {
      method: "POST",
      body: JSON.stringify({
        blueprint_id: state.bpId,
        title: $("#paperTitle").value.trim() || null,
        target_difficulty: Number($("#diffRange").value) / 100,
        restarts: 8,
      }),
    });
    state.paper = data.paper;
    state.report = data.report;
    renderResult();
    refreshStats();
    toast("已生成：" + data.paper.title);
    const el = $("#result");
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    toast(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

function qRow(n, it, showSwap) {
  const opts = (it.options || []).map((o) => "<div>" + esc(o) + "</div>").join("");
  return '<div class="q">' +
    '<div class="stem"><b>' + n + "．</b>" + esc(it.stem) + "</div>" +
    (opts ? '<div class="opts">' + opts + "</div>" : "") +
    '<div class="qmeta"><span class="tag-d ' + bandOf(it.difficulty) + '">' + bandLabel(it.difficulty) +
    " " + Number(it.difficulty).toFixed(2) + "</span>" +
    '<span class="tag-k">' + esc(it.knowledge_code) + " · " + it.score + " 分</span></div>" +
    (showSwap ? '<button class="btn sm swap" data-item="' + it.item_id + '">换一题</button>' : "") +
    "</div>";
}

function renderResult() {
  const box = $("#result");
  if (!box) return;
  if (!state.paper) { box.innerHTML = ""; return; }
  const paper = state.paper;
  const rep = state.report;

  const groups = {};
  paper.items.forEach((it) => { (groups[it.section] = groups[it.section] || []).push(it); });

  let n = 0;
  const body = rep.sections.map((sec) => {
    const items = (groups[sec.key] || []).slice().sort((a, b) => a.position - b.position);
    if (!items.length) return "";
    const rows = items.map((it) => { n += 1; return qRow(n, it, true); }).join("");
    return '<div class="sec-title">' + esc(sec.label) + "</div>" +
      '<div class="sec-hint">' + esc(sec.hint || "") + "　共 " + sec.count + " 题 / " + sec.score + " 分</div>" + rows;
  }).join("");

  const sheet =
    '<div class="sheet"><div class="sheet-head"><h2>' + esc(paper.title) + "</h2>" +
    '<div class="meta">考试时间 ' + paper.duration_min + " 分钟　满分 " + rep.total_score + " 分　共 " +
    rep.question_count + " 题</div>" +
    '<div class="blank">姓名 ____________　班级 ____________　考号 ____________</div></div>' +
    body + "</div>";

  const pct = Math.max(0, Math.min(100, rep.health));
  const rc = pct >= 85 ? "var(--good)" : pct >= 70 ? "var(--accent)" : pct >= 55 ? "var(--mid)" : "var(--bad)";
  const verdict = pct >= 85 ? "结构优良" : pct >= 70 ? "基本合格" : pct >= 55 ? "需要调整" : "建议重做";

  const curve = rep.curve.map((c) =>
    '<div class="bar' + (c.difficulty >= 0.55 ? " hi" : "") + '" style="height:' +
    Math.round(c.difficulty * 100) + '%" title="难度 ' + c.difficulty + '"></div>'
  ).join("");

  const cov = rep.coverage.slice().sort((a, b) => a.ratio - b.ratio).slice(0, 9).map((c) =>
    '<div class="cov-row"><span class="name">' + esc(c.name) + "</span><b>" + Math.round(c.ratio * 100) + "%</b>" +
    '<div class="track"><div class="fill' + (c.ratio < 0.5 ? " low" : c.ratio < 1 ? " warn" : "") +
    '" style="width:' + Math.round(c.ratio * 100) + '%"></div></div></div>'
  ).join("");

  const warnings = (rep.warnings || []).map((w) => '<div class="alert">' + esc(w) + "</div>").join("");

  const report =
    '<div class="report">' +

    '<div class="card"><h3>试卷体检</h3><div class="health">' +
    '<div class="ring" style="--p:' + pct + ";--rc:" + rc + '"><span>' + pct + "</span></div>" +
    '<div class="txt"><b>' + verdict + "</b><br>难度 " + rep.difficulty.toFixed(2) + " / 目标 " +
    rep.target_difficulty.toFixed(2) + "<br>考点覆盖 " + Math.round(rep.coverage_ratio * 100) + "%</div></div>" +
    '<div style="margin-top:12px">' +
    '<div class="kv"><span>预估平均得分率</span><b>' + rep.prediction.expected_rate.toFixed(1) + "%</b></div>" +
    '<div class="kv"><span>预估平均分</span><b>' + rep.prediction.expected_mean.toFixed(1) + " / " + rep.total_score + "</b></div>" +
    '<div class="kv"><span>及格概率</span><b>' + rep.prediction.pass_probability.toFixed(1) + "%</b></div>" +
    '<div class="kv"><span>预估用时</span><b>' + rep.est_time + " / " + rep.duration_min + " 分钟</b></div>" +
    (rep.difficulty_ceiling != null
      ? '<div class="kv"><span>题库难度上限</span><b>' + Number(rep.difficulty_ceiling).toFixed(2) + "</b></div>"
      : "") +
    "</div></div>" +

    '<div class="card"><h3>难度分布（按题序）</h3><div class="curve">' + curve + "</div>" +
    '<div style="font-size:11px;color:var(--muted);margin-top:6px">越高越难，虚线为整卷目标 ' +
    rep.target_difficulty.toFixed(2) + "</div></div>" +

    '<div class="card"><h3>考点覆盖（最弱 9 项）</h3>' + (cov || '<div style="font-size:12px;color:var(--muted)">—</div>') + "</div>" +

    (warnings ? '<div class="card"><h3>体检提示</h3>' + warnings + "</div>" : "") +

    '<div class="card"><h3>导出</h3>' +
    '<button class="btn primary" id="btnExport" style="width:100%">下载 Word 试卷</button>' +
    '<p style="font-size:11px;color:var(--muted);margin-top:8px;line-height:1.6">含卷面与分页的参考答案、解析，可直接在 Word 中排版修改。</p></div>' +

    "</div>";

  box.innerHTML = '<div class="result-grid">' + sheet + report + "</div>";

  $("#btnExport").addEventListener("click", () => {
    window.location.href = "/api/papers/" + paper.id + "/export.docx";
  });
  if (!box.dataset.bound) {
    box.dataset.bound = "1";
    box.addEventListener("click", onResultClick);
  }
}

function onResultClick(e) {
  const btn = e.target.closest("[data-item]");
  if (!btn || !state.paper) return;
  if (state.modalBusy) return;
  const item = state.paper.items.find((i) => i.item_id === Number(btn.dataset.item));
  if (!item) return;
  openAlternatives(item);
}

/** 打开弹窗立刻显示骨架，再异步填候选；失败信息留在弹窗里，而不是一闪而过的 toast */
function openAlternatives(item) {
  const modal = $("#modal");
  const body = $("#modalBody");
  $("#modalTitle").textContent = "换一道题 · 当前难度 " + Number(item.difficulty).toFixed(2);
  body.innerHTML = '<div class="empty"><span class="spinner dark"></span>正在检索同题型的候选题目…</div>';
  body.onclick = null;
  modal.hidden = false;
  document.body.classList.add("modal-open");
  $("#modalClose").focus();

  const pid = state.paper.id;
  api("/papers/" + pid + "/alternatives?item_id=" + item.item_id)
    .then((data) => { if (state.paper.id === pid && !modal.hidden) renderAlternatives(item, data.items || []); })
    .catch((err) => {
      if (modal.hidden) return;
      body.innerHTML = '<div class="empty"><b>候选题目加载失败</b>' + esc(err.message) + "</div>";
    });
}

function renderAlternatives(item, list) {
  const body = $("#modalBody");
  if (!list.length) {
    body.innerHTML = '<div class="empty"><b>没有可替换的题目</b>题库里该题型已经没有可换的题了</div>';
    return;
  }
  body.innerHTML = list.map((q) =>
    '<div class="alt" data-q="' + q.id + '"><div class="a-stem">' + esc(q.stem) + "</div>" +
    '<div class="a-meta"><span class="tag-d ' + bandOf(q.difficulty) + '">' + bandLabel(q.difficulty) +
    " " + Number(q.difficulty).toFixed(2) + "</span><span>" + esc(q.knowledge_code) +
    "</span><span>答案 " + esc(q.answer) + "</span></div></div>"
  ).join("");

  body.onclick = async (ev) => {
    const el = ev.target.closest("[data-q]");
    if (!el || el.classList.contains("busy")) return;
    el.classList.add("busy");
    state.modalBusy = true;
    try {
      const data = await api("/papers/" + state.paper.id + "/items/" + item.item_id + "/swap", {
        method: "POST",
        body: JSON.stringify({ question_id: Number(el.dataset.q) }),
      });
      state.paper = data.paper;
      state.report = data.report;
      closeModal();
      renderResult();
      toast("已替换该题，体检报告已刷新");
    } catch (err) {
      el.classList.remove("busy");
      toast(err.message);
    } finally {
      state.modalBusy = false;
    }
  };
}

function closeModal() {
  const modal = $("#modal");
  modal.hidden = true;
  $("#modalBody").innerHTML = "";
  $("#modalBody").onclick = null;
  document.body.classList.remove("modal-open");
}

/* ---------------------------------------------------------------- 题库 */
function flattenKnowledge(nodes, depth, out) {
  nodes.forEach((n) => {
    out.push({ code: n.code, name: n.name, depth: depth, count: n.question_count });
    flattenKnowledge(n.children || [], depth + 1, out);
  });
  return out;
}

function renderBank() {
  const v = $("#view");
  const flat = flattenKnowledge(state.knowledge, 0, []);
  const kOpts = flat.map((k) =>
    '<option value="' + k.code + '">' + "　".repeat(k.depth) + esc(k.name) + "（" + k.count + "）</option>"
  ).join("");

  v.innerHTML =
    '<div class="page-head"><div><h1>题库</h1><p>结构化题目资源，按题型、考点、难度检索</p></div></div>' +
    '<div class="toolbar">' +
    '<input type="search" id="bankKw" placeholder="搜索题干关键词" style="height:38px;border:1px solid var(--line);border-radius:9px;padding:0 12px;width:240px;font-size:13.5px">' +
    '<select id="bankType" style="height:38px;border:1px solid var(--line);border-radius:9px;padding:0 10px;font-size:13.5px">' +
    '<option value="">全部题型</option>' +
    state.meta.qtypes.map((t) => '<option value="' + t.key + '">' + t.label + "</option>").join("") +
    "</select>" +
    '<select id="bankKp" style="height:38px;border:1px solid var(--line);border-radius:9px;padding:0 10px;font-size:13.5px;max-width:240px">' +
    '<option value="">全部考点</option>' + kOpts + "</select>" +
    '<select id="bankBand" style="height:38px;border:1px solid var(--line);border-radius:9px;padding:0 10px;font-size:13.5px">' +
    '<option value="">全部难度</option><option value="0.7-1">易（≥0.7）</option>' +
    '<option value="0.4-0.7">中（0.4~0.7）</option><option value="0-0.4">难（&lt;0.4）</option></select>' +
    "</div>" +
    '<div id="bankTable"></div>';

  $("#bankKw").value = state.bank.keyword || "";
  $("#bankType").value = state.bank.qtype || "";
  $("#bankKp").value = state.bank.knowledge || "";
  $("#bankBand").value = state.bank.band || "";

  $("#bankKw").addEventListener("input", debounce(() => { state.bank.keyword = $("#bankKw").value.trim(); state.bank.page = 1; loadBank(); }, 300));
  $("#bankType").addEventListener("change", () => { state.bank.qtype = $("#bankType").value; state.bank.page = 1; loadBank(); });
  $("#bankKp").addEventListener("change", () => { state.bank.knowledge = $("#bankKp").value; state.bank.page = 1; loadBank(); });
  $("#bankBand").addEventListener("change", () => { state.bank.band = $("#bankBand").value; state.bank.page = 1; loadBank(); });

  loadBank();
}

function debounce(fn, ms) {
  let t;
  return function () { clearTimeout(t); t = setTimeout(fn, ms); };
}

async function loadBank() {
  const box = $("#bankTable");
  if (!box) return;
  box.innerHTML = '<div class="empty">加载中…</div>';
  const b = state.bank;
  const qs = new URLSearchParams();
  if (b.qtype) qs.set("qtype", b.qtype);
  if (b.knowledge) qs.set("knowledge", b.knowledge);
  if (b.keyword) qs.set("keyword", b.keyword);
  if (b.band) {
    const parts = b.band.split("-");
    qs.set("difficulty_min", parts[0]);
    qs.set("difficulty_max", parts[1]);
  }
  qs.set("page", b.page);
  qs.set("size", b.size);
  try {
    const data = await api("/questions?" + qs.toString());
    b.total = data.total;
    if (!data.items.length) {
      box.innerHTML = '<div class="table-wrap"><div class="empty"><b>没有匹配的题目</b>换个筛选条件试试</div></div>';
      return;
    }
    const rows = data.items.map((q) =>
      "<tr><td>" + q.id + '</td><td><div class="stem-cell">' + esc(q.stem) + "</div></td>" +
      '<td><span class="pill acc">' + esc(q.knowledge_name || q.knowledge_code) + "</span></td>" +
      "<td>" + esc(q.qtype) + "</td>" +
      '<td><span class="tag-d ' + bandOf(q.difficulty) + '">' + bandLabel(q.difficulty) + " " +
      Number(q.difficulty).toFixed(2) + "</span></td>" +
      "<td>" + q.score + "</td><td>" + (q.usage_count || 0) + "</td></tr>"
    ).join("");
    const pages = Math.max(1, Math.ceil(b.total / b.size));
    box.innerHTML =
      '<div class="table-wrap"><table><thead><tr><th>ID</th><th>题干</th><th>考点</th><th>题型</th><th>难度</th><th>分值</th><th>使用</th></tr></thead>' +
      "<tbody>" + rows + "</tbody></table></div>" +
      '<div class="pager"><span>共 ' + b.total + " 题 · 第 " + b.page + " / " + pages + " 页</span>" +
      '<button class="btn sm" id="prevPg"' + (b.page <= 1 ? " disabled" : "") + ">上一页</button>" +
      '<button class="btn sm" id="nextPg"' + (b.page >= pages ? " disabled" : "") + ">下一页</button></div>";
    $("#prevPg").addEventListener("click", () => { b.page = Math.max(1, b.page - 1); loadBank(); });
    $("#nextPg").addEventListener("click", () => { b.page = Math.min(pages, b.page + 1); loadBank(); });
  } catch (err) {
    box.innerHTML = '<div class="empty">' + esc(err.message) + "</div>";
  }
}

/* ---------------------------------------------------------------- 试卷库 */
async function renderPapers() {
  const v = $("#view");
  v.innerHTML =
    '<div class="page-head"><div><h1>试卷库</h1><p>已生成的试卷，可重新打开调整或导出</p></div></div>' +
    '<div id="paperList"><div class="empty">加载中…</div></div>';
  try {
    const data = await api("/papers");
    const box = $("#paperList");
    if (!data.items.length) {
      box.innerHTML = '<div class="table-wrap"><div class="empty"><b>还没有试卷</b>去工作台生成第一套试卷吧</div></div>';
      return;
    }
    const rows = data.items.map((p) =>
      "<tr><td><b>" + esc(p.title) + "</b></td>" +
      "<td>" + p.total_score + " 分</td><td>" + p.question_count + " 题</td>" +
      '<td><span class="tag-d ' + bandOf(p.difficulty) + '">' + Number(p.difficulty).toFixed(2) + "</span></td>" +
      '<td style="color:var(--muted);font-size:12px">' + esc(p.created_at || "") + "</td>" +
      '<td style="text-align:right;white-space:nowrap">' +
      '<button class="btn sm" data-open="' + p.id + '">打开</button> ' +
      '<a class="btn sm" href="/api/papers/' + p.id + '/export.docx">导出</a> ' +
      '<button class="btn sm" data-del="' + p.id + '">删除</button></td></tr>'
    ).join("");
    box.innerHTML =
      '<div class="table-wrap"><table><thead><tr><th>标题</th><th>总分</th><th>题量</th><th>难度</th><th>创建时间</th><th></th></tr></thead><tbody>' +
      rows + "</tbody></table></div>";
    box.addEventListener("click", async (e) => {
      const open = e.target.closest("[data-open]");
      const del = e.target.closest("[data-del]");
      if (open) await gotoPaper(Number(open.dataset.open));
      if (del) {
        if (!confirm("确定删除这套试卷？")) return;
        await api("/papers/" + del.dataset.del, { method: "DELETE" });
        if (state.paper && state.paper.id === Number(del.dataset.del)) {
          state.paper = null;
          state.report = null;
        }
        refreshStats();
        renderPapers();
        toast("已删除");
      }
    });
  } catch (err) {
    $("#paperList").innerHTML = '<div class="empty">' + esc(err.message) + "</div>";
  }
}

async function gotoPaper(id) {
  const data = await api("/papers/" + id);
  state.paper = data.paper;
  state.report = data.report;
  state.bpId = data.paper.blueprint_id;
  if (location.hash.indexOf("#/workbench") === 0) renderWorkbench();
  else location.hash = "#/workbench";
}

/* ---------------------------------------------------------------- 路由 */
const routes = { workbench: renderWorkbench, bank: renderBank, papers: renderPapers };

function route() {
  const raw = location.hash.replace(/^#\//, "") || "workbench";
  const parts = raw.split("?");
  const name = parts[0];
  const fn = routes[name] || renderWorkbench;
  $$("#nav a").forEach((a) => a.classList.toggle("on", a.dataset.route === name));
  fn();
  window.scrollTo(0, 0);

  const pid = new URLSearchParams(parts[1] || "").get("paper");
  if (pid && (!state.paper || state.paper.id !== Number(pid))) {
    gotoPaper(Number(pid)).catch((err) => toast(err.message));
  }
}

async function refreshStats() {
  try {
    const s = await api("/stats");
    state.stats = s;
    $("#stQ").textContent = s.questions;
    $("#stB").textContent = s.blueprints;
    $("#stP").textContent = s.papers;
  } catch (e) { /* 忽略 */ }
}

async function boot() {
  try {
    const [meta, bps, kp] = await Promise.all([
      api("/meta"), api("/blueprints"), api("/knowledge"),
    ]);
    state.meta = meta;
    state.blueprints = bps.items;
    state.knowledge = kp.tree;
    state.bpId = state.blueprints.length ? state.blueprints[0].id : null;
    refreshStats();
    route();
  } catch (err) {
    $("#view").innerHTML = '<div class="empty"><b>无法连接后端</b>' + esc(err.message) + "</div>";
  }
}

window.addEventListener("hashchange", route);
$("#modalClose").addEventListener("click", closeModal);
$("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeModal(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });

boot();
