

### 1. 运筹学与组合优化经典算法库（基础理论与伪代码）
这是 LLM 理解 CVRP 求解范式的基础。FunSearch 在生成启发式函数时，需要知道前人已经探索出了哪些有效的路径构建和改进策略。

+ **经典构造启发式（Construction Heuristics）：** Clarke-Wright 节约算法（Savings Algorithm）、最近邻启发式（Nearest Neighbor）、扫描算法（Sweep Algorithm）、插入启发式（Cheapest Insertion）的原理和伪代码。
+ **局部搜索与元启发式（Local/Meta-Heuristics）：** 禁忌搜索（Tabu Search）、模拟退火（Simulated Annealing）、自适应大邻域搜索（ALNS）的核心逻辑。
+ **语料形式：** 顶级运筹学期刊（如 EJOR, Computers & Operations Research, Transportation Science）中与 VRP 相关论文的可追溯章节级节点。每篇入选论文至少包含 `Abstract`、`Introduction`、`Methodology`、`Experiments`、`Results` 五类核心内容；其中 `Methodology` 在表达足够清晰时，可进一步补充算法流程图的文本描述与标准化伪代码。该类期刊语料仅作为类别 1 的基础理论补充，不向后续算子原子层扩散。

### 2. 高质量开源求解器源码库（工程级代码片段）
FunSearch 的输出是可执行的代码（通常是 Python）。为了让生成的代码具有高效率和正确的语法结构，需要检索工业级和顶尖学术级的开源实现。

+ **顶级求解器项目：** * **Google OR-Tools:** 检索其 Routing API 中的底层 C++ 启发式逻辑和 Python 封装库。
    - **PyVRP:** 这是一个目前在 CVRP 领域非常先进的开源 Python 库，基于 HGS（Hybrid Genetic Search），它的算子实现极具参考价值。
    - **LKH-3:** 解决 VRP 的最强局部搜索求解器之一，虽然是 C 语言，但可以提取其 K-opt 算子的逻辑描述代码。
+ **语料形式：** 经过清洗的函数级别代码片段（Snippet）、类定义、以及带有详细 Docstring 的注释代码。建立“代码-功能描述”的映射对。

### 3. 启发式算子的“原子化”特征库（微观操作）
在 CVRP 中，启发式函数往往是由多个微小的“邻域动作”组成的。FunSearch 在设计新的评分函数或接受准则时，需要参考这些原子操作。

+ **节点级操作：** Relocate（节点重定位）、Exchange/Swap（节点交换）、2-opt, 2-opt*, 3-opt 及其变体。
+ **路径级操作：** Cross-exchange（交叉交换）、Or-opt、Ejection Chains（排出链）。
+ **破坏与修复算子（ALNS特有）：** Shaw Removal（相关性移除）、Worst Removal（最差移除）、Regret Insertion（后悔插入）。
+ **语料形式：** 将这些算子拆解为独立的微小代码块，并附带时间复杂度（如  $ O\left(n^{2}\right) $ ）和适用场景说明。

### 4. 实例特征与数学度量标准库（评估上下文）
CVRP 的启发式函数好坏往往取决于具体的客户分布（例如：聚集型 Clustering、随机型 Random、中心型 Depot-central）。

+ **CVRPLIB 基准测试特征：** 包含常见数据集（如 Uchoa, Christofides, Golden）的数学特征描述。
+ **空间几何度量：** 计算距离、极角、客户需求/容量比（Demand/Capacity Ratio）、时间窗（如果扩展到 VRPTW）的常用数学公式和特征工程函数。
+ **语料形式：** 描述如何从原始坐标/需求数据中提取“状态特征向量”的代码和公式。

### 5. FunSearch 内部演化历史数据库（动态 RAG 语料）
除了外部静态知识，RAG 还应该包含 FunSearch 自身的历史轨迹。这是一个**动态更新的检索源**。

+ **高分代码池（Elites Pool）：** 历史上在评测器（Evaluator）中获得高分的启发式代码。
+ **错题本（Failed Mutations）：** 导致超时、死循环或得分极低的代码模式（避免 LLM 重蹈覆辙）。
+ **语料形式：** `<Prompt, Generated_Code, Score, Evaluation_Feedback>` 格式的 JSONL 数据。

### 6. 高效的数据结构与增量评估机制（Delta Evaluation）
在 CVRP 的局部搜索中，时间复杂度是决定启发式算法能否在合理时间内收敛的命脉。LLM 往往能写出逻辑正确的算子，但容易写出性能极差的  $ O\left(n\right) $  或  $ O\left(n^{2}\right) $  评估代码。

+ **增量评估（Delta Evaluation）代码库：** 补充如何在执行 2-opt 或 Swap 时，只计算发生改变的边和节点约束，而不是重新计算整条路径的总成本。
+ **前缀/后缀数据结构：** 引入用于  $ O\left(1\right) $  复杂度检查时间窗约束、容量约束的辅助数据结构代码片段（如前缀和、后缀和、连续子路径的负载/距离记录）。
+ **语料形式：** 顶级求解器（如 Vidal 提出的 HGS 变体）中专门用于“快速适应度计算（Fast Fitness Evaluation）”的 C++/Python 代码，配合时间复杂度证明。

### 7. 沙盒环境与 API 约束说明库（Meta-Knowledge）
FunSearch 生成的代码必须在一个特定的评测器（Evaluator）中运行。RAG 必须提供关于这个“运行环境”的绝对规则。

+ **对象模型（Object Models）：** 你的 CVRP 环境中 `Node`, `Route`, `Solution` 类的定义、可用方法和属性是什么？（例如：是否有 `route.is_feasible()` 方法？容量上限变量叫 `capacity` 还是 `Q`？）
+ **合法性检查器（Validator）：** 提供严格的容量约束和节点唯一性约束检查的伪代码，防止大模型产生“幻觉”，生成破坏硬约束的操作。
+ **语料形式：** 类似 API 文档格式的 Markdown 文件，包含代码输入/输出签名的严格规定。
