# GitHub 优惠码自动同步仓库部署与接入指南

本目录（`github-repo-files/`）包含了用于部署在 GitHub 上的全部文件。部署完成后，你的网站将在更新优惠券时自动通知该仓库刷新并生成最新的多语言 README。

---

## 步骤 1：在 GitHub 创建新仓库

1. 登录你的 GitHub 账号，点击右上角的 **「+」** -> **「New repository」**。
2. 填写仓库信息：
   - **Repository name**: 例如 `netcup-coupons` 或 `netcup-gutschein`（使用这类关键词有助于 Google SEO 排名）。
   - **Description**: 例如 `⚡ Verified Netcup Coupons & Voucher Codes. Automated real-time verification.`
   - **Public / Private**: 必须选择 **Public（公开）**，只有公开仓库才能被搜索引擎收录并吸引流量。
   - 不要勾选 "Add a README file"（我们将使用此目录下的文件初始化）。
3. 点击 **「Create repository」**。

---

## 步骤 2：将本目录文件上传到你的 GitHub 仓库

你可以通过以下两种方式之一上传：

### 方式 A：使用 Git 命令行（推荐）

在终端中打开当前 `github-repo-files` 目录并运行以下命令（将 `<你的GitHub用户名>` 替换为真实用户名）：

```bash
cd github-repo-files
git init
git branch -M main
git add .
git commit -m "feat: initial commit for netcup coupons auto sync"
git remote add origin https://github.com/<你的GitHub用户名>/netcup-coupons.git
git push -u origin main
```

### 方式 B：通过 GitHub 网页直接上传

1. 在刚刚创建的空仓库页面中，点击 **"uploading an existing file"**。
2. 将 `github-repo-files` 目录下的：
   - `sync.py`
   - `.github/workflows/sync.yml`（注意包含 `.github` 目录层级）
3. 提交（Commit changes）到 `main` 分支。

---

## 步骤 3：在 GitHub 仓库设置权限（关键）

GitHub Actions 默认可能没有推送权限，需检查确保开启写权限：

1. 进入该仓库的 **Settings** -> 左侧菜单选择 **Actions** -> **General**。
2. 页面向下滚动到 **Workflow permissions**：
3. 选择 **「Read and write permissions」**（读写权限）。
4. 勾选 **「Allow GitHub Actions to create and approve pull requests」**。
5. 点击 **Save** 保存。

---

## 步骤 4：生成 GitHub Personal Access Token (PAT)

这是让你的网站服务器能够向 GitHub 发送触发信号（Dispatch）的凭据：

1. 登录 GitHub，点击右上角头像 -> **Settings**。
2. 在左侧菜单最底部，点击 **Developer settings**。
3. 选择 **Personal access tokens** -> **Tokens (classic)**。
4. 点击右上角 **Generate new token** -> **Generate new token (classic)**。
5. 填写：
   - **Note**: `netcup.free sync`
   - **Expiration**: 推荐 `No expiration`（永不过期）
   - **Select scopes**: 勾选 **`repo`**（完整仓库控制权限）
6. 点击页面底部的绿色按钮 **Generate token**。
7. **复制生成的以 `ghp_` 开头的 Token 字符串**（离开页面后将无法再次查看）。

---

## 步骤 5：在网站服务器 `.env` 中配置

在你的网站项目根目录的 `.env` 文件中，添加以下三行：

```env
# GitHub 自动同步配置
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_OWNER=你的GitHub用户名或组织名
GITHUB_REPO=netcup-coupons
```

保存后，重启你的网站应用即可生效。

---

## 步骤 6：测试与验证

### 验证 1：在网站管理后台一键触发
1. 打开你的网站管理后台 `/admin`。
2. 切换到 **「📊 爬虫监控」** 标签页。
3. 找到 **「🐙 GitHub 优惠码仓库自动联动」** 区域。
4. 点击 **「🚀 立即同步至 GitHub 仓库」** 按钮。
5. 提示成功后，打开你的 GitHub 仓库的 **Actions** 页面，即可看到正在运行的 `Sync Netcup Vouchers` 工作流，运行完成后仓库首页的 `README.md`、`README_ZH.md`、`README_DE.md` 将自动生成并上架最新的优惠券！

### 验证 2：爬虫更新自动联动
每当 `netcup-api` 机器人调用网站的 `POST /api/wp-json/pages` 提交新优惠码时，网站将在后台无感异步触发该流水线，实现秒级自动同步！
