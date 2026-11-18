import fs from "node:fs";
import path from "node:path";
import { JSDOM, VirtualConsole } from "jsdom";

const BASE = "http://127.0.0.1:8123";
const ROOT = path.resolve(import.meta.dirname, "..");

const errors = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errors.push("jsdomError: " + (e.stack || e.message)));
vc.on("error", (...a) => errors.push("console.error: " + a.join(" ")));
vc.on("warn", (...a) => errors.push("console.warn: " + a.join(" ")));

const html = fs.readFileSync(path.join(ROOT, "web/index.html"), "utf8");
const appjs = fs.readFileSync(path.join(ROOT, "web/app.js"), "utf8");

const dom = new JSDOM(html, {
  url: BASE + "/#/workbench?paper=1",
  runScripts: "outside-only",
  pretendToBeVisual: true,
  virtualConsole: vc,
});
const w = dom.window;
w.fetch = (u, o) => globalThis.fetch(new URL(u, BASE).href, o);
w.scrollTo = () => {};
w.HTMLElement.prototype.scrollIntoView = () => {};
w.confirm = () => true;

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

w.eval(appjs);
await wait(2000);

const $ = (s) => w.document.querySelector(s);
const txt = (s) => ($(s) ? $(s).textContent.trim().slice(0, 60) : "(none)");

console.log("h1:", txt("h1"));
console.log("bp cards:", w.document.querySelectorAll(".bp-card").length);
console.log("sheet title:", txt(".sheet-head h2"));
console.log("questions rendered:", w.document.querySelectorAll(".q").length);
console.log("health:", txt(".ring span"));
console.log("report kvs:", w.document.querySelectorAll(".kv").length);
console.log("warnings:", w.document.querySelectorAll(".alert").length);
console.log("stats sidebar:", txt("#stQ"), txt("#stB"), txt("#stP"));

// 交互：换一题
const swapBtn = w.document.querySelector(".q .swap");
if (swapBtn) {
  swapBtn.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await wait(800);
  console.log("modal hidden:", $("#modal").hidden, "alts:", w.document.querySelectorAll(".alt").length);
  const alt = w.document.querySelector(".alt");
  if (alt) {
    alt.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
    await wait(1000);
    console.log("after swap questions:", w.document.querySelectorAll(".q").length, "toast:", txt("#toast"));
  }
  $("#modalClose").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
}

// 交互：题库页
w.location.hash = "#/bank";
await wait(1200);
console.log("bank rows:", w.document.querySelectorAll("tbody tr").length, "pager:", txt(".pager"));

// 交互：试卷库
w.location.hash = "#/papers";
await wait(1000);
console.log("paper rows:", w.document.querySelectorAll("#paperList tbody tr").length);

console.log("--- errors ---");
console.log(errors.length ? errors.slice(0, 8).join("\n") : "(none)");
