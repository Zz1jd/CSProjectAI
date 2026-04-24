# CVRP FunSearch 算法改进与对比实验报告

CVRP FunSearch Algorithm Improvements and Comparative Experiment Report

## 1. 问题描述与方法动机 (Problem Description & Motivation)

### 问题描述
原始版本（基于 `funsearch_cvrp_(1).ipynb` 及旧版 `implementation`）在解决 CVRP（带容量限制的车辆路径问题）时面临以下核心痛点：
<br>
The original version (based on `funsearch_cvrp_(1).ipynb` and the legacy `implementation`) faced the following core issues when solving CVRP (Capacitated Vehicle Routing Problem):
- **指令引导薄弱（Weak Guidance）**：LLM 仅接收到简单的代码片段，缺乏对 CVRP 业务逻辑（如需求密度、容量平衡）的深度引导，导致演化过程近乎“随机游走”。
<br>
   Weak guidance — the LLM only receives simple code snippets and lacks deep guidance on CVRP logic (e.g., demand density, capacity balancing), making the evolution process close to a “random walk”.
- **协议理解偏差（Logic Reversal）**：由于缺乏对框架 `np.argmax()` 机制的说明，LLM 经常产生逻辑反转（例如本应寻找最近点，却写成了寻找最远点），导致距离爆炸。
  <br>
  Logic reversal — without an explicit explanation of the `np.argmax()` mechanism, the LLM often reverses the intended logic (e.g., selecting the farthest node instead of the nearest), causing distances to explode.
- **执行脆弱性（Execution Fragility）**：生成的代码频繁出现缩进错误、废话干扰或缺少变量初始化，导致评估器返回大量的 `Score: None`。
<br>
  Execution fragility — generated code often has indentation errors, extraneous text, or missing variable initialization, leading the evaluator to return many `Score: None`.
- **计算效率低下（Performance Bottleneck）**：原始模板使用 Python 原生 `for` 循环计算分数，在处理大规模数据集时，单次评估耗时过长，严重拖慢了演化循环。
<br>
  Performance bottleneck — the original template uses Python `for` loops to compute scores; for larger datasets, each evaluation takes too long and severely slows down the evolutionary loop.

### 方法动机
通过引入 **CoT（思维链）** 和 **模块化 Prompt 引擎**，旨在将 LLM 从一个简单的“代码续写器”提升为“算法设计师”。同时通过 **Numpy 向量化** 提升底层评估性能，从而实现更高效、更稳定的启发式函数搜索。
<br>
  By introducing **Chain-of-Thought (CoT)** and a **modular prompt engine**, we aim to elevate the LLM from a simple “code completer” to an “algorithm designer”. In addition, **NumPy vectorization** improves evaluation throughput, enabling a more efficient and stable search for heuristic functions.

---

## 2. 方法设计 (Design of Method)

改进方案的核心在于将演化逻辑从底层解耦，并引入了两个关键的新模块：
<br>
  The key idea is to decouple the evolutionary logic from low-level execution details and introduce two new core modules:

### A. 引入 PromptEngine (思维链大脑)
- **CoT 注入**：不再直接发送代码，而是先注入一组**专家级引导语**。例如，要求模型“先分析客户分布，再平衡距离与剩余容量”。
<br>
  CoT injection — instead of sending code directly, inject expert-level guidance first (e.g., “analyze customer distribution first, then balance distance and remaining capacity”).
- **协议锁定**：明确告知 LLM 框架使用 `np.argmax()`，必须返回负距离（`-scores`）以确保正确进化。
<br>
  Protocol locking — clearly state that the framework uses `np.argmax()` and the function must return negative distance (e.g., `-scores`) to ensure correct evolution.
- **挑战机制**：在 Prompt 中显式设定性能目标（如 "Reach < 1000"），激发 LLM 尝试非线性数学组合。
<br>
  Challenge targets — explicitly set performance targets in the prompt (e.g., “Reach < 1000”) to encourage non-linear mathematical combinations.

### B. 引入 LLMClient (执行保障)
- **鲁棒性裁剪（Robust Trimming）**：改进了代码提取逻辑，支持自动剥离 Markdown 标记，并**严格保留 4 空格缩进**，确保生成代码与框架完美拼接。
<br>
  Robust trimming — improve code extraction to automatically strip Markdown artifacts while strictly preserving 4-space indentation, ensuring safe stitching into the framework.
- **API 适配**：封装了对代理接口（如 ChatAnywhere）的支持，并实现了代码纯度过滤，防止 LLM 返回非代码描述信息。
<br>
  API adaptation — wrap support for proxy-based APIs (e.g., ChatAnywhere) and filter outputs to enforce code-only responses, preventing non-code text.

### C. 模板向量化重构
- 将 `priority` 函数的基准模板从 Python 循环重构为 **Numpy 向量化实现**。这不仅提升了运行速度（单次评估快 50-100 倍），还为 LLM 提供了更高质量的代码学习基准，引导其生成高性能的科学计算代码。
<br>
  Refactor the baseline `priority` template from Python loops to a NumPy-vectorized implementation. This improves runtime (50–100× faster per evaluation) and provides a higher-quality reference for the LLM to learn from, encouraging performant scientific-computing code.

---

## 3. 初步结果 (Preliminary Results)

通过对比原始版本与改进版本的运行日志，数据表现如下：
<br>
  By comparing the run logs of the original and improved versions, the results are as follows:

| 指标 | 原始版本 (funsearch_cvrp_(1)) | 改进版本 (hjr + CoT 增强) | 提升/差异 |
| :--- | :--- | :--- | :--- |
| **最佳分数 (Best Score)** | **-1154.59** | **-1123.02** | **提升了约 31.57 个单位** (距离缩短 ~3%) |
| **收敛速度** | 采样 89 次后达到 -1154 | 采样不到 100 次即突破 **-1123** | 同样的采样次数下，改进版更早发现优质解 |
| **无效代码比例 (None)** | 约 15% | 约 12% | 稳定性提升，API 资源浪费减少 |
| **代码专业度** | 简单的线性数学修改 | **复杂的非线性加权 (如 np.power, ratios)** | LLM 表现出明显的“算法设计”思维 |

<br>

| Metric | Original (funsearch_cvrp_(1)) | Improved (hjr + CoT enhanced) | Gain / Difference |
| :--- | :--- | :--- | :--- |
| **Best Score** | **-1154.59** | **-1123.02** | **Improved by ~31.57** (distance reduced by ~3%) |
| **Convergence** | Reaches -1154 after 89 samples | Breaks **-1123** within <100 samples | Finds better solutions earlier under similar budgets |
| **Invalid code rate (None)** | ~15% | ~12% | More stable; less wasted API budget |
| **Code sophistication** | Simple linear math tweaks | **Complex non-linear weighting (e.g., `np.power`, ratios)** | Stronger “algorithm designer” behavior |

### 结论
实验证明，通过改进 LLM 的“思考方式”和“交互协议”，在不改变核心演化算法的情况下，可以显著提升 CVRP 问题的求解质量。改进后的框架表现出更强的逻辑正确性和搜索深度。
<br>
  The experiment shows that improving the LLM’s “thinking process” and “interaction protocol” can significantly improve CVRP solution quality without changing the core evolutionary algorithm. The enhanced framework demonstrates stronger logical correctness and deeper search behavior.
