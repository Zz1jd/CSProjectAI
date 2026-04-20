# 权威语料库分阶段构建计划

## 1. 目标

在不再手工编写语料正文的前提下，按照 [Corpus Design.md](Corpus%20Design.md) 的 7 类设计要求，从权威、官方、一手来源重建 `external_corpus/`，形成一套可治理、可追溯、可用于检索与实验的 `v3.*` 语料版本族，并在通过治理检查后再恢复自适应检索实验。类别 1 除官方文档外，还要纳入顶级运筹学期刊 VRP 论文的章节级语料包，每篇入选论文至少覆盖 `Abstract`、`Introduction`、`Methodology`、`Experiments`、`Results`，并在需要时补充算法流程图的文本描述与标准化伪代码。

## 2. 当前问题

- 当前 `v2.*` 语料包含手工总结、内部蒸馏和空 `url` 元数据，不能视为合规语料。
- 当前实验已经证明，在 `v2.*` 上继续调参数收益很低，5% 阈值运行没有任何候选进入 stage 2。
- 当前论文型语料设计还停留在摘要级补充，缺少 `Introduction`、`Methodology`、`Experiments`、`Results` 这些能支撑理论理解与证据检索的章节级节点。
- 当前真正需要解决的是语料来源质量与治理约束，而不是继续扩充手写文档。

## 3. 约束原则

- 外部语料只允许来自官方文档、官方仓库、官方 benchmark/dataset 站点，以及类别 1 中经过治理约束的顶级运筹学期刊 VRP 论文。
- 内部语料只允许来自本仓库的一手源码、评测器、运行日志、结果文件和程序数据库记录。
- 顶级期刊论文只进入类别 1 和 `v3.0.0_official_foundation`，不作为类别 2、3、6 的主来源。
- 每篇入选期刊论文必须形成完整章节包，至少包含 `Abstract`、`Introduction`、`Methodology`、`Experiments`、`Results`；`journal_flow_description` 和 `journal_pseudocode` 只能作为 `Methodology` 的增强节点，不能替代核心章节。
- 论文型语料必须记录可追溯章节锚点，包括 `section_ref`，并在需要时补充 `figure_ref`、`table_ref`、`algorithm_ref`、benchmark family、metrics、baseline 等元数据。
- 允许对论文章节进行结构化摘录、流程图文字化描述和标准化伪代码整理，但不允许复制原图、不允许整节大段照搬、不允许没有章节锚点的自由改写。
- 不允许把 [Corpus Design.md](Corpus%20Design.md) 或现有内部笔记直接改写成语料正文。
- 所有文档必须带可追溯来源，包括 `url` 或仓库内源路径、`license`、`source_type`、`distilled_from`。
- `v2.*` 在 `v3.*` 完成前保留，但只能作为迁移参考和失败案例，不再作为合规版本继续扩写。

## 4. 版本策略

| 版本 | 作用 | 覆盖类别 | 说明 |
| --- | --- | --- | --- |
| `v3.0.0_official_foundation` | 新控制组 | 1、4、7 | 先建立最稳的官方基础语料，并为类别 1 纳入期刊论文章节包 |
| `v3.1.0_official_solver_atoms` | 算子与代码扩展 | 2、3、6 | 在基础语料上追加工程级代码与原子算子 |
| `v3.2.0_official_plus_history` | 内部历史增强 | 5 | 只追加从一手运行记录抽取的动态语料 |
| `v3.3.0_official_full` | 最终实验版本 | 1-7 | 全量合规版本，用于后续正式检索实验 |

## 5. 设计类别到来源矩阵

| 类别 | 目标内容 | 主来源 | 允许的语料形式 | 目标版本 |
| --- | --- | --- | --- | --- |
| 1. 经典理论与伪代码 | 构造启发式、局部搜索、元启发式、实验设计与结果证据 | OR-Tools 官方文档、ALNS 官方文档、VeRyPy 官方仓库、HGS-CVRP 官方仓库、LKH-3 官方页面、EJOR、Computers & Operations Research、Transportation Science 等顶级期刊 VRP 论文 | `Abstract`、`Introduction`、`Methodology`、`Experiments`、`Results` 章节节点，流程描述，标准化伪代码，带来源说明的摘要与论文定位节点 | `v3.0.0` |
| 2. 高质量开源求解器源码 | 函数级代码片段、Docstring、类定义 | OR-Tools、PyVRP、HGS-CVRP、VeRyPy、jsprit 官方仓库 | 受许可约束的短代码片段和功能说明对 | `v3.1.0` |
| 3. 原子化算子 | Relocate、Swap、2-opt、Or-opt、Shaw removal 等 | PyVRP、HGS-CVRP、VeRyPy、ALNS 官方示例、jsprit 官方仓库 | 单算子文档、复杂度标签、适用场景标签 | `v3.1.0` |
| 4. 实例特征与数学度量 | CVRPLIB 实例族、VRPLIB 格式、需求/容量特征 | CVRPLIB 官方站点、PyVRP 官方文档 | 数据集说明、公式、特征提取说明 | `v3.0.0` |
| 5. FunSearch 内部演化历史 | 高分样本、失败模式、反馈 | `results/`、运行日志、ProgramsDatabase 相关输出 | JSONL 记录、结构化 Markdown、失败模式索引 | `v3.2.0` |
| 6. Delta evaluation 与快速评估 | 增量代价计算、前缀/后缀结构 | PyVRP、HGS-CVRP、OR-Tools、VeRyPy 官方资料 | 代码片段、复杂度说明、适用约束说明 | `v3.1.0` |
| 7. 沙盒环境与 API 约束 | 真实输入签名、可用数组、合法性检查 | 本仓库源码：`specification.py`、`sandbox.py`、`dataset.py`、`implementation/evaluator.py`、`implementation/evaluator_accelerate.py` | 精确摘录、契约文档、约束说明 | `v3.0.0` |

## 6. 分阶段计划

### 阶段 0：冻结当前状态并建立治理红线

**目标**

把当前 `v2.*` 明确标记为“非合规占位语料”，先停止继续写新语料，再建立进入 `v3.*` 的准入规则。

**输入**

- 现有 `external_corpus/v2.*`
- [Corpus Design.md](Corpus%20Design.md)
- 现有 manifest、dedup 报告、检索实验结果

**任务**

- 盘点所有 `license: Internal synthesis`、空 `url`、仅指向设计文档的文档。
- 形成允许来源白名单与禁止来源黑名单。
- 定义外部来源与内部来源的最小元数据要求。
- 为顶级期刊论文补充专门准入规则，明确允许的章节类型、允许的摘录粒度，以及 `section_ref`、`figure_ref`、`table_ref`、`algorithm_ref`、benchmark/metrics/baseline 标签的最小要求。
- 明确 `v2.*` 只保留、不扩写、不参与“合规语料”口径。

**产物**

- 非合规问题清单
- 来源准入规则文档
- `v3.*` 版本命名与范围说明

**退出条件**

- 已能明确判断一个文档是否允许进入 `v3.*`
- 已能明确判断一篇期刊论文是否满足“完整章节包”准入条件，以及单个章节节点是否合规。
- 团队内部对“官方/权威来源”口径无歧义

### 阶段 1：建立来源注册表与采集规范

**目标**

把“从哪里抓、抓什么、怎么标注、进哪个版本”固化成机器可读和人工可审的注册表，而不是临时手写 Markdown。

**输入**

- 阶段 0 的来源准入规则
- 已确认的权威来源站点与仓库

**任务**

- 为每个候选来源登记：类别、来源类型、许可证、提取策略、目标版本、允许摘录粒度。
- 区分“页面摘录”“代码片段”“仓库内一手日志抽取”“期刊章节摘录”四类采集模式。
- 规定快照策略，避免上游页面后续变化导致语料不可复现。
- 规定每篇入选论文必须同时登记 `journal_abstract`、`journal_introduction`、`journal_methodology`、`journal_experiments`、`journal_results` 五类核心节点；在算法描述足够清晰时，再登记 `journal_flow_description` 与 `journal_pseudocode`。
- 规定何时允许 DOI 页面、出版社摘要页或论文主页作为稳定来源入口，以及如何把章节锚点映射到语料 front matter。

**产物**

- 来源注册表
- 采集规范
- 许可证分桶规则

**退出条件**

- 每个设计类别至少有 1 个已批准主来源
- 类别 1 至少有一组已批准的期刊来源家族，且采集规范足以支持完整章节包构建。
- 所有来源都能映射到明确的目标版本

### 阶段 2：构建 `v3.0.0_official_foundation`

**目标**

先完成最小但可靠的基础语料，用它替换当前实验控制组。

**覆盖类别**

- 类别 1：经典理论与伪代码
- 类别 4：实例特征与数学度量
- 类别 7：沙盒环境与 API 约束

**输入**

- OR-Tools 官方 CVRP 文档
- ALNS 官方文档
- EJOR、Computers & Operations Research、Transportation Science 等顶级期刊中的代表性 VRP 论文
- CVRPLIB 官方站点
- PyVRP 官方 VRPLIB 与 benchmark 文档
- 本仓库运行时源码与评测器源码

**任务**

- 为类别 1 生成“论文定位节点 + 章节叶子节点”结构化文档，避免大段综述文本。每篇入选论文必须至少产出 `Abstract`、`Introduction`、`Methodology`、`Experiments`、`Results` 五类节点。
- 在 `Methodology` 节点基础上，按需补充算法流程图的文本描述与标准化伪代码，但不以流程描述或伪代码替代核心章节。
- 为类别 4 提取实例族、格式规则、特征工程入口，而不是泛化成经验文字。
- 为类别 7 生成严格契约文档，精确说明评测函数签名、输入张量、禁止假设的对象模型。
- 对所有文档补齐 front matter，并运行 manifest/dedup 构建。

**产物**

- `external_corpus/v3.0.0_official_foundation/`
- 对应 `manifest.json` 和 `dedup_report.json`
- Foundation 级语料覆盖清单，包括类别 1 的期刊论文章节包覆盖表

**退出条件**

- 类别 1、4、7 均有合规文档，且类别 1 至少有一组来自批准期刊的完整章节包
- 不存在空 `url` 或 `Internal synthesis`
- 检索层可以对 `v3.0.0` 返回非空、带 provenance 的命中

### 阶段 3：构建 `v3.1.0_official_solver_atoms`

**目标**

在基础语料之上补齐工程级代码片段、算子和增量评估知识，使检索内容更贴近 FunSearch 会生成的代码形态。

**覆盖类别**

- 类别 2：高质量开源求解器源码
- 类别 3：原子化算子
- 类别 6：Delta evaluation 与快速评估

**输入**

- PyVRP 官方仓库与文档
- HGS-CVRP 官方仓库
- VeRyPy 官方仓库
- OR-Tools 官方仓库和文档
- ALNS 官方示例

**任务**

- 提取短代码片段与功能描述映射，不导入大段不可控代码。
- 为每个原子算子单独建文档，附复杂度、约束、适用场景。
- 为 delta evaluation 建立“操作类型 -> 受影响边/节点 -> 需要增量更新的量”文档。
- 不把期刊论文章节直接迁移为类别 2、3、6 的主语料，避免 solver_atoms 层退化成论文综述层。
- 对许可证敏感来源做最小化摘录或只保留元数据引用。

**产物**

- `external_corpus/v3.1.0_official_solver_atoms/`
- 算子级索引
- 代码片段许可证清单

**退出条件**

- 类别 2、3、6 均至少有一组高质量来源支撑
- 检索结果不再只偏向内部总结，而能命中官方算子与代码片段

### 阶段 4：构建 `v3.2.0_official_plus_history`

**目标**

把 FunSearch 自身的历史记录变成结构化动态语料，但不再写手工“经验总结”。

**覆盖类别**

- 类别 5：FunSearch 内部演化历史

**输入**

- `results/` 下的实验日志与报告
- 程序数据库与历史样本记录
- 运行期反馈信息，如超时、无效样本、得分变化

**任务**

- 定义历史样本记录模式，例如 `<prompt_hash, generated_code, score, valid_ratio, failure_type, evaluation_feedback>`。
- 把高分样本与失败模式拆为不同索引，避免失败案例在默认检索中压过有效案例。
- 只从原始记录生成 JSONL 或结构化 Markdown，不写自由叙述的历史总结。
- 给内部历史记录补齐来源路径、生成时间、实验批次、适用性标签。

**产物**

- `external_corpus/v3.2.0_official_plus_history/`
- 历史 JSONL 或结构化记录文件
- 失败模式与高分样本索引

**退出条件**

- 类别 5 可用于检索，但默认策略不会让失败模式主导上下文
- 历史文档能追溯到具体实验结果文件或数据库记录

### 阶段 5：构建 `v3.3.0_official_full` 并完成治理闭环

**目标**

合并所有合规类别，完成最终实验版本，同时用治理规则阻断未来再次出现手工蒸馏语料。

**输入**

- `v3.0.0`、`v3.1.0`、`v3.2.0` 的构建结果
- 现有治理脚本与检索运行时

**任务**

- 合并全量语料，执行 dedup、front matter 校验、许可证校验、来源校验。
- 新增治理规则，拒绝空来源、拒绝设计文档直改语料、拒绝 `Internal synthesis`、拒绝缺失核心章节的期刊论文包。
- 为期刊章节节点增加专门治理规则，校验 `source_type`、`summary_level`、`section_ref`、期刊来源字段，以及 `Experiments`/`Results` 节点所需的 benchmark 与指标元数据。
- 对 summary/leaf 结构做一次统一整理，避免 full 版本重新退化为大块平铺文本。
- 生成最终版本覆盖矩阵，说明每个类别由哪些来源支撑。

**产物**

- `external_corpus/v3.3.0_official_full/`
- 完整 manifest 和 dedup 报告
- 全量来源与许可证清单

**退出条件**

- 全部 7 类设计要求都能在 `v3.3.0` 中找到合规支撑
- 治理规则可以自动拦截不合规新增文档，并能识别不完整的期刊章节包

### 阶段 6：切换检索配置并恢复实验

**目标**

把新的权威语料接回现有检索与实验流程，验证其是否优于当前 `v2.*` 脚手架版本。

**输入**

- `v3.0.0` 至 `v3.3.0` 全部语料版本
- 现有检索和实验脚本
- 已确认的 5% 接受阈值配置

**任务**

- 更新控制组与 source variants，使实验只比较 `v3.*` 版本。
- 先做 retrieval smoke check，确认命中结果非空、来源可追溯、注入字符数正常。
- 增加章节意图 smoke check：算法原理类 query 应优先命中 `Methodology`、流程描述和标准化伪代码节点；benchmark、指标和适用场景类 query 才优先命中 `Experiments`、`Results` 节点。
- 再做 20-sample staged smoke run，避免直接投入完整 20->100 正式运行。
- 如果 smoke run 正常，再执行正式自适应搜索，并对比 `v3.0.0` 至 `v3.3.0`。

**产物**

- 切换后的实验配置
- smoke run 结果
- 正式 staged run 结果和报告

**退出条件**

- 新语料族已替换旧控制组
- 检索命中质量和实验指标都可解释
- 可以决定是否彻底退役 `v2.*`

## 7. 并行安排

- 阶段 0 和阶段 1 必须串行完成。
- 阶段 2 中的类别 1、4、7 可以并行采集，但必须使用同一套来源注册表和元数据规范；类别 1 内部可以并行采集官方理论文档和期刊章节包，但每篇论文的核心章节包必须成套完成。
- 阶段 3 的类别 2、3、6 可以并行采集，但要共享统一的许可证规则和片段粒度限制。
- 阶段 4 可以在阶段 3 后半段并行启动，因为它依赖的是内部记录模式，而不是外部来源抓取。
- 阶段 5 和阶段 6 必须顺序执行。

## 8. 文件与目录规划

| 路径 | 用途 |
| --- | --- |
| `external_corpus/v3.0.0_official_foundation/` | 基础官方语料与类别 1 的期刊论文章节包 |
| `external_corpus/v3.1.0_official_solver_atoms/` | 代码、算子、delta evaluation 语料 |
| `external_corpus/v3.2.0_official_plus_history/` | 结构化内部历史语料 |
| `external_corpus/v3.3.0_official_full/` | 全量实验语料 |
| `implementation/corpus_governance.py` | 新增来源与许可证治理规则 |
| `scripts/build_corpus_manifest.py` | 继续作为 manifest 构建入口 |
| `implementation/retrieval.py` | 复用现有检索逻辑，后续只需要切版本和验证命中质量 |
| `tests/test_corpus_governance.py` | 覆盖期刊章节包与 provenance 约束的治理测试 |
| `scripts/experiments/rag_iteration_config.py` | 切换控制组和 source variants 到 `v3.*` |
| `scripts/experiments/space.py` | 调整候选空间以比较新语料族 |
| `scripts/run_rag_iteration.py` | 在语料构建完成后恢复实验 |

## 8.1 类别 1 期刊目录与命名规范

- 期刊章节包目录统一放在 `external_corpus/v3.0.0_official_foundation/journals/`。
- 期刊层级使用 `journals/<journal_slug>/<year>_<first_author>_<paper_slug>/`，其中 `journal_slug` 例如 `ejor`、`cor`、`transportation_science`。
- 每篇论文至少包含以下 5 个核心文件：`abstract.md`、`introduction.md`、`methodology.md`、`experiments.md`、`results.md`。
- 可选增强文件只允许在核心章节齐备后补充：`flow_description.md`、`pseudocode.md`。
- 一个目录只对应一篇论文；同一论文的所有节点共用同一组 `paper_title`、`url`、`doi`、`journal`、`paper_type`、`year`。
- `abstract.md` 推荐使用 `summary_level: summary`；其余核心章节默认使用 `summary_level: leaf`。
- `Experiments` 与 `Results` 节点必须填写 `benchmark_family` 和 `metrics`；如论文明确给出对比方法，再补 `baseline`。

## 8.2 类别 1 期刊节点模板

### 核心章节模板：`abstract.md` / `introduction.md` / `methodology.md`

```yaml
---
title: <node_title>
paper_title: <paper_title>
url: <stable_url_or_doi_url>
doi: <doi_if_available>
date: <snapshot_or_publication_date>
year: <paper_year>
license: <license_or_access_note>
topics: cvrp,vrp,<topic_3>
summary: <1_line_node_summary>
source_type: journal_abstract | journal_introduction | journal_methodology
summary_level: summary | leaf
journal: <journal_name>
paper_type: research_article
section_ref: Abstract | 1 Introduction | 3 Methodology
figure_ref: <optional>
table_ref: <optional>
algorithm_ref: <optional>
distilled_from: <optional_source_anchor>
---

<2_to_8_sentence_structured_paraphrase_with_clear_section_scope>
```

### 证据章节模板：`experiments.md` / `results.md`

