# First_repository

本次已按桌面端最小可运行目标完成技术选型与骨架：

- **Tauri + React + SQLite**
- `app/`：React 前端与 Tauri 配置
- `backend/`：编排服务、状态服务、结构化日志
- `data/`：SQLite 本地存档目录（运行后生成 `campaign_state.db`）

## 最小功能已落地

1. **最小命令链路**
   - UI 按钮 -> `POST /api/orchestration/narrative` -> 返回 mock 叙事文本 -> UI 渲染。
2. **CampaignStateService 最小读写**
   - 创建战役：`POST /api/campaigns`
   - 读取战役：`GET /api/campaigns/{campaign_id}`
   - 写入一次事件：`POST /api/campaigns/{campaign_id}/events`
3. **结构化日志**
   - 日志字段包含：`eventId`, `sessionId`, `module`, `durationMs`。
4. **启动健康检查页**
   - 前端“刷新健康检查”按钮读取 `/api/health`，显示模型可用性和数据库可用性。

## 启动方式

### 1) 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2) 启动前端

```bash
cd app
npm install
npm run dev
```

访问 `http://127.0.0.1:5173`。

## 现有仓库其它内容

- 架构文档：`docs/desktop-rpg-architecture.md`
- 低保真线框图：`wireframes/lofi.html`
