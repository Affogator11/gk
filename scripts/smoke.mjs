
const base = "http://127.0.0.1:8123";
async function waitUp() {
  for (let i = 0; i < 60; i++) {
    try { const r = await fetch(base + "/api/health"); if (r.ok) return true; } catch (e) {}
    await new Promise(r => setTimeout(r, 300));
  }
  return false;
}
(async () => {
  if (!await waitUp()) { console.log("SERVER NOT UP"); return; }
  const show = async (label, url, opts) => {
    try {
      const r = await fetch(base + url, opts);
      const ct = r.headers.get("content-type") || "";
      if (ct.includes("json")) {
        const j = await r.json();
        const s = JSON.stringify(j);
        console.log(label, r.status, s.length > 400 ? s.slice(0, 400) + "..." : s);
        return j;
      } else {
        console.log(label, r.status, ct, "bytes=", (await r.arrayBuffer()).byteLength);
      }
    } catch (e) { console.log(label, "ERR", e.message); }
  };
  await show("meta", "/api/meta");
  await show("bps", "/api/blueprints");
  await show("knowledge", "/api/knowledge");
  await show("questions", "/api/questions?size=2");
  await show("stats", "/api/stats");
  const created = await show("assemble", "/api/papers/assemble", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ blueprint_id: 1, target_difficulty: 0.55, restarts: 6 }),
  });
  if (created && created.paper) {
    const pid = created.paper.id;
    console.log("PAPER", pid, created.paper.title, "items", created.paper.items.length, "health", created.report.health);
    console.log("sections", JSON.stringify(created.report.sections));
    console.log("warnings", JSON.stringify(created.report.warnings));
    console.log("pred", JSON.stringify(created.report.prediction.expected_rate));
    await show("get", "/api/papers/" + pid);
    await show("alts", "/api/papers/" + pid + "/alternatives?item_id=" + created.paper.items[0].item_id);
    await show("docx", "/api/papers/" + pid + "/export.docx");
    await show("list", "/api/papers");
    await show("index", "/");
    await show("css", "/styles.css");
    await show("js", "/app.js");
  }
})();
