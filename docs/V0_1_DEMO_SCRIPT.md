# V0.1 演示脚本（10-15 分钟）

## 演示目标
- 展示从“新建战役”到“第一章结算”完整链路。
- 展示三类异常回退：模型超时、图片失败、存档中断。
- 展示可验收输出：功能状态、结构化日志、性能指标、演示存档。

## 时间分配建议
1. **0:00-1:30（1.5 分钟）**：背景与目标
2. **1:30-5:30（4 分钟）**：正常流程 E2E 演示
3. **5:30-10:30（5 分钟）**：异常场景演练（三连）
4. **10:30-12:30（2 分钟）**：验收清单核对
5. **12:30-15:00（2.5 分钟）**：演示存档复用 + Q&A

## 演示前准备
- 打开 `tests/test_release_readiness.py`，说明覆盖场景。
- 准备演示存档：`data/demo_campaign_save_v0_1.json`。
- 终端待执行：`pytest -q`。

## 详细讲解台词（可直接照读）

### 第 1 段：背景（0:00-1:30）
“本次 V0.1 目标不是 UI 打磨，而是验证主干链路稳定性：从创建战役开始，能完成第一章；遇到模型、图片、存档异常时，系统必须有可验证回退；并且输出可验收的日志与性能指标。”

### 第 2 段：正常 E2E（1:30-5:30）
1. 展示 `test_e2e_from_new_campaign_to_chapter_1_settlement`。
2. 说明事件序列：`CAMPAIGN_CREATED -> CHAPTER_1_STARTED -> ... -> CHAPTER_1_SETTLED`。
3. 强调 `fallback_summary` 在正常场景全为 `False`。
4. 强调结算完成且生成 checkpoint，具备后续追溯能力。

### 第 3 段：异常演练（5:30-10:30）
1. 展示 `test_failure_drills_timeout_image_fail_and_save_interruption_have_fallbacks`。
2. 逐个解释：
   - `narrative_mode="timeout"` -> 文本回退模板。
   - `image_mode="failure"` -> 占位图回退。
   - `save_mode="interrupted"` -> 回滚到稳定节点并恢复结算。
3. 展示 `ROLLBACK_PERFORMED` 事件，证明回退不是静默处理。

### 第 4 段：验收清单（10:30-12:30）
1. 打开 `docs/V0_1_ACCEPTANCE_CHECKLIST.md`。
2. 逐项勾选功能验收、日志验收、性能验收。
3. 说明 V0.1 的性能口径为“先可观测，再优化”。

### 第 5 段：演示存档固化（12:30-15:00）
1. 打开 `data/demo_campaign_save_v0_1.json`。
2. 指出其用途：
   - 预置演示数据；
   - 回归测试复现基线；
   - 供后续 UI 联调直接读取。
3. 结尾：V0.1 已满足“可走通、可回退、可验收、可复现”。

## 演示完成判定
- `pytest -q` 通过。
- 演示存档存在且结算态正确。
- 验收清单内容完整。
