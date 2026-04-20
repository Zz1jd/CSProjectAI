## 两阶段 RAG 迭代超越 Baseline（2026-04-17）

目标：在单 seed 场景下，自动迭代 RAG 参数组合，先用 20 次预算做门槛筛选，若通过再用 100 次复评；每阶段均要求相对提升 ≥ 10%；最多尝试 10 轮。

---

### 一句话概览

不修改 implementation/（框架实现层）；把实验配置、搜索空间与两阶段编排放在仓库外层（scripts/、results/ 或新建 experiments/ 目录），并实现可重复的“20 次快速门槛 → 通过则 100 次复评”自动化流程。

### 决策要点（已对齐）
- 评测模式：单 seed 配对（固定 seed = 42）
- 阶段预算：初筛 stage1 = 20，复评 stage2 = 100
- 显著进步判定：相对提升（RAG vs Baseline）≥ 10%，同时满足现有 acceptance 的质量 guard（valid eval ratio、completion）
- baseline 策略：baseline 只跑一次并复用（为 speed 优先）
- 最大尝试轮数：max_attempts = 10
- 搜索范围：检索 + 切片（corpus_roots, retrieval_mode, top_k, score_threshold, max_context_chars, use_intent_query, chunk_size, chunk_overlap）
- 约束：严禁把实验特定配置直接写入 implementation/，应通过外层适配/包装调用框架 API

### 步骤（按优先级）
1. 外置实验配置（必做）
   - 在 scripts/ 下新增实验配置模块（例如 scripts/experiments/rag_iteration_config.py 或 JSON/YAML），定义：seed=42、stage1_budget=20、stage2_budget=100、relative_gain_threshold_pct=10.0、max_attempts=10 以及候选参数空间（检索+切片）。

2. 扩展接受判定（并保留兼容性）
   - 在 scripts/compare_rag.py 中：扩展 evaluate_acceptance 输出，新增 relative_gain_pct 与 relative_gain_guard（基于 baseline.best 的相对增益），并把该字段写入 Pair 报告与 CLI 汇总。保持现有 policy/guard 检查不变。

3. 抽取脚本复用层（DRY）
   - 把 run_compare_once.py 中的“运行 + tee 写日志 + 解析 + 生成报告”通用部分封成 scripts/_runner.py，供一次对比和自动迭代脚本复用，避免重复实现。

4. 新增自动迭代编排脚本（核心）
   - 在 scripts/ 下新增 run_rag_iteration.py：实现流程
     - 预先只跑一次 baseline@stage1 (20) 和 baseline@stage2 (100)，保存 baseline logs
     - 对候选参数集逐轮执行：每轮对某个候选配置执行 RAG@20
     - 解析 compare 报告：若 accepted 且 relative_gain_pct >= 10.0，则执行 RAG@100；若 RAG@100 通过相同门槛则成功并停止
     - 若未通过，继续下一个候选，直到 max_attempts 或候选耗尽
     - 输出每轮 attempt 的 JSON 汇总和最终 Markdown 报告到 results/experiments/<timestamp>/

5. 定义参数空间（外置）
   - 在 scripts/experiments/space.py 中以确定性顺序列举至多 max_attempts 个候选组合，避免随机性决定搜索顺序

6. 运行可观测性与错误处理
   - 在迭代脚本中打印进度（当前 attempt、参数、stage1/stage2 状态、当前最佳 delta、累计耗时估计）并捕获异常写入 results/

7. 测试与验证
   - 更新/新增单测：tests/test_compare_logs.py（相对提升字段），新增 tests/test_rag_iteration.py（用 mocks 验证 gate 行为、baseline_once、max_attempts 停止条件）
   - 先用 mock dry-run 验证流程，再用真实一次运行检查 results/ 产物

8. 文档
   - 更新 README.md 或在 docs/ 添加说明，明确“实验放外层、不改 implementation/” 的约束和两阶段运行方法

### 验证清单
1. 单元测试通过：python -m unittest tests/test_compare_logs.py tests/test_rag_iteration.py
2. Mock dry-run：python scripts/run_rag_iteration.py --dry-run（或配置文件开启 dry-run）
3. 真实 run：python scripts/run_rag_iteration.py → 检查 results/experiments/<ts>/ 下的 per-attempt JSON 与最终 Markdown

### 产物示例（路径）
- scripts/experiments/rag_iteration_config.py — 实验配置/候选空间（外置）
- scripts/_runner.py — 运行与日志/tee 公共函数
- scripts/run_rag_iteration.py — 迭代编排脚本（主入口）
- results/experiments/<timestamp>/attempt_01.json — 每轮详情
- results/experiments/<timestamp>/final_report.md — 最终汇总

### 风险与建议
- 若 10% 门槛一直未命中，建议将 gate 分级（例如 gate=5%、final=10%）或扩大参数空间；这应由实验层配置控制，而非框架改动。
- 推荐对 dataset.py 做 os.listdir() 排序以提升跨运行可重复性（非必需，但建议作为下步优化）。

---

计划已按“外置实验层”规则撰写。要我接下来在 scripts/ 下直接创建上述模板文件并实现 run_rag_iteration.py 吗？
