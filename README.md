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
