import fs from "node:fs";
import path from "node:path";
import { JSDOM, VirtualConsole } from "jsdom";

const BASE = "http://127.0.0.1:8123";
const ROOT = path.resolve(import.meta.dirname, "..");
const errors = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errors.push("jsdomError: " + (e.stack || e.message)));
vc.on("error", (...a) => errors.push("console.error: " + a.join(" ")));

const dom = new JSDOM(fs.readFileSync(path.join(ROOT, "web/index.html"), "utf8"), {
  url: BASE + "/#/workbench",
  runScripts: "outside-only",
  pretendToBeVisual: true,
  virtualConsole: vc,
});
const w = dom.window;
w.fetch = (u, o) => globalThis.fetch(new URL(u, BASE).href, o);
w.scrollTo = () => {};
w.HTMLElement.prototype.scrollIntoView = () => {};
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const $ = (s) => w.document.querySelector(s);
const txt = (s) => ($(s) ? $(s).textContent.trim().slice(0, 50) : "(none)");

w.eval(fs.readFileSync(path.join(ROOT, "web/app.js"), "utf8"));
await wait(1500);

console.log("初始 h1:", txt("h1"), "| 卡片:", w.document.querySelectorAll(".bp-card").length,
            "| 结果区空:", $("#result").innerHTML === "");
console.log("滑块默认值:", $("#diffRange").value, $("#diffVal").textContent);

$("#paperTitle").value = "高三上学期期中模拟卷";
$("#diffRange").value = 50;
$("#diffRange").dispatchEvent(new w.Event("input", { bubbles: true }));
$("#btnAssemble").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
await wait(2500);

console.log("生成后 标题:", txt(".sheet-head h2"));
console.log("题数:", w.document.querySelectorAll(".q").length, "| 体检:", txt(".ring span"),
            "| 预警:", w.document.querySelectorAll(".alert").length);
console.log("kvs:", Array.from(w.document.querySelectorAll(".kv")).map((k) => k.textContent.trim().replace(/\s+/g, "")).join(" | "));
console.log("导出按钮:", !!$("#btnExport"));

w.location.hash = "#/papers";
await wait(1000);
const openBtn = w.document.querySelector("[data-open]");
console.log("试卷库行数:", w.document.querySelectorAll("#paperList tbody tr").length, "| 有打开按钮:", !!openBtn);
if (openBtn) {
  openBtn.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await wait(1500);
  console.log("打开后 hash:", w.location.hash, "| 题数:", w.document.querySelectorAll(".q").length);
}
console.log("--- errors ---");
console.log(errors.length ? errors.slice(0, 5).join("\n") : "(none)");
