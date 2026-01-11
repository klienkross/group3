from flask import Flask, render_template, jsonify
from core.benchmark_generator import extract_sample_from_benchmark
from core.llm_security_audit import audit_with_llm, calculate_accuracy
from core.codeql_analyzer import run_codeql_analysis, compare_llm_vs_codeql, generate_comparison_report
import pandas as pd
import os

app = Flask(__name__)

# 简单的全局进度存储（演示用）
CURRENT_PROGRESS = ""

def set_progress(msg: str):
    global CURRENT_PROGRESS
    CURRENT_PROGRESS = msg

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/progress')
def progress():
    return jsonify({ 'msg': CURRENT_PROGRESS })

@app.route('/run', methods=['POST'])
def run_pipeline():
    try:
        # 1) 生成测试集
        set_progress('开始生成测试集…')
        extract_sample_from_benchmark(sample_size=50, output_csv='data/output/benchmark_sample.csv')
        # 2) 运行LLM审计
        set_progress('开始审计…')
        audit_with_llm('data/output/benchmark_sample.csv', 'data/output/benchmark_sample_results.csv', on_progress=set_progress)
        # 3) 计算准确率
        set_progress('计算准确率…')
        stats = calculate_accuracy('data/output/benchmark_sample_results.csv')
        
        set_progress('完成')
        
        # 返回少量结果预览
        preview = []
        if os.path.exists('data/output/benchmark_sample_results.csv'):
            df = pd.read_csv('data/output/benchmark_sample_results.csv')
            preview = df.head(5).to_dict(orient='records')
        
        return jsonify({
            'ok': True,
            'stats': stats,
            'preview': preview
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/codeql', methods=['POST'])
def run_codeql_comparison():
    """运行 CodeQL 分析并对比 LLM 结果"""
    try:
        set_progress('启动 CodeQL 分析…')
        
        # 尝试从请求中获取数据库路径，默认值也要提供
        database_path = 'codeql-database'  # 用户需要提前创建 CodeQL 数据库
        
        # 检查数据库是否存在
        if not os.path.exists(database_path):
            return jsonify({
                'ok': False,
                'error': f'CodeQL 数据库不存在: {database_path}。请先运行: codeql database create {database_path} --language=java --source-root=<source>'
            }), 400
        
        # 运行 CodeQL 分析
        set_progress('运行 CodeQL 默认查询…')
        codeql_result = run_codeql_analysis(database_path, 'data/output/codeql_results.json')
        
        if 'error' in codeql_result:
            return jsonify({
                'ok': False,
                'error': codeql_result['error']
            }), 500
        
        # 对比 LLM 和 CodeQL 结果
        set_progress('对比分析结果…')
        comparison = compare_llm_vs_codeql(
            'data/output/benchmark_sample.csv',
            'data/output/benchmark_sample_results.csv',
            'data/output/codeql_results.json'
        )
        
        # 生成对比报告
        set_progress('生成对比报告…')
        generate_comparison_report(
            'data/output/benchmark_sample.csv',
            'data/output/benchmark_sample_results.csv',
            'data/output/codeql_results.json',
            'data/output/comparison_report.csv'
        )
        
        set_progress('完成')
        
        return jsonify({
            'ok': True,
            'comparison': comparison,
            'report_file': 'data/output/comparison_report.csv'
        })
        
    except Exception as e:
        set_progress(f'错误: {str(e)}')
        return jsonify({'ok': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # 默认在 http://127.0.0.1:5000
    app.run(host='127.0.0.1', port=5000, debug=True)
