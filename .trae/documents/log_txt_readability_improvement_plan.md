# 日志 TXT 可读性改进计划

## 问题描述
当前的日志 txt 文件输出缺乏清晰的分隔符，导致多条日志信息混杂在一起，难以阅读和解析。

## 当前日志输出点分析

### 1. `scripts/_runner.py` - `run_logged_experiment` 函数
- 输出 `RUN_LABEL` 和 header_fields
- 通过 TeeWriter 将所有 print 输出同时写入终端和日志文件

### 2. `implementation/funsearch.py` - `main` 函数
- 输出 `RUN_METADATA: {json}` (第121行)

### 3. `implementation/sampler.py` - `Sampler.sample` 方法
- 输出 `RETRIEVAL_DIAGNOSTICS: {json}` (第153行)，仅当 `rag.enable_diagnostics=True`，每批次 1 次
- 输出 `DEBUG: Sample {i} prefix: ...` 或 `DEBUG: Sample {i} is empty or too short!` (第162-164行)，无条件，每个 sample 1 条
- 输出 `SAMPLER_ERROR: {error}` (第184行)，异常时输出

### 4. `implementation/evaluator.py` - `Evaluator.analyse` 方法
- 输出 `EVAL_SUMMARY: valid={valid_evals} total={total_evals} ratio={valid_ratio:.6f}` (第206行)，每个 sample 1 条

### 5. `implementation/profile.py` - `Profiler._record_and_verbose` 方法
- 输出 `================= Evaluated Function =================` (第109行)，每个 sample 最多 1 次（按 sample_orders 去重）

## 目标日志输出样式

假设 `max_sample_nums=8`, `samples_per_prompt=4`, `rag.enable_diagnostics=True`，完整循环输出如下：

```
===============================================================
  EXPERIMENT START
===============================================================
RUN_LABEL: RAG
RUN_MODE: stage_eval
RUN_BUDGET: 8
---------------------------------------------------------------

RUN_METADATA: {"seed": 42, "llm_model": "gpt-4o-mini", "model_track": "rag", "run_mode": "stage_eval", "dataset_path": "./cvrplib/setB", "max_sample_nums": 8, "samples_per_prompt": 4, "evaluate_timeout_seconds": 30, "num_samplers": 1, "num_evaluators": 1, "api_base_url_explicit": true, "api_key_explicit": true, "api_timeout_seconds": 60, "api_max_retries": 2, "rag_enabled": true, "rag_corpus_root": "corpus/", "rag_chunk_size": 1200, "rag_chunk_overlap": 200, "rag_top_k": 2, "rag_retrieval_mode": "hybrid", "rag_score_threshold": 0.05, "rag_max_context_chars": 900, "rag_diagnostics_enabled": true, "rag_use_intent_query": true, "rag_embedding_model": "BAAI/bge-small-en-v1.5", "rag_embedding_base_url_explicit": false, "rag_embedding_api_key_explicit": false}
---------------------------------------------------------------

  [Sample Batch #1 - Samples 1 to 4]
---------------------------------------------------------------
RETRIEVAL_DIAGNOSTICS: {"query": "optimize vehicle routing priority function", "docs_found": 2, "top_score": 0.8523, "top_score_gap": 0.1234, "confidence": 0.9012, "injected_chars": 456, "injected_sources": 1, "unique_sources": 2, "skipped": false}
DEBUG: Sample 0 prefix: def priority(current_node, distance_data, remaining_capacity, node_demands):     return -distance_data[current_node]...
DEBUG: Sample 1 prefix: def priority(current_node, distance_data, remaining_capacity, node_demands):     return distance_data[current_node] * node_dem...
DEBUG: Sample 2 prefix: def priority(current_node, distance_data, remaining_capacity, node_demands):     score = distance_data[current_node] / remaini...
DEBUG: Sample 3 is empty or too short!
---------------------------------------------------------------
================= Evaluated Function =================
def priority_v0(current_node, distance_data, remaining_capacity, node_demands):
    return -distance_data[current_node]
------------------------------------------------------
Score        : -1161.9876066089935
Sample time  : 1.25
Evaluate time: 4.5
Sample orders: 1
======================================================

EVAL_SUMMARY: valid=2 total=10 ratio=0.200000


================= Evaluated Function =================
def priority_v0(current_node, distance_data, remaining_capacity, node_demands):
    return distance_data[current_node] * node_demands[current_node]
------------------------------------------------------
Score        : -1245.3321098765432
Sample time  : 1.18
Evaluate time: 4.2
Sample orders: 2
======================================================

EVAL_SUMMARY: valid=3 total=10 ratio=0.300000


================= Evaluated Function =================
def priority_v0(current_node, distance_data, remaining_capacity, node_demands):
    score = distance_data[current_node] / remaining_capacity
    return score
------------------------------------------------------
Score        : -1890.445566778899
Sample time  : 1.32
Evaluate time: 4.8
Sample orders: 3
======================================================

EVAL_SUMMARY: valid=1 total=10 ratio=0.100000


================= Evaluated Function =================
def priority_v0(current_node, distance_data, remaining_capacity, node_demands):
    return None
------------------------------------------------------
Score        : None
Sample time  : 1.05
Evaluate time: 3.9
Sample orders: 4
======================================================

EVAL_SUMMARY: valid=0 total=10 ratio=0.000000



  [Sample Batch #2 - Samples 5 to 8]
---------------------------------------------------------------
RETRIEVAL_DIAGNOSTICS: {"query": "CVRP heuristic function design", "docs_found": 1, "top_score": 0.7234, "top_score_gap": 0.0987, "confidence": 0.8543, "injected_chars": 312, "injected_sources": 1, "unique_sources": 1, "skipped": false}
DEBUG: Sample 0 prefix: def priority(current_node, distance_data, remaining_capacity, node_demands):     if remaining_capacity < node_demands[curre...
DEBUG: Sample 1 prefix: def priority(current_node, distance_data, remaining_capacity, node_demands):     return np.exp(-distance_data[current_node])...
DEBUG: Sample 2 is empty or too short!
DEBUG: Sample 3 prefix: def priority(current_node, distance_data, remaining_capacity, node_demands):     demands_ratio = node_demands[current_node] /...
---------------------------------------------------------------
================= Evaluated Function =================
def priority_v0(current_node, distance_data, remaining_capacity, node_demands):
    if remaining_capacity < node_demands[current_node]:
        return float('inf')
    return distance_data[current_node]
------------------------------------------------------
Score        : -1089.7766554433221
Sample time  : 1.41
Evaluate time: 5.1
Sample orders: 5
======================================================

EVAL_SUMMARY: valid=4 total=10 ratio=0.400000


================= Evaluated Function =================
def priority_v0(current_node, distance_data, remaining_capacity, node_demands):
    return np.exp(-distance_data[current_node])
------------------------------------------------------
Score        : -1356.8899001122334
Sample time  : 1.28
Evaluate time: 4.6
Sample orders: 6
======================================================

EVAL_SUMMARY: valid=2 total=10 ratio=0.200000


================= Evaluated Function =================
def priority_v0(current_node, distance_data, remaining_capacity, node_demands):
    return float('nan')
------------------------------------------------------
Score        : None
Sample time  : 1.15
Evaluate time: 4.0
Sample orders: 7
======================================================

EVAL_SUMMARY: valid=0 total=10 ratio=0.000000


================= Evaluated Function =================
def priority_v0(current_node, distance_data, remaining_capacity, node_demands):
    demands_ratio = node_demands[current_node] / sum(node_demands)
    return distance_data[current_node] * demands_ratio
------------------------------------------------------
Score        : -1278.5544332211009
Sample time  : 1.35
Evaluate time: 4.7
Sample orders: 8
======================================================

EVAL_SUMMARY: valid=3 total=10 ratio=0.300000



===============================================================
  EXPERIMENT END
===============================================================
```

