#!/usr/bin/env node
/** 把源码打成 zip（无第三方依赖，deflate 压缩），用于备份或手动上传 GitHub。 */
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

const ROOT = path.resolve(import.meta.dirname, "..");
const OUT = path.join(ROOT, "out");
const SKIP_DIRS = new Set(["vendor", "node_modules", "__pycache__", ".npm-cache", ".wheels", "out", "shots", ".git", ".tmp"]);
const SKIP_EXT = new Set([".pyc", ".db", ".db-wal", ".db-shm", ".docx", ".whl", ".zip"]);
const SKIP_FILES = new Set(["package.json", "package-lock.json"]);

const CRC_TABLE = (() => {
  const t = new Int32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c;
  }
  return t;
})();
function crc32(buf) {
  let c = -1;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ -1) >>> 0;
}

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
    } else if (!SKIP_FILES.has(ent.name) && !SKIP_EXT.has(path.extname(ent.name))) {
      out.push({ rel, abs });
    }
  }
  return out;
}

const files = walk(ROOT).sort((a, b) => a.rel.localeCompare(b.rel));
const chunks = [];
const central = [];
let offset = 0;

function dosTime(d) {
  return { time: (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1),
           date: ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate() };
}

for (const f of files) {
  const raw = fs.readFileSync(f.abs);
  const deflated = zlib.deflateRawSync(raw, { level: 9 });
  const useDeflate = deflated.length < raw.length;
  const data = useDeflate ? deflated : raw;
  const crc = crc32(raw);
  const name = Buffer.from(f.rel, "utf8");
  const { time, date } = dosTime(fs.statSync(f.abs).mtime);
  const local = Buffer.alloc(30);
  local.writeUInt32LE(0x04034b50, 0);
  local.writeUInt16LE(20, 4);
  local.writeUInt16LE(0x0800, 6);
  local.writeUInt16LE(useDeflate ? 8 : 0, 8);
  local.writeUInt16LE(time, 10);
  local.writeUInt16LE(date, 12);
  local.writeUInt32LE(crc, 14);
  local.writeUInt32LE(data.length, 18);
  local.writeUInt32LE(raw.length, 22);
  local.writeUInt16LE(name.length, 26);
  local.writeUInt16LE(0, 28);
  chunks.push(local, name, data);

  const cen = Buffer.alloc(46);
  cen.writeUInt32LE(0x02014b50, 0);
  cen.writeUInt16LE(20, 4);
  cen.writeUInt16LE(20, 6);
  cen.writeUInt16LE(0x0800, 8);
  cen.writeUInt16LE(useDeflate ? 8 : 0, 10);
  cen.writeUInt16LE(time, 12);
  cen.writeUInt16LE(date, 14);
  cen.writeUInt32LE(crc, 16);
  cen.writeUInt32LE(data.length, 20);
  cen.writeUInt32LE(raw.length, 24);
  cen.writeUInt16LE(name.length, 28);
  cen.writeUInt32LE(offset, 42);
  central.push(cen, name);

  offset += local.length + name.length + data.length;
}

const centralBuf = Buffer.concat(central);
const eocd = Buffer.alloc(22);
eocd.writeUInt32LE(0x06054b50, 0);
eocd.writeUInt16LE(files.length, 8);
eocd.writeUInt16LE(files.length, 10);
eocd.writeUInt32LE(centralBuf.length, 12);
eocd.writeUInt32LE(offset, 16);

fs.mkdirSync(OUT, { recursive: true });
const stamp = new Date().toISOString().slice(0, 10).replace(/-/g, "");
const target = path.join(OUT, "zujuan-src-" + stamp + ".zip");
fs.writeFileSync(target, Buffer.concat([...chunks, centralBuf, eocd]));
console.log("已生成 " + target + "（" + files.length + " 个文件，" + (fs.statSync(target).size / 1024).toFixed(1) + "KB）");
