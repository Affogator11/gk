import fs from "node:fs";
import path from "node:path";
import { JSDOM, VirtualConsole } from "jsdom";

const BASE = "http://127.0.0.1:8123";
const ROOT = path.resolve(import.meta.dirname, "..");
const errors = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errors.push("jsdomError: " + (e.stack || e.message)));
vc.on("error", (...a) => errors.push("console.error: " + a.join(" ")));

const html = fs.readFileSync(path.join(ROOT, "web/index.html"), "utf8")
  .replace('<link rel="stylesheet" href="/styles.css" />', "<style>" + fs.readFileSync(path.join(ROOT, "web/styles.css"), "utf8") + "</style>");

const dom = new JSDOM(html, {
  url: BASE + "/#/workbench?paper=1",
  runScripts: "outside-only",
  pretendToBeVisual: true,
  virtualConsole: vc,
});
const w = dom.window;
const hits = [];
w.fetch = (u, o) => { hits.push(String(u)); return globalThis.fetch(new URL(u, BASE).href, o); };
w.scrollTo = () => {};
w.HTMLElement.prototype.scrollIntoView = () => {};
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const $ = (s) => w.document.querySelector(s);
const disp = (s) => w.getComputedStyle($(s)).display;

w.eval(fs.readFileSync(path.join(ROOT, "web/app.js"), "utf8"));
await wait(1800);

let fail = 0;
const ok = (cond, label, extra) => { console.log((cond ? "  PASS " : "  FAIL ") + label + (extra ? "  " + extra : "")); if (!cond) fail++; };

console.log("[1] 初始状态");
ok(disp("#modal") === "none", "弹窗默认不可见", "display=" + disp("#modal"));
ok(disp("#toast") === "none", "toast 默认不可见", "display=" + disp("#toast"));
ok(w.document.querySelectorAll(".q").length > 0, "深链加载了试卷", w.document.querySelectorAll(".q").length + " 题");

console.log("[2] 打开换题弹窗");
const before = hits.filter((u) => u.includes("/alternatives")).length;
$(".q .swap").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
ok(disp("#modal") === "grid", "弹窗可见", "display=" + disp("#modal"));
ok(/正在检索/.test($("#modalBody").textContent), "先显示加载态");
await wait(1500);
ok($("#modalBody").querySelectorAll(".alt").length > 0, "候选已渲染", $("#modalBody").querySelectorAll(".alt").length + " 个");
const after = hits.filter((u) => u.includes("/alternatives")).length;
ok(after - before === 1, "一次点击只发一次请求", (after - before) + " 次");
ok($("#modalTitle").textContent.includes("当前难度"), "标题显示难度", $("#modalTitle").textContent);

console.log("[3] 点候选换题");
const firstStem = $(".q .stem").textContent;
$("#modalBody .alt").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
await wait(1500);
ok(disp("#modal") === "none", "换题后弹窗关闭", "display=" + disp("#modal"));
ok($("#toast").textContent.includes("已替换"), "有成功提示", $("#toast").textContent);
const changed = w.document.querySelectorAll(".q .stem").length > 0 && Array.from(w.document.querySelectorAll(".q .stem")).some((s) => s.textContent !== firstStem);
ok(changed, "卷面已更新");

console.log("[4] Esc 关闭 / 连点不叠加");
$(".q .swap").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
await wait(800);
const b2 = hits.filter((u) => u.includes("/alternatives")).length;
$(".q .swap").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
await wait(800);
const b3 = hits.filter((u) => u.includes("/alternatives")).length;
ok(b3 - b2 === 1, "再次点击仍只发一次请求", (b3 - b2) + " 次");
w.document.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
ok(disp("#modal") === "none", "Esc 可关闭弹窗");

console.log("[5] 重新组卷两次后仍然只发一次请求");
$("#diffRange").value = 45;
$("#diffRange").dispatchEvent(new w.Event("input", { bubbles: true }));
$("#btnAssemble").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
await wait(3500);
$("#btnAssemble").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
await wait(3500);
const b4 = hits.filter((u) => u.includes("/alternatives")).length;
$(".q .swap").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
await wait(1200);
const b5 = hits.filter((u) => u.includes("/alternatives")).length;
ok(b5 - b4 === 1, "多次组卷后监听器未叠加", (b5 - b4) + " 次");
ok($("#modalBody").querySelectorAll(".alt").length > 0, "候选正常");

console.log("[6] 题库筛选回填");
w.location.hash = "#/bank";
await wait(1200);
$("#bankType").value = "single";
$("#bankType").dispatchEvent(new w.Event("change", { bubbles: true }));
await wait(1000);
w.location.hash = "#/workbench";
await wait(600);
w.location.hash = "#/bank";
await wait(1200);
ok($("#bankType").value === "single", "返回后筛选条件保留", $("#bankType").value);

console.log("\n" + (fail ? fail + " 项失败" : "全部通过"));
if (errors.length) console.log("console errors:\n" + errors.slice(0, 5).join("\n"));
process.exit(fail ? 1 : 0);
