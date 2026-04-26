# 删除 retrieval_policy_counts 相关代码

## 背景
`retrieval_policy_counts` 是一个在代码中被引用但从未在 `ParsedRun` dataclass 中定义的字段。它在 `compare_rag.py` 的 `ParsedRun` 中没有对应的属性，但在两个文件中被引用，尝试访问一个不存在的字段。

## 影响范围
共 2 个文件需要修改：

1. **`scripts/run_rag_eval_20260420_133019.py`** (第177行)
   - `_parsed_run_summary` 函数中引用了 `run.retrieval_policy_counts`
   - 需要删除字典中的 `"retrieval_policy_counts": run.retrieval_policy_counts` 这一行

2. **`funsearch_cvrp_cot_plus_rag.ipynb`** (第145行)
   - notebook 的 print 语句中打印了 `run_result["retrieval_policy_counts"]`
   - 需要删除对应的 print 行

## 执行步骤

### Step 1: 删除 `run_rag_eval_20260420_133019.py` 中的引用
- 打开 `scripts/run_rag_eval_20260420_133019.py`
- 在 `_parsed_run_summary` 函数中，删除第177行：`"retrieval_policy_counts": run.retrieval_policy_counts,`

### Step 2: 删除 Jupyter Notebook 中的引用
- 打开 `funsearch_cvrp_cot_plus_rag.ipynb`
- 在最后一个 cell 中，删除第145行的 print 语句：`"print(\"retrieval_policy_counts:\", run_result[\"retrieval_policy_counts\"])"`

### Step 3: 验证
- 使用 grep 搜索确认没有遗漏的 `retrieval_policy_counts` 或 `policy_counts` 相关引用
- 确认修改后的文件语法正确

## 注意事项
- 不需要修改 `compare_rag.py`，因为该文件从未定义过 `retrieval_policy_counts` 字段
- 测试文件 `test_compare_runner.py` 也不涉及该字段，无需修改