```yaml
---
title: <node_title>
paper_title: <paper_title>
url: <stable_url_or_doi_url>
doi: <doi_if_available>
date: <snapshot_or_publication_date>
year: <paper_year>
license: <license_or_access_note>
topics: cvrp,benchmark,<topic_3>
summary: <1_line_node_summary>
source_type: journal_experiments | journal_results
summary_level: leaf
journal: <journal_name>
paper_type: research_article
section_ref: 4 Experiments | 5 Results
figure_ref: <optional>
table_ref: <optional>
algorithm_ref: <optional>
benchmark_family: <dataset_family_1>,<dataset_family_2>
metrics: <metric_1>,<metric_2>
baseline: <baseline_1>,<baseline_2>
distilled_from: <optional_source_anchor>
---

<2_to_8_sentence_structured_paraphrase_focused_on_setup_or_findings>
```

### 可选增强模板：`flow_description.md` / `pseudocode.md`

```yaml
---
title: <node_title>
paper_title: <paper_title>
url: <stable_url_or_doi_url>
doi: <doi_if_available>
date: <snapshot_or_publication_date>
year: <paper_year>
license: <license_or_access_note>
topics: cvrp,heuristics,<topic_3>
summary: <1_line_node_summary>
source_type: journal_flow_description | journal_pseudocode
summary_level: leaf
journal: <journal_name>
paper_type: research_article
section_ref: <methodology_subsection_anchor>
algorithm_ref: <required_if_available>
figure_ref: <optional>
distilled_from: <optional_source_anchor>
---

<structured_flow_or_standardized_pseudocode_notes>
```

## 8.3 样板目录要求

- 在正式采集前，先建立一篇模板论文目录，文件名和 front matter 字段必须与正式规范一致。
- 样板目录中的文件统一使用 `.md.example` 后缀，避免在内容未替换为真实语料前被 `manifest` 当作正式文档收录。
- 真实入库时，只替换内容与元数据，不改目录结构和文件基名。

## 9. 验证清单

- 文档级验证：每个语料文档都带真实来源、许可证和来源类型；期刊章节节点还必须带 `section_ref`，并在需要时带 `figure_ref`、`table_ref`、`algorithm_ref`、benchmark/metrics/baseline 元数据。
- 类别级验证：7 个设计类别都至少有一组合规来源支撑；类别 1 的每篇入选期刊论文都形成完整的 `Abstract`、`Introduction`、`Methodology`、`Experiments`、`Results` 章节包。
- 版本级验证：每个 `v3.*` 版本都能成功生成 manifest 和 dedup 报告。
- 检索级验证：`retrieval_mean_injected_chars` 不再长期为 0，且命中来源与类别符合预期；方法类 query 与实验结果类 query 的命中章节分布符合设计意图。
- 实验级验证：在 `v3.*` 上先过 smoke run，再决定是否做完整正式运行。

## 10. 建议执行顺序

1. 先完成阶段 0 和阶段 1，锁定来源规则，不再写任何新手工语料。
2. 立即落地阶段 2，优先构建 `v3.0.0_official_foundation`，并先把类别 1 的期刊论文章节包做完整，因为它将成为新的控制组。
3. 再推进阶段 3 和阶段 4，把外部官方知识和内部历史知识分开建设。
4. 最后做阶段 5 与阶段 6，统一治理并恢复实验。

## 11. 明确不做的事

- 不再手工撰写“经典启发式总览”“经验总结”“失败模式故事化描述”作为主语料。
- 不把二手博客、论坛、无来源教程纳入正式语料。
- 不把期刊论文只做摘要节点而忽略 `Introduction`、`Methodology`、`Experiments`、`Results` 核心章节。
- 不复制论文原图、整节大段正文或缺少章节锚点的自由总结进入正式语料。
- 不在 `v3.*` 通过治理前继续做大规模参数搜索。
- 不直接删除 `v2.*`，直到 `v3.*` 全部验证完成。