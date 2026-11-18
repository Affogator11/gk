# 部署上线指南

知卷是**单进程应用**：FastAPI 同时提供 `/api/*` 接口和 `web/` 里的前端页面，
所以部署时**只需要一个服务、一个端口**，不用拆分前后端。

前端是原生 HTML/CSS/JS，没有构建步骤；后端依赖见 `requirements.txt`。

---

## 一、环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PORT` | `8123`（run.py）/ `8000`（Docker） | 监听端口，托管平台一般会自动注入 |
| `HOST` | `127.0.0.1` | 容器内要设成 `0.0.0.0` 才能被外部访问 |
| `ZUJUAN_DATA_DIR` | 项目内 `data/` | SQLite 数据库所在目录，**部署时指向持久盘** |
| `ZUJUAN_DB` | `$ZUJUAN_DATA_DIR/zujuan.db` | 直接指定数据库文件路径（优先级更高） |
| `ZUJUAN_AUTO_INIT` | `1` | `0` 关闭启动时自动建表/灌示例数据 |

首次启动会自动建表并在空库中灌入 65 道示例题 + 3 套细目表；非空库不会重复灌。

---

## 二、方案 A：Render（免费，最快上线，不用服务器）

### A1. 用蓝图（推荐，仓库里已有 `render.yaml`）

1. 注册并登录 https://render.com （可以用 GitHub 账号直接登录）
2. 右上 **New +** → **Blueprint**
3. 选择仓库 `gk` → **Connect** → 直接 **Apply**
4. 等构建完成（3–5 分钟），访问形如 `https://zujuan-xxxx.onrender.com` 的地址

### A2. 手动建服务

1. **New +** → **Web Service** → 连仓库 `gk`
2. 填写：

| 字段 | 值 |
|---|---|
| Name | `zujuan` |
| Region | Singapore（离国内最近） |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Plan | Free |

3. **Environment Variables** 加两条：
   - `PYTHON_VERSION` = `3.12.6`
   - `ZUJUAN_DATA_DIR` = `/opt/render/project/src/data`（免费实例可写但重启即清空）
4. **Create Web Service**

### A3. 免费版的三个限制（务必知道）

1. **15 分钟无访问会休眠**，下次有人打开要等 30–60 秒才醒（页面会白屏一会儿）
2. **没有持久盘**：每次重启/重新部署，数据库回到初始状态 —— 老师组的卷会丢
3. 国内访问速度一般，首屏 1–3 秒

要让试卷长期保存，升到 Starter（约 $7/月）后在服务 → **Disks** 加一块 1GB 盘、
Mount Path 填 `/var/data`，同时把环境变量 `ZUJUAN_DATA_DIR` 改成 `/var/data`
（`render.yaml` 里已留好注释，改完重新部署即可）。

---

## 三、方案 B：Docker（任意云服务器）

仓库自带 `Dockerfile`，内存 512MB 以上的机器都跑得动。

```bash
# 在服务器上
git clone https://github.com/Affogator11/gk.git zujuan && cd zujuan

docker build -t zujuan .
docker run -d --name zujuan \
  -p 80:8000 \
  -v /opt/zujuan-data:/data \
  --restart unless-stopped \
  zujuan
```

`-v /opt/zujuan-data:/data` 把数据库挂到宿主机，容器重建也不丢数据。

**国内服务器**：解析域名 → 备案 → Nginx 反代到 8000 端口即可。
阿里云/腾讯云轻量学生机约 ¥10/月，访问速度比 Render 好一个量级。

### Nginx 反代示例

```nginx
server {
    listen 80;
    server_name paper.example.com;
    client_max_body_size 10m;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }
}
```

---

## 四、本地验证部署形态

```powershell
# 用独立数据目录 + 非默认端口，模拟线上环境
$env:ZUJUAN_DATA_DIR="$PWD\.tmp\deploytest"
$env:PORT="8125"
python backend\run.py
```

浏览器打开 http://127.0.0.1:8125 ，能组卷、能导出 docx 就说明部署形态没问题。

---

## 五、常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 构建失败 `Could not find a version of fastapi` | `PYTHON_VERSION` 太老 | 设成 3.12.6 |
| 部署成功但打开 502 | 启动命令没 `cd backend`，模块 `app` 找不到 | 用文档里的 Start Command |
| 页面能开，接口全 404 | 前端请求的是 `/api/...`，代理把路径吃掉了 | Nginx 里不要改写路径 |
| 重启后试卷全没了 | 免费实例无持久盘 | 加 Disk 或换付费/自建服务器 |
| 首次访问很慢 | 免费实例从休眠唤醒 | 正常，或升级套餐 |
| docx 导出 500 | 容器缺 `python-docx` | `pip install -r requirements.txt` 已包含 |

---

## 六、上线前必须补的功课

这个 MVP 是**演示形态**，真要给老师用之前至少要补：

1. **登录与权限**：现在没有用户体系，任何人打开都能删试卷
2. **题库版权**：示例题仅用于跑通流程，真实组卷必须换成有授权的真题
3. **数据备份**：SQLite 单文件，定时复制一份到对象存储
4. **HTTPS**：Render 自带；自建服务器用 Caddy 或 certbot
