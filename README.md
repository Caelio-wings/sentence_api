# 📖 轻量句子 API · 多分类一言风格服务

一个轻量、个人使用的句子服务，类似 [hitokoto](https://hitokoto.cn)（一言）。  
支持多分类、随机获取、网页管理、导入导出，并可通过 systemd 实现开机自启。

## ✨ 特性

- 🗄️ **轻量后端**：FastAPI + SQLite，单文件部署，资源占用极小
- 🏷️ **多分类支持**：一句话可属于多个分类（如“励志”、“古风”）
- 🖥️ **网页管理界面**：美观的卡片式 UI，支持句子增删改查、分类管理、导入导出
- 🔌 **API 接口**：符合 RESTful 风格，支持按分类随机获取句子
- 📂 **数据导入/导出**：JSON 格式，便于迁移、备份
- 🐧 **Linux 服务**：提供 systemd 配置，实现开机自启和进程守护

## 🛠️ 技术栈

| 角色       | 技术                                 |
| ---------- | ------------------------------------ |
| 后端框架   | FastAPI                              |
| 数据库     | SQLite3                              |
| 前端       | 原生 HTML / CSS / JavaScript         |
| 部署       | Uvicorn + systemd（Linux）           |

## 📦 安装与运行

### 1. 克隆或下载项目

将项目文件（`main.py`, `database.py`, `static/` 目录）放置在一个文件夹中，例如 `/home/yourname/sentence_api`。

### 2. 安装 Python 依赖

```bash
pip install fastapi uvicorn
````

（可选）使用虚拟环境：

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
pip install fastapi uvicorn
```

### 3. 启动服务

#### 开发模式（带自动重载）

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 生产模式（后台运行）

```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
```

#### 使用提供的 Linux 脚本

```bash
chmod +x sentence_api.sh
./sentence_api.sh start   # 启动
./sentence_api.sh stop    # 停止
./sentence_api.sh restart # 重启
./sentence_api.sh status  # 状态
```

### 4. 访问 Web 管理界面

浏览器打开 `http://你的服务器IP:8000` 即可使用。

## 🚀 部署为 systemd 服务（推荐）

### 创建服务文件

```bash
sudo nano /etc/systemd/system/sentence-api.service
```

填入以下内容（请根据实际路径和用户修改）：

```ini
[Unit]
Description=Sentence API Service
After=network.target

[Service]
Type=simple
User=你的用户名
WorkingDirectory=/home/你的用户名/sentence_api
ExecStart=/home/你的用户名/sentence_api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 启动并设置开机自启

```bash
sudo systemctl daemon-reload
sudo systemctl start sentence-api
sudo systemctl enable sentence-api
sudo systemctl status sentence-api
```

### 查看日志

```bash
sudo journalctl -u sentence-api -f
```

## 📚 API 文档

服务启动后，FastAPI 自动生成交互式文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 主要接口

#### 1. 随机获取句子

```text
GET /api/random
```

**参数**（可选）：

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| category | string | 分类名，例如 `category=励志` |

**示例响应**：

```json
{
  "id": 42,
  "hitokoto": "生活不止眼前的苟且",
  "author": "高晓松",
  "categories": ["励志", "经典"],
  "commit_from": "web",
  "created_at": 1744567890,
  "length": 10
}
```

#### 2. 获取句子列表（分页）

```text
GET /api/sentences?page=1&limit=20
```

#### 3. 添加句子

```text
POST /api/sentences
```

**请求体**：

```json
{
  "hitokoto": "句子内容",
  "author": "作者",
  "categories": ["分类1", "分类2"],
  "commit_from": "web"
}
```

#### 4. 更新句子

```text
PUT /api/sentences/{id}
```

请求体同添加。

#### 5. 删除句子

```text
DELETE /api/sentences/{id}
```

#### 6. 获取所有分类

```text
GET /api/categories
```

#### 7. 新增分类

```text
POST /api/categories?name=分类名
```

#### 8. 删除分类

```text
DELETE /api/categories/{name}
```

#### 9. 批量导入（JSON 文件）

```text
POST /api/import
```

- 表单参数 `file`: JSON 数组文件
- 表单参数 `replace`: `true` 或 `false`（是否清空现有数据）

#### 10. 导出所有句子

```text
GET /api/export
```

返回 JSON 文件下载。

## 📂 数据格式

### 导入/导出的 JSON 数组示例

```json
[
  {
    "hitokoto": "你是我记忆里偶尔会去拜访的一座墓园",
    "author": "佚名",
    "categories": ["散文", "伤感"],
    "commit_from": "import_script",
    "created_at": 1744567890,
    "length": 20
  }
]
```

- `created_at` 和 `length` 可选，导入时会自动补全
- 若未提供 `categories`，将自动归为“默认分类”

## 🎨 前端管理界面功能

- ✅ 添加/编辑句子（支持多选分类）
- 🏷️ 管理分类（新增、删除）
- 📋 分页展示句子列表
- ✏️ 编辑、删除操作
- 📤 导入 JSON 文件（追加或替换模式）
- 📥 导出全部句子为 JSON

## 🛡️ 安全提醒

- 本服务默认**无任何鉴权**，适合个人内网使用或本地运行。
- 如需对外暴露，建议在前面加一层反向代理（如 Nginx）并配置 Basic Auth 或 API Key。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 或 Pull Request。

---

**Enjoy!** 🎉

```text

```