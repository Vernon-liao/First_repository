# First_repository

桌面端 AI 跑团系统架构设计文档见：

- [docs/desktop-rpg-architecture.md](docs/desktop-rpg-architecture.md)
# Profile-driven Narrative System

该仓库实现了角色 Profile 的结构化建模、AI 生成约束校验、剧情驱动判定和章节差分日志。

## 核心能力

- 完整 Profile 结构（基础/世界观/行为/玩法/状态/关系/视觉）
- `profile_version` 版本字段（当前 `1.0.0`）用于存档兼容
- AI 生成人设提示词强制要求输出合法 JSON Schema
- 输出入库前执行 JSON 校验
- 对话、线索掉落、背叛/援助判定基于 Profile 字段计算
- `diff_log` 记录章节间角色变化（信任、污染、阵营等）

## 运行测试

```bash
pytest -q
```
# First_repository

TRPG 控制台低保真线框图位于：

- `wireframes/lofi.html`

可直接在浏览器中打开该文件查看 GM 界面、玩家界面、信息隔离层、线索板与章节回放设计。
# AI 剧情内容治理与一致性方案

本文档定义一套“AI 结果先隔离、人工可控采纳、自动状态联动、可回滚可复用”的剧情管理机制，满足以下目标：

- 避免 AI 生成内容直接污染主线剧情。
- 保持世界观与剧情状态一致。
- 让主持人/创作者可以低成本筛选、调整、回滚。
- 将高质量结果沉淀为复用素材，提升后续命中率。

---

## 1. 待采纳区（Staging）

### 设计原则
所有 AI 结果（文本、图像、NPC）**默认进入待采纳区**，不直接写入正式剧情。

### 数据结构

```ts
type AIContentType = 'text' | 'image' | 'npc';
type PendingStatus = 'pending' | 'adopted' | 'edited' | 'rerolled' | 'rejected';

interface PendingCandidate {
  id: string;
  type: AIContentType;
  sourcePrompt: string;
  payload: Record<string, unknown>; // 文本内容、图片元信息、NPC属性等
  consistencyReport?: ConsistencyReport;
  status: PendingStatus;
  createdAt: string;
  updatedAt: string;
  operationLog: CandidateOperation[];
}
```

### 流程
1. AI 返回结果。
2. 写入 `PendingCandidate`。
3. 可选：立即执行一致性检查（先给风险提示，不阻塞查看）。
4. 前端在“待采纳区”展示，等待人工操作。

---

## 2. 三类操作 + 原因标签

### 操作定义
- `采纳`（adopt）：直接接受候选结果。
- `轻改`（minor_edit）：允许局部改写（措辞修饰、轻微设定修正）。
- `重掷`（reroll）：丢弃当前候选并基于原意重生一版。

### 原因标签（可多选）
- `风格不符`
- `剧透`
- `信息冲突`

### 记录结构

```ts
type ReasonTag = 'style_mismatch' | 'spoiler' | 'conflict';
type OperationType = 'adopt' | 'minor_edit' | 'reroll';

interface CandidateOperation {
  id: string;
  candidateId: string;
  operation: OperationType;
  reasonTags: ReasonTag[];
  note?: string;
  actorId: string;
  timestamp: string;
}
```

### 行为约束
- `轻改`必须保存“原始版本 + 修改后版本 + diff”。
- `重掷`需保留与原候选的 `rerollFrom` 关联，形成可追溯链。
- 所有操作进入审计日志，支持复盘。

---

## 3. 采纳后写入 CampaignState 并触发事件

### CampaignState 建议切片

```ts
interface CampaignState {
  clues: Clue[];
  relations: RelationEdge[];
  quests: Quest[];
  npcs: NPC[];
  timeline: TimelineEvent[];
  stableSnapshots: StableSnapshot[];
}
```

### 自动事件触发
当候选被 `采纳`（或 `轻改后采纳`）时：

1. **写入状态**：将结构化内容 merge 到 `CampaignState`。
2. **触发领域事件**：
   - `ClueAdded`
   - `RelationChanged`
   - `QuestUpdated`
3. **投递事件总线**：供 UI、日志、通知系统订阅。

```ts
interface DomainEvent {
  id: string;
  type: 'ClueAdded' | 'RelationChanged' | 'QuestUpdated';
  payload: Record<string, unknown>;
  createdAt: string;
}
```

---

## 4. 一致性检查器（Consistency Checker）

### 目标
在“采纳前”识别与既有世界设定冲突，防止错误进入主状态。

### 必检规则
1. **序列错误**：时间线逆序、未来事件被提前引用。
2. **阵营矛盾**：角色阵营与历史记录互斥。
3. **已死亡角色复活**：无复活机制却重新出现。

### 报告格式

```ts
interface ConsistencyIssue {
  code: 'SEQUENCE_ERROR' | 'FACTION_CONFLICT' | 'DEAD_CHARACTER_RETURN';
  severity: 'warning' | 'error';
  message: string;
  evidenceRefs: string[]; // 指向世界设定条目或历史事件ID
}

interface ConsistencyReport {
  candidateId: string;
  pass: boolean;
  issues: ConsistencyIssue[];
  checkedAt: string;
}
```

### 策略
- `error`：默认禁止直接采纳，只允许“轻改后再检”或“重掷”。
- `warning`：允许采纳，但界面高亮风险。

---

## 5. 一键回滚到上个稳定节点

### 稳定节点定义
每次完成关键操作后生成 `StableSnapshot`：
- 章节结算
- 大事件采纳完成
- 主持人手动“标记稳定”

```ts
interface StableSnapshot {
  id: string;
  campaignStateHash: string;
  state: CampaignState;
  createdAt: string;
  reason: 'chapter_end' | 'major_adoption' | 'manual_checkpoint';
}
```

### 回滚流程
1. 用户点击“一键回滚”。
2. 系统加载最近 `StableSnapshot` 覆盖当前 `CampaignState`。
3. 生成 `RollbackPerformed` 事件。
4. 将被回滚区间内容标记为 `rolled_back`，但不删除，供后续审阅。

---

## 6. 可复用素材库（Knowledge/Asset Library）

### 目标
将“被采纳内容”沉淀为后续生成的高权重参考，提升 AI 命中率与风格稳定性。

### 入库策略
- 仅采纳内容进入素材库。
- 按类型分桶：剧情片段、角色设定、场景描述、线索模板。
- 写入标签：世界观、阵营、章节、语气风格、安全级别。

```ts
interface ReusableAsset {
  id: string;
  sourceCandidateId: string;
  assetType: 'plot' | 'character' | 'scene' | 'clue_template';
  content: Record<string, unknown>;
  tags: string[];
  qualityScore: number;
  adoptedAt: string;
}
```

### 生成时利用
- 在提示词构造阶段检索高相关素材（向量检索 + 标签过滤）。
- 优先注入高质量、近期、同章节素材。
- 若命中冲突标签（如阵营互斥），在生成前剔除。

---

## 推荐 API 草案

- `POST /ai/candidates`：创建待采纳候选。
- `POST /ai/candidates/{id}/check`：运行一致性检查。
- `POST /ai/candidates/{id}/operate`：执行采纳/轻改/重掷。
- `POST /campaign/rollback`：回滚到最近稳定节点。
- `GET /assets/reusable`：检索素材库。

---

## 最小可落地迭代（MVP）

1. 建立 `PendingCandidate` 与三类操作审计。
2. 采纳后写入 `CampaignState` + 触发三种领域事件。
3. 实现三条一致性硬规则（序列/阵营/死亡角色）。
4. 加入稳定快照与一键回滚。
5. 采纳即入库素材，并接入生成提示词检索。

以上 5 步可快速形成“可控生成闭环”。
