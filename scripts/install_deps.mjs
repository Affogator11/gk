import { mkdir, writeFile, rm, readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { createWriteStream } from "node:fs";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";

const ROOT = process.argv[2];
const PKGS = process.argv.slice(3);
const WHEEL_DIR = path.join(ROOT, ".wheels");
const VENDOR = path.join(ROOT, "backend", "vendor");

const PY_TAGS = ["cp312-cp312-win_amd64", "cp312-abi3-win_amd64", "cp311-abi3-win_amd64", "py3-none-any", "py2.py3-none-any"];

function norm(name) { return name.toLowerCase().replace(/[-_.]+/g, "-"); }

async function pypiJson(name) {
  const res = await fetch("https://pypi.org/pypi/" + name + "/json", { headers: { "accept": "application/json" } });
  if (!res.ok) throw new Error(name + " -> HTTP " + res.status);
  return res.json();
}

function pickWheel(files) {
  const wheels = files.filter(f => f.filename.endsWith(".whl") && !f.yanked);
  for (const tag of PY_TAGS) {
    const hit = wheels.find(f => f.filename.endsWith("-" + tag + ".whl"));
    if (hit) return hit;
  }
  return null;
}

function parseRequires(name, requires) {
  const out = [];
  for (const raw of requires || []) {
    if (raw.includes("extra ==")) continue;
    const m = raw.match(/^([A-Za-z0-9._-]+)/);
    if (!m) continue;
    out.push(norm(m[1]));
  }
  return out;
}

await mkdir(WHEEL_DIR, { recursive: true });
await mkdir(VENDOR, { recursive: true });

const seen = new Set();
const queue = [...PKGS.map(norm)];
const wheels = [];

while (queue.length) {
  const name = queue.shift();
  if (seen.has(name)) continue;
  seen.add(name);
  const data = await pypiJson(name);
  const info = data.info;
  const wheel = pickWheel(data.urls);
  if (!wheel) { console.log("SKIP(no wheel):", name, data.info.version); continue; }
  console.log("PICK:", name, wheel.filename);
  wheels.push(wheel);
  for (const dep of parseRequires(name, info.requires_dist)) {
    if (name === "uvicorn" && dep === "uvloop") continue;
    if (!seen.has(dep)) queue.push(dep);
  }
}

// download
for (const w of wheels) {
  const dest = path.join(WHEEL_DIR, w.filename);
  if (existsSync(dest)) { console.log("CACHED:", w.filename); continue; }
  const res = await fetch(w.url);
  if (!res.ok) throw new Error("download fail " + w.filename + " " + res.status);
  await pipeline(Readable.fromWeb(res.body), createWriteStream(dest));
  console.log("DOWN:", w.filename, (w.size/1024).toFixed(0) + "KB");
}

const manifest = { wheels: wheels.map(w => w.filename), packages: [...seen].sort() };
await writeFile(path.join(ROOT, ".wheels", "manifest.json"), JSON.stringify(manifest, null, 2));
console.log("DONE", wheels.length, "wheels");