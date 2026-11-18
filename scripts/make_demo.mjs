import fs from "node:fs";
const BASE = "http://127.0.0.1:8123";
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
for (let i = 0; i < 60; i++) {
  try { const r = await fetch(BASE + "/api/health"); if (r.ok) break; } catch (e) {}
  await wait(300);
}
const res = await fetch(BASE + "/api/papers/assemble", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ blueprint_id: 1, target_difficulty: 0.6, restarts: 10 }),
});
const data = await res.json();
const pid = data.paper.id;
console.log("paper", pid, "difficulty", data.report.difficulty, "target", data.report.target_difficulty,
            "health", data.report.health, "coverage", data.report.coverage_ratio,
            "est", data.report.est_time, "pred", data.report.prediction.expected_rate);
console.log("warnings", JSON.stringify(data.report.warnings));
const docx = await fetch(BASE + "/api/papers/" + pid + "/export.docx");
const buf = Buffer.from(await docx.arrayBuffer());
fs.mkdirSync("out", { recursive: true });
fs.writeFileSync("out/paper-" + pid + ".docx", buf);
console.log("docx bytes", buf.length);
const list = await (await fetch(BASE + "/api/papers")).json();
console.log("list keys", Object.keys(list.items[0]).join(","));
