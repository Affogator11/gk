# 给「知卷」上传代码用的 GitHub 令牌：完整教程

> 你截图的那个页面是 **仓库 → 设置 → 常规**（改仓库名、模板库、Wikis 等）。
> 令牌**不在仓库设置里**，在**个人账号设置**里，两者是两套菜单。下面是完整路径。

---

## 0. 先确认两件事

| 项目 | 你的情况 |
|---|---|
| 仓库名 | 截图里显示为 **gk**（所以命令要带 `--repo gk`） |
| 仓库是否已建 | 已建，且是**空仓库**（没有 README）——正好 |

---

## 方案 A：fine-grained token（推荐，权限最小）

### A1. 打开创建页

直接访问：**https://github.com/settings/personal-access-tokens/new**

找不到入口时的点击路径：

1. 右上角**头像** → **Settings**（设置）
2. 左侧菜单拉到**最底部** → **Developer settings**（开发者设置）
3. 左侧 **Personal access tokens** → **Fine-grained tokens**
4. 右上角 **Generate new token**

### A2. 填基本信息

| 字段 | 填什么 |
|---|---|
| **Token name** | `zujuan-upload`（随便起，只是给你自己认） |
| **Expiration** | **7 days**（上传完就作废，安全） |
| **Description** | 可留空 |
| **Resource owner** | 选你自己的账号（头像那个） |

### A3. 选仓库（最关键的一步）

**Repository access** 三个选项：

- ~~Public Repositories (read-only)~~ ❌ 只读，传不了
- ~~All repositories~~ ❌ 权限太大
- ✅ **Only select repositories** → 点 **Select repositories** → 搜索并勾选 **gk**

### A4. 选权限

展开 **Permissions** → **Repository permissions**，只需要改一项：

| 权限 | 设置 | 为什么 |
|---|---|---|
| **Contents** | **Read and write** | 建文件、改文件、提交都靠它 |
| Metadata | Read-only（自动勾上，改不了） | 读仓库基本信息 |
| 其他全部 | No access（默认） | 不要多给 |

> 注意：如果你要让它**顺便帮你新建仓库**，还得给 **Administration: Read and write**。
> 但你的 gk 已经建好了，**不需要**。

### A5. 生成并复制

1. 页面拉到底 → **Generate token**
2. 出现一串 `github_pat_xxxxxxxx...`
3. **立刻点复制图标** —— 这串字符只显示这一次，刷新页面就再也看不到了（丢了只能重新生成）

---

## 方案 B：classic token（更快，30 秒搞定）

如果方案 A 的选项太多嫌烦，用这个：

1. 打开 **https://github.com/settings/tokens/new**
2. **Note**：`zujuan-upload`
3. **Expiration**：7 days
4. **Select scopes**：只勾最上面的 **`repo`**（勾它会自动带上下面 5 个子项，正常）
5. 拉到底 → **Generate token** → 复制 `ghp_xxxxxxxx`

**区别**：classic 的 `repo` 权限覆盖你**所有**仓库，fine-grained 只覆盖 gk。传完记得撤销，实际风险差别不大。

---

## 3. 把令牌交给我

两种方式，任选其一：

### 方式一：写进文件（推荐，不会留在聊天记录里）

在 PowerShell 里执行（把 `粘贴你的令牌` 换成实际字符串）：

```powershell
Set-Content -Path "D:\文件\有趣的游戏\.gh_token" -Value "粘贴你的令牌" -NoNewline -Encoding ascii
```

- 位置在 `zujuan` 仓库**外面**，永远不会被提交
- 脚本会自动读它，你不用设环境变量

### 方式二：直接贴在对话里

我会立刻用它执行上传，然后提醒你撤销。

---

## 4. 上传命令

拿到令牌后我会跑（你也可以自己跑）：

```powershell
cd "D:\文件\有趣的游戏\zujuan"

# 先体检：验证令牌有效、仓库可访问、写权限够不够
node scripts\publish.mjs --repo gk --check

# 正式上传（36 个文件，已存在的自动跳过相同内容）
node scripts\publish.mjs --repo gk
```

成功后会打印：

```
账号：xxx（fine-grained token）
仓库可访问：https://github.com/xxx/gk（私有）
写权限：有
```

---

## 5. 上传完立刻撤销（重要）

1. 回到 **https://github.com/settings/personal-access-tokens**（classic 是 `/settings/tokens`）
2. 找到 `zujuan-upload` → 右侧 **...** → **Delete**
3. 顺手删掉本地文件：`Remove-Item "D:\文件\有趣的游戏\.gh_token"`

令牌一旦泄露，别人就能以你的身份改你所有有权限的仓库。

---

## 6. 常见报错对照

| 报错 | 原因 | 解决 |
|---|---|---|
| `401 Bad credentials` | 令牌复制不全 / 已被撤销 / 多了空格 | 重新生成，用 `--token` 或文件重新给 |
| `404 Not Found`（读仓库时） | ① 仓库名拼错 ② fine-grained 没勾这个仓库 ③ 仓库属于别人 | 检查 `--repo` 后面的名字；回 A3 重新勾选 |
| `403 Resource not accessible by personal access token` | Contents 权限给了 Read 而不是 Read and write | 回 A4 改权限（改完要重新生成令牌） |
| `403 You have exceeded a secondary rate limit` | 传太快 | 等 1 分钟重跑，脚本会跳过已上传的相同文件 |
| `422 Reference does not exist` | 空仓库还没有默认分支 | 脚本已自动处理（首传时去掉 branch 参数，由 GitHub 建首个提交），直接重跑即可 |

---

## 7. 一图流

```
头像 → Settings → Developer settings → Personal access tokens → Fine-grained tokens
  → Generate new token
     name: zujuan-upload
     expiration: 7 days
     repository access: Only select repositories → gk
     permissions: Contents = Read and write
  → Generate token → 复制 github_pat_...
  → 写入 D:\文件\有趣的游戏\.gh_token
  → 我执行 node scripts\publish.mjs --repo gk
  → 你回 GitHub 删除该令牌
```
