from flask import Flask, render_template, jsonify
from benchmark_generator import extract_sample_from_benchmark
from llm_security_audit import audit_with_llm, calculate_accuracy
import pandas as pd
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_pipeline():
    try:
        # 1) 生成测试集
        extract_sample_from_benchmark(sample_size=50, output_csv='benchmark_sample.csv')
        # 2) 运行LLM审计
        audit_with_llm('benchmark_sample.csv', 'benchmark_sample_results.csv')
        # 3) 计算准确率
        stats = calculate_accuracy('benchmark_sample_results.csv')
        
        # 返回少量结果预览
        preview = []
        if os.path.exists('benchmark_sample_results.csv'):
            df = pd.read_csv('benchmark_sample_results.csv')
            preview = df.head(5).to_dict(orient='records')
        
        return jsonify({
            'ok': True,
            'stats': stats,
            'preview': preview
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # 默认在 http://127.0.0.1:5000
    app.run(host='127.0.0.1', port=5000, debug=True)