## 格式规则总结

1. **主分隔线**（实验开始/结束）：`=` 63 个
2. **次级分隔线**（批次分隔、元数据分隔）：`-` 63 个
3. **采样间隔**：每个采样之间空 3 行
4. **Evaluated Function 和 EVAL_SUMMARY 顺序**：Evaluated Function 在前，EVAL_SUMMARY 在后，两者之间空 1 行
5. **批次标题**：`[Sample Batch #N - Samples X to Y]`
6. **DEBUG 消息**：保留原有前缀格式，确保解析器兼容
7. **RETRIEVAL_DIAGNOSTICS**：紧跟批次标题后
8. **所有原有的 `KEY: VALUE` 前缀保持不变**

## 具体步骤

### 步骤 1: 创建日志格式化工具模块
**文件**: `implementation/log_formatter.py`

提供分隔线常量和格式化函数。

### 步骤 2: 修改 `scripts/_runner.py`
- 在实验开始/结束时输出主分隔线
- 使用格式化工具输出 RUN_LABEL 和 header_fields

### 步骤 3: 修改 `implementation/funsearch.py`
- 在 main 函数开始时输出实验开始分隔线
- 使用格式化工具输出 RUN_METADATA

### 步骤 4: 修改 `implementation/sampler.py`
- 在批次开始/结束时输出批次标题和次级分隔线
- 使用格式化工具输出 RETRIEVAL_DIAGNOSTICS 和 DEBUG 信息

### 步骤 5: 修改 `implementation/evaluator.py`
- 移除原有的 EVAL_SUMMARY 输出（移至 profile.py 中输出）

### 步骤 6: 修改 `implementation/profile.py`
- 调整 Evaluated Function 输出格式
- 在 Evaluated Function 之后输出 EVAL_SUMMARY
- 每个采样之间添加 3 行空行

### 步骤 7: 更新测试文件
- 更新 `tests/test_profile_fallback.py` 中的测试期望

## 兼容性考虑
- 日志解析器 (`scripts/compare_rag.py`) 使用正则表达式解析日志
- 所有关键前缀保持不变：`RUN_METADATA:`、`EVAL_SUMMARY:`、`DEBUG:`、`RETRIEVAL_DIAGNOSTICS:`
- 分隔线不应干扰正则表达式匹配

## 实施约束
- 不改变现有的日志解析逻辑
- 保持所有现有的 `KEY: VALUE` 格式前缀
- 分隔线使用 ASCII 兼容字符
- 不引入新的依赖
