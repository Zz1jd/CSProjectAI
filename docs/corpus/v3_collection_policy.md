# V3 语料来源规则

## 1. 这份文档解决什么问题

这份规则不是语料正文，而是告诉后续构建流程三件事：

- 哪些来源可以进入 `v3.*`
- 哪些来源必须一票否决
- 每篇文档至少要写清楚哪些来源追踪信息

第一批落地只覆盖两件事：

- 用规则和审计停用 `v2.*` 的活动地位
- 用仓库内原始 Python 源码先建出类别 7 的合规样例

## 2. 允许来源

- 官方文档站点，例如 OR-Tools、ALNS、PyVRP 文档
- 官方仓库，例如 PyVRP、HGS-CVRP、VeRyPy、jsprit
- 官方 benchmark 或 dataset 站点，例如 CVRPLIB
- 顶级运筹学期刊论文，但只允许按章节包方式进入 `v3.0.0_official_foundation`
- 本仓库内的一手源码、评测器、结果日志、程序数据库输出

## 3. 禁止来源

- `license: Internal synthesis`
- 空来源，也就是既没有 `url`，也没有 `source_paths`
- 直接把 [Corpus Design.md](Corpus%20Design.md) 或其他规划文档改写成语料正文
- 论坛、博客、匿名教程、二手综述
- 缺核心章节的期刊论文包

## 4. V3 文档最小字段

所有 `v3.*` 文档都必须至少具备这些字段：

- `title`
- `summary`
- `source_type`
- `summary_level`
- `license`
- `distilled_from`
- `url` 或 `source_paths`

如果来源是仓库内原始代码，还必须额外写：

- `source_scope: repository`
- `source_paths`
- `source_anchor`

如果来源是期刊论文，还必须额外写：

- `section_ref`
- `journal`
- `paper_type`
- `summary_level`

如果章节属于 `Experiments` 或 `Results`，还必须额外写：

- `benchmark_family`
- `metrics`

## 5. 第一批样例只写什么

第一批正式语料只写 Markdown 说明文档，不写新的 Python 代码。原因很简单：

- 检索系统消费的是文本语料
- 这些文档的内容必须来自原始代码文件
- 文档 front matter 要能追踪到具体源文件路径

第一批样例限定在 `external_corpus/v3.0.0_official_foundation/runtime_contracts/`，来源仅限：

- [specification.py](../../specification.py)
- [sandbox.py](../../sandbox.py)
- [dataset.py](../../dataset.py)
- [implementation/evaluator.py](../../implementation/evaluator.py)
- [implementation/evaluator_accelerate.py](../../implementation/evaluator_accelerate.py)

## 6. 为什么还要做 V2 审计

`v2.*` 已经被判定为不可作为合规语料继续使用，但审计仍然有意义，因为它要产出一份明确的红名单：

- 哪些文件因为 `Internal synthesis` 出局
- 哪些文件因为缺失来源出局
- 哪些文件因为直接依赖规划文档出局

这份红名单随后会变成自动检查逻辑，防止同样的问题重新进入 `v3.*`。
