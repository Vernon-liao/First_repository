# V0.1 验收清单

## 1) 功能验收
- [x] 从新建战役启动到第一章结算的端到端流程可运行。
- [x] 第一章流程包含：开局建档、章节行动、章节结算。
- [x] 异常演练：模型超时时触发文本保底回退。
- [x] 异常演练：图片生成失败时触发占位图回退。
- [x] 异常演练：存档中断时触发最近稳定点回滚并完成恢复结算。

## 2) 日志验收
- [x] 每个关键步骤均有结构化日志（step/source/fallback_used/latency/detail）。
- [x] 回退场景记录具体回退原因：
  - `narrative_timeout_fallback_template`
  - `image_placeholder_uri`
  - `save_interrupted_rollback_to_last_checkpoint`
- [x] 回滚行为形成可追踪事件：`ROLLBACK_PERFORMED`。

## 3) 性能验收（V0.1 基线）
- [x] 首屏时间指标存在：`first_screen_ms`。
- [x] 单步响应指标存在：`single_step_response_ms`。
- [x] 指标可随每次联调输出，作为后续优化基线。

> 备注：当前仓库为逻辑模拟与流程验证形态，V0.1 重点是“可联调、可回退、可验收”，下一阶段再接入真实模型与桌面端容器。
