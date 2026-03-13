# 桌面端 AI 跑团系统技术架构说明

## 1. 四层架构设计

```text
┌────────────────────────────────────────────────────────────┐
│ Presentation（桌面 UI: Electron/Tauri + 前端框架）         │
├────────────────────────────────────────────────────────────┤
│ Orchestration（剧情导演、状态机、规则判定、事件编排）       │
├────────────────────────────────────────────────────────────┤
│ Generation Services（文本/图片/NPC 生成与模型适配）         │
├────────────────────────────────────────────────────────────┤
│ Persistence（战役档、场次档、记忆、素材缓存）               │
└────────────────────────────────────────────────────────────┘
```

### 1.1 Presentation（桌面 UI）
- 职责：
  - 显示地图、角色面板、对话日志、判定结果。
  - 提供“行动输入 -> 请求编排层 -> 渲染事件结果”的交互闭环。
  - 只处理 UI 状态（如当前选中角色、面板开关），不承载业务规则。
- 建议：
  - Tauri + React/Vue（更轻、更安全）或 Electron + React（生态丰富）。
  - 前端通过统一 `AppCommand` 调用 Orchestration API。

### 1.2 Orchestration（核心编排层）
- 职责：
  - 维护剧情状态机（场景流转、阶段推进）。
  - 执行规则判定（技能检定、战斗结算、线索触发条件）。
  - 调用 Generation Services（文本、图片、NPC）。
  - 发布统一事件到 `GameEventBus`，驱动 UI 和持久化更新。
- 关键模块：
  - `DirectorEngine`：剧情导演，负责叙事推进策略。
  - `RuleEngine`：检定与规则判定。
  - `CampaignCoordinator`：战役级数据装载、切场、收束。

### 1.3 Generation Services（生成服务层）
- 职责：
  - 屏蔽模型差异，对上提供稳定接口。
  - 管理 Prompt 模板、上下文裁剪、重试与降级。
- 组成：
  - `NarrativeService`：剧情文本、旁白、分支建议。
  - `CharacterService`：NPC 生成（背景、人格、动机、关系）。
  - `ImageService`：场景图、角色立绘、道具图。

### 1.4 Persistence（持久化层）
- 职责：
  - 存储战役档、场次档、事件日志、缓存素材。
  - 提供事务一致性（关键状态+事件同写）。
- 建议存储：
  - SQLite（结构化数据）+ 本地对象存储目录（图片、音频等）。

---

## 2. 核心服务接口定义

> 以下以 TypeScript 风格展示接口契约，可映射到 Rust/Kotlin/C# 等实现。

```ts
export interface NarrativeService {
  generateSceneNarration(input: {
    campaignId: string;
    sessionId: string;
    contextWindow: string;
    playerActions: string[];
  }): Promise<{ text: string; tokens?: number; source: "model" | "fallback" }>;

  suggestBranches(input: {
    sceneId: string;
    currentState: Record<string, unknown>;
  }): Promise<Array<{ id: string; description: string }>>;
}

export interface CharacterService {
  generateNpc(input: {
    campaignTheme: string;
    roleHint?: string;
    relationHints?: string[];
  }): Promise<{
    npcId: string;
    name: string;
    profile: string;
    traits: string[];
    motivations: string[];
  }>;

  evolveNpcState(input: {
    npcId: string;
    events: GameEvent[];
  }): Promise<{ npcId: string; updatedFields: Record<string, unknown> }>;
}

export interface ImageService {
  generateSceneImage(input: {
    prompt: string;
    style?: string;
    seed?: number;
  }): Promise<{ uri: string; source: "model" | "placeholder" }>;

  generateCharacterPortrait(input: {
    npcId: string;
    visualPrompt: string;
  }): Promise<{ uri: string; source: "model" | "placeholder" }>;
}

export interface CampaignStateService {
  loadCampaign(campaignId: string): Promise<CampaignSnapshot>;
  saveCampaign(snapshot: CampaignSnapshot): Promise<void>;

  loadSession(campaignId: string, sessionId: string): Promise<SessionSnapshot>;
  saveSession(snapshot: SessionSnapshot): Promise<void>;

  appendEvents(campaignId: string, sessionId: string, events: GameEvent[]): Promise<void>;
}
```

---

## 3. 统一事件总线设计（`GameEvent`）

### 3.1 事件模型

```ts
export type GameEventType =
  | "SCENE_SWITCHED"
  | "ROLL_RESOLVED"
  | "CHARACTER_STATUS_CHANGED"
  | "CLUE_UNLOCKED";

export interface GameEvent {
  eventId: string;
  type: GameEventType;
  campaignId: string;
  sessionId: string;
  occurredAt: string; // ISO time
  actorId?: string;
  payload: Record<string, unknown>;
}
```

### 3.2 事件流约束
- 所有可观察业务变化必须产出 `GameEvent`。
- UI 不直接读写底层状态，只订阅事件和查询快照。
- 持久化层落盘事件日志，支持回放与调试。

### 3.3 典型事件
- `SCENE_SWITCHED`：进入新场景（payload 含 sceneId、entryReason）。
- `ROLL_RESOLVED`：检定结果（payload 含 dice、dc、outcome）。
- `CHARACTER_STATUS_CHANGED`：角色状态变化（payload 含 hp/sanity/buff）。
- `CLUE_UNLOCKED`：线索解锁（payload 含 clueId、visibilityScope）。

---

## 4. AI 调用异步化与失败回退

### 4.1 异步任务封装
- 采用 `TaskRunner` 封装所有模型请求：
  - 超时控制（如文本 8s，图片 20s）。
  - 重试策略（指数退避，最多 2~3 次）。
  - 熔断与限流（避免模型抖动拖垮主流程）。

### 4.2 回退策略
- 文本生成超时/失败：返回模板叙述（含保底剧情推进句）。
- 图片生成超时/失败：返回本地占位图 URI。
- NPC 生成失败：回退到规则模板随机生成。

```ts
async function safeNarrationCall(input: NarrationInput): Promise<{ text: string; source: "model" | "fallback" }> {
  try {
    return await withTimeout(() => narrativeService.generateSceneNarration(input), 8000);
  } catch {
    return {
      text: "你们踏入昏暗长廊，空气中弥漫着不安；远处传来金属摩擦声。",
      source: "fallback",
    };
  }
}
```

---

## 5. 本地存档：战役档 + 场次档双层存储

### 5.1 战役档（Campaign Save）
- 粒度：长期、跨场次。
- 内容：
  - 世界设定、主线进度、NPC 长期关系图。
  - 玩家角色成长（等级、装备、声望）。
  - 已解锁全局线索与分支历史。

### 5.2 场次档（Session Save）
- 粒度：单次游玩局。
- 内容：
  - 当前场景、临时状态（HP、BUFF、即时资源）。
  - 本局事件序列与即时判定结果。
  - 场景内临时生成素材引用。

### 5.3 读写策略
- 开局：加载战役档 -> 创建/恢复场次档。
- 进行中：关键动作写入场次档 + 事件日志。
- 结算：将场次关键结果汇总回战役档（关系变化、长期后果）。

---

## 6. 桌面端技术选型建议

## 6.1 客户端框架
- **首选：Tauri + React/Vue**
  - 优点：包体小、内存占用低、Rust 后端能力强。
  - 适合：本地 AI 工具链、对性能和分发体积敏感。
- **备选：Electron + React**
  - 优点：生态成熟、前端团队上手快。
  - 适合：快速验证、依赖大量 Node 生态库。

## 6.2 本地数据库与缓存
- **SQLite**：
  - 存储战役/场次元数据、角色状态、事件索引。
- **本地文件系统对象缓存**：
  - 存储图片、语音、日志分片（按 `campaignId/sessionId` 分目录）。
- **可选扩展**：
  - 使用 `sqlite + FTS5` 做剧情日志全文检索。

## 6.3 模型服务适配层（Model Adapter）
- 统一适配 OpenAI / 本地模型（Ollama, vLLM 等）：
  - `TextModelAdapter`
  - `ImageModelAdapter`
- 适配层负责：
  - 参数标准化（temperature、top_p、seed）。
  - 供应商差异屏蔽（API key、endpoint、响应格式）。
  - 成本与延迟观测（埋点到 telemetry）。

## 6.4 推荐最小可行技术栈（MVP）
- UI：Tauri + React + Zustand
- Orchestration：Rust（Tauri command）或 Node/TypeScript service
- Persistence：SQLite + 本地 `assets/` 缓存目录
- AI：Model Adapter（OpenAI API + 本地模型二选一）
- Observability：结构化日志 + 事件回放工具

---

## 7. 交付建议（迭代顺序）
1. 先打通事件流骨架（`GameEventBus + CampaignStateService`）。
2. 再接入 `NarrativeService`（文本最先可见价值）。
3. 接入 `CharacterService`，建立 NPC 生命周期。
4. 最后接 `ImageService` 与缓存优化。
5. 补充回放、导出、异常恢复能力。
