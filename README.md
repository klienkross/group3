# LLM 安全审计系统

一个基于 LLM（DeepSeek）的代码安全审计工具，可以自动检测 Java 代码中的漏洞，并计算审计准确率。

## 功能特性

- **自动测试集生成** - 从 Benchmark XML 中随机抽取样本，支持混入正常函数进行评估
- **LLM 审计** - 调用 DeepSeek API 对代码进行安全审计
- **准确率评估** - 自动计算 Accuracy、Precision、Recall、F1 分数
- **Web UI** - 简单易用的前端界面，支持实时进度显示
- **隐藏标签机制** - 向 LLM 隐藏 ground truth，仅暴露必要的代码信息

## 项目结构

```
group3/
├── app.py                          # Flask 服务器入口
├── llm_security_audit.py          # LLM 审计核心逻辑
├── benchmark_generator.py         # 测试集生成器
├── config.py                      # 配置文件（API密钥等）
├── templates/
│   └── index.html                # Web UI 界面
├── benchmark/
│   └── benchmark-crawler-http.xml # 数据源
└── README.md                      # 本文件
```

## 依赖

- Python 3.7+
- Flask
- pandas
- openai (for DeepSeek API)

## 安装

1. 安装依赖：
```bash
python -m pip install flask pandas openai
```

2. 配置 API 密钥：
编辑 `config.py`，设置你的 DeepSeek API key：
```python
DEEPSEEK_API_KEY = "your-api-key-here"
```

## 快速开始

### 方法1：Web UI（推荐）

```bash
cd group3
python app.py
```

然后打开浏览器访问 http://127.0.0.1:5000

点击"开始"按钮：
- 自动生成 50 条随机测试样本
- 逐条发送给 LLM 进行审计
- 实时显示处理进度（处理第 1/50 条...）
- 返回准确率统计和结果预览

### 方法2：命令行

```bash
python llm_security_audit.py
```

会依次执行：
1. 生成测试集 -> `benchmark_sample.csv`
2. LLM 审计 -> `benchmark_sample_results.csv`
3. 计算准确率并打印到控制台

## 核心模块说明

### benchmark_generator.py

**功能**：从 XML 中提取样本，打乱后抽取

```python
from benchmark_generator import extract_sample_from_benchmark

# 抽取 50 条样本
df = extract_sample_from_benchmark(sample_size=50, output_csv='samples.csv')
```

**输出 CSV 列**：
- `tcName`: 测试用例名
- `URL`: 测试 URL
- `tcType`: 类型（通常为 SERVLET）
- `vuln_type`: 漏洞类型（从 URL 提取，不给 LLM 看）
- `has_vulnerability`: 是否有漏洞（不给 LLM 看）

### llm_security_audit.py

**两个核心函数**：

#### 1. `audit_with_llm()`
调用 LLM 进行审计，支持实时进度回调

```python
from llm_security_audit import audit_with_llm

results = audit_with_llm(
    samples_csv='benchmark_sample.csv',
    output_results_csv='benchmark_sample_results.csv',
    on_progress=lambda msg: print(msg)  # 可选的进度回调
)
```

**工作流程**：
1. 读取样本 CSV（包含 ground truth 但不会发给 LLM）
2. 对每条样本，只发送 `tcName`, `URL`, `tcType` 给 LLM
3. 提取 LLM 回复中的 `vuln` 字段作为预测
4. 保存结果（包含预测和真实标签供对比）

#### 2. `calculate_accuracy()`
计算审计准确率

```python
from llm_security_audit import calculate_accuracy

stats = calculate_accuracy(results_csv='benchmark_sample_results.csv')
```

**返回指标**：
- `accuracy`: 总体准确率
- `precision`: 精确率（漏洞检测准确性）
- `recall`: 召回率（漏洞检出率）
- `f1_score`: F1 综合分数
- 混淆矩阵：TP, TN, FP, FN

### app.py

Flask 服务器，提供 3 个端点：

- `GET /` - 返回 index.html 前端
- `GET /progress` - 返回当前进度消息
- `POST /run` - 执行完整的审计流程

## 如何混入正常函数进行测试？

**步骤**：

1. 在 `benchmark_generator.py` 的采样逻辑中添加正常函数：

```python
# 例如在 extract_sample_from_benchmark 中
normal_funcs = [
    {
        'tcName': 'SAFE_TEST001',
        'URL': 'http://example.com/safe1',
        'tcType': 'SERVLET',
        'vuln_type': 'normal',
        'has_vulnerability': False  # ← 标记为正常
    },
    # ... 更多正常函数
]
samples = random.sample(tests, min(sample_size, len(tests)))
samples.extend(normal_funcs)  # 混入正常函数
random.shuffle(samples)
```

2. 重新运行审计，系统会自动计算混合数据的准确率

## 输出文件说明

### benchmark_sample.csv
抽取的样本数据，包含 ground truth 和漏洞类型标签

### benchmark_sample_results.csv
审计结果，包含以下列：
- `tcName`: 测试用例名
- `URL`: 代码地址
- `ground_truth`: 真实标签（1=有漏洞，0=无漏洞）
- `vuln_type`: 漏洞类型
- `llm_prediction`: LLM 预测（true/false/null）
- `reply`: LLM 完整回复
- `timestamp`: 处理时间

## 提示

1. **API 配额**：DeepSeek API 有速率限制，代码已添加 1 秒延迟
2. **隐私保护**：向 LLM 隐藏了 ground truth，保证评估的公平性
3. **本地运行**：Flask 运行在 `127.0.0.1:5000`，仅本地访问

## 示例输出

```
=== 审计准确率统计 ===
总样本数: 50
有效预测数: 50
正确预测数: 45
准确率 (Accuracy): 90.00%

混淆矩阵:
  真阳性 (TP): 43
  真阴性 (TN): 2
  假阳性 (FP): 3
  假阴性 (FN): 2

性能指标:
  精确率 (Precision): 93.48%
  召回率 (Recall): 95.56%
  F1分数: 94.51%
```

## 许可证

自由使用

## 联系方式

如有问题，请提出 issue 或 PR。
