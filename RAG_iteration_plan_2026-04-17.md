## 两阶段 RAG 迭代超越 Baseline（2026-04-17）

目标：在单 seed 场景下，自动迭代 RAG 参数组合，先用 20 次预算做门槛筛选，若通过再用 100 次复评；每阶段均要求相对提升 ≥ 10%；最多尝试 10 轮。

状态（2026-04-21）：核心两阶段流程、相对增益守卫、脚本复用层、候选空间与单测已经落地；当前已重新收口为“实验行为继续保留，但仍完全不改 implementation/ 源文件”的口径。

---

### 一句话概览

两阶段编排完全保持在仓库外层（scripts/、results/）；生成器 thinking 模式与 `max_context_chars = 0` 的“不限注入长度”语义通过脚本层运行时 patch 实现，不再要求修改 implementation/。

### 决策要点（已对齐）
- 评测模式：单 seed 配对（固定 seed = 42）
- 阶段预算：初筛 stage1 = 20，复评 stage2 = 100
- 显著进步判定：相对提升（RAG vs Baseline）≥ 10%，同时满足现有 acceptance 的质量 guard（valid eval ratio、completion）
- baseline 策略：baseline 只跑一次并复用（为 speed 优先）
- 最大尝试轮数：max_attempts = 10
- 搜索范围（当前实现）：query strategy + density/chunking（use_intent_query, top_k, score_threshold, chunk_size, chunk_overlap），其中 `top_k` 搜索值固定为 `3 / 5 / 10`
- 固定参数（当前实现）：开启生成器 thinking/推理模式、使用 `v3.3.0_official_full`、使用 `hybrid` 检索（含内置 `_hybrid_rerank` 重排序）、不显式设置 `max_tokens`、`max_context_chars = 0` 由脚本层解释为不裁剪检索注入内容
- 约束（已恢复）：实验编排与实验特定行为都必须留在外层；如需扩展生成调用或检索注入语义，优先通过 scripts 层 wrapper / runtime patch 实现，而不是改 implementation/
- `source_variant_versions` 已默认置空；默认两阶段搜索只保留 query alignment 与 density/chunk refinement，不再进入 source-variant phase

### 步骤（按优先级）
1. [已完成] 外置实验配置
   - 在 scripts/ 下新增实验配置模块（例如 scripts/experiments/rag_iteration_config.py 或 JSON/YAML），定义：seed=42、stage1_budget=20、stage2_budget=100、relative_gain_threshold_pct=10.0、max_attempts=10 以及候选参数空间（检索+切片）。所有实验特定参数都停留在外层。

2. [已完成] 扩展接受判定（并保留兼容性）
   - 在 scripts/compare_rag.py 中：扩展 evaluate_acceptance 输出，新增 relative_gain_pct 与 relative_gain_guard（基于 baseline.best 的相对增益），并把该字段写入 Pair 报告与 CLI 汇总。保持现有 policy/guard 检查不变。

3. [已完成] 抽取脚本复用层（DRY）
   - 把 run_compare_once.py 中的“运行 + tee 写日志 + 解析 + 生成报告”通用部分封成 scripts/_runner.py，供一次对比和自动迭代脚本复用，避免重复实现。

4. [已完成] 新增自动迭代编排脚本（核心）
   - 在 scripts/ 下新增 run_rag_iteration.py：实现流程
     - 预先只跑一次 baseline@stage1 (20) 和 baseline@stage2 (100)，保存 baseline logs
     - 对候选参数集逐轮执行：每轮对某个候选配置执行 RAG@20
     - 解析 compare 报告：若 accepted 且 relative_gain_pct >= 10.0，则执行 RAG@100；若 RAG@100 通过相同门槛则成功并停止
     - 若未通过，继续下一个候选，直到 max_attempts 或候选耗尽
     - 输出每轮 attempt 的 JSON 汇总和最终 Markdown 报告到 results/experiments/<timestamp>/

5. [已完成] 定义参数空间（外置）
   - 已在 scripts/experiments/space.py 中以确定性顺序列举候选。
   - 当前已固定 `retrieval_mode=hybrid`、`max_context_chars=0`、`control_corpus_version=v3.3.0_official_full`。
   - 当前 `top_k` 搜索空间为 `3 / 5 / 10`；query phase 固定 `top_k=3`，density phase 再比较 `3 / 5 / 10` 与 chunk granularity。
   - `source_variant_versions` 默认置空；如需做版本对比，只能显式配置为手动 ablation，而不是默认搜索流程的一部分。

6. [已完成] 运行可观测性与错误处理
   - 在迭代脚本中打印进度（当前 attempt、参数、stage1/stage2 状态、当前最佳 delta、累计耗时估计）并捕获异常写入 results/

7. [已完成，清单需改写] 测试与验证
   - 更新/新增单测：tests/test_compare_logs.py（相对提升字段），新增 tests/test_rag_iteration.py（用 mocks 验证 gate 行为、baseline_once、max_attempts 停止条件）
   - 当前已执行 `python -m pytest tests/`，79 个测试通过
   - 当前未实现 `--dry-run`，因此验证清单不应再要求 dry-run

8. [已完成] 文档同步
   - 更新 README.md 与相关说明，改成当前真实口径：
       - implementation/ 保持不变；thinking 与 zero-context 语义由 scripts 层 runtime patch 提供
     - `hybrid` 模式包含内置 `_hybrid_rerank` 重排序
       - `max_context_chars = 0` 在该编排脚本中表示不限制检索注入长度
   - source-variant phase 已从默认两阶段流程中移除

### 验证清单
1. 单元测试通过：`python -m pytest tests/`
2. 真实 run：`python scripts/run_rag_iteration.py` → 检查 `results/experiments/<ts>/` 下的 per-attempt JSON 与最终 Markdown
3. 若显式启用 source-variant ablation：补跑 `tests/test_rag_iteration.py` 并同步更新 README 中的两阶段搜索说明

### 产物示例（路径）
- scripts/experiments/rag_iteration_config.py — 实验配置/候选空间（外置）
- scripts/_runner.py — 运行与日志/tee 公共函数
- scripts/run_rag_iteration.py — 迭代编排脚本（主入口）
- results/experiments/<timestamp>/attempt_01.json — 每轮详情
- results/experiments/<timestamp>/final_report.md — 最终汇总

### 风险与建议
- 若 10% 门槛一直未命中，建议将 gate 分级（例如 gate=5%、final=10%）或扩大参数空间；这应由实验层配置控制，而非框架改动。
- 推荐对 dataset.py 做 os.listdir() 排序以提升跨运行可重复性（非必需，但建议作为下步优化）。
- 后续若要恢复 source-variant 比较，建议单独作为手动 ablation 配置，而不是重新混入默认两阶段搜索流程。

---

计划已按“外置实验层”规则撰写。要我接下来在 scripts/ 下直接创建上述模板文件并实现 run_rag_iteration.py 吗？
