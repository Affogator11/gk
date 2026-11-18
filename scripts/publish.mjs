#!/usr/bin/env node
/**
 * 把 zujuan 源码发布到 GitHub —— 不依赖 git 命令，全程走 REST API。
 *
 * 用法：
 *   $env:GITHUB_TOKEN="ghp_xxx"; node scripts/publish.mjs            # 创建（或更新）私有仓库
 *   node scripts/publish.mjs --repo zujuan --public                  # 公开仓库
 *   node scripts/publish.mjs --dry                                   # 只列出会上传的文件
 *
 * Token 需要 repo 权限（classic: repo；fine-grained: Administration + Contents 读写）。
 */
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(import.meta.dirname, "..");
const API = "https://api.github.com";
const argv = process.argv.slice(2);
const flag = (n) => argv.includes("--" + n);
const opt = (n, d) => {
  const i = argv.indexOf("--" + n);
  return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[i + 1] : d;
};

const REPO = opt("repo", "zujuan");
const PRIVATE = !flag("public");
const DRY = flag("dry");
function readTokenFile() {
  const cands = [path.resolve(ROOT, "..", ".gh_token"), path.join(ROOT, ".gh_token")];
  for (const p of cands) {
    try {
      const t = fs.readFileSync(p, "utf8").trim().replace(/^Bearer\s+/i, "");
      if (t) return t;
    } catch { /* 文件不存在就换下一个 */ }
  }
  return "";
}
const TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || opt("token", "") || readTokenFile();
const CHECK = flag("check");

const SKIP_DIRS = new Set(["vendor", "node_modules", "__pycache__", ".npm-cache", ".wheels", "out", "shots", ".git"]);
const SKIP_EXT = new Set([".pyc", ".db", ".db-wal", ".db-shm", ".docx", ".whl", ".zip"]);
const SKIP_FILES = new Set(["package.json", "package-lock.json"]);

function walk(dir, base = "") {
  const out = [];
  let entries = [];
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return out; }
  for (const ent of entries) {
    const rel = base ? base + "/" + ent.name : ent.name;
    const abs = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      if (SKIP_DIRS.has(ent.name)) continue;
      out.push(...walk(abs, rel));
    } else {
      if (SKIP_FILES.has(ent.name) || SKIP_EXT.has(path.extname(ent.name))) continue;
      out.push({ rel, abs });
    }
  }
  return out;
}

async function api(pathname, init = {}) {
  const res = await fetch(API + pathname, {
    ...init,
    headers: {
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      Authorization: "Bearer " + TOKEN,
      "Content-Type": "application/json",
      "User-Agent": "zujuan-publish",
      ...(init.headers || {}),
    },
  });
  const text = await res.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = text; }
  if (!res.ok) {
    const msg = body && body.message ? body.message : String(text).slice(0, 200);
    throw new Error(res.status + " " + pathname + " -> " + msg);
  }
  return body;
}

const files = walk(ROOT).sort((a, b) => a.rel.localeCompare(b.rel));
console.log("待上传 " + files.length + " 个文件：");
for (const f of files) console.log("  " + f.rel + "  " + (fs.statSync(f.abs).size / 1024).toFixed(1) + "KB");
if (DRY) process.exit(0);
if (!TOKEN) {
  console.error("\n缺少 token：先设置 $env:GITHUB_TOKEN=ghp_xxx 再运行。");
  process.exit(1);
}

const me = await api("/user");
const owner = me.login;
console.log("\n账号：" + owner + (TOKEN.startsWith("github_pat_") ? "（fine-grained token）" : "（classic token）"));

if (CHECK) {
  try {
    const r = await api("/repos/" + owner + "/" + REPO);
    console.log("仓库可访问：" + r.html_url + "（" + (r.private ? "私有" : "公开") + "）");
    const push = r.permissions && r.permissions.push;
    console.log("写权限：" + (push ? "有" : "无 —— token 需要 Contents: Read and write"));
  } catch (e) {
    console.log("仓库不可访问：" + e.message);
    console.log("若为 404，检查仓库名是否写错（当前 --repo " + REPO + "），或 token 未勾选该仓库。");
  }
  process.exit(0);
}

let repo = null;
try {
  repo = await api("/repos/" + owner + "/" + REPO);
  console.log("仓库已存在，更新内容：" + repo.html_url);
} catch (e) {
  if (!String(e.message).startsWith("404")) throw e;
}

if (!repo) {
  repo = await api("/user/repos", {
    method: "POST",
    body: JSON.stringify({
      name: REPO,
      description: "知卷 · 面向高中老师的智能组卷系统（细目表 + 组卷引擎 + 试卷体检 + Word 导出）",
      private: PRIVATE,
      auto_init: false,
      has_issues: true,
      has_wiki: false,
    }),
  });
  console.log("已创建仓库：" + repo.html_url);
}

const branch = repo.default_branch || "main";
let uploaded = 0;
for (const f of files) {
  const content = fs.readFileSync(f.abs).toString("base64");
  const body = { message: "add " + f.rel, content, branch };
  const current = await fetch(API + "/repos/" + owner + "/" + REPO + "/contents/" + f.rel, {
    headers: { Authorization: "Bearer " + TOKEN, Accept: "application/vnd.github+json", "User-Agent": "zujuan-publish" },
  });
  if (current.ok) {
    const meta = await current.json();
    if (meta.sha) body.sha = meta.sha;
    const same = meta.content && meta.content.replace(/\n/g, "") === content;
    if (same) { console.log("  = " + f.rel + "（未变化）"); continue; }
    body.message = "update " + f.rel;
  }
  try {
    await api("/repos/" + owner + "/" + REPO + "/contents/" + f.rel, { method: "PUT", body: JSON.stringify(body) });
  } catch (e) {
    // 空仓库还没有默认分支时，带 branch 会 422；去掉 branch 让 GitHub 建首个提交
    if (!/422/.test(e.message) || !body.branch) throw e;
    const first = { message: body.message, content: body.content };
    await api("/repos/" + owner + "/" + REPO + "/contents/" + f.rel, { method: "PUT", body: JSON.stringify(first) });
  }
  uploaded++;
  console.log("  + " + f.rel);
}

console.log("\n完成：" + repo.html_url + "（" + uploaded + " 个文件写入）");
