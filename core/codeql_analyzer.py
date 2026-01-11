import subprocess
import json
import pandas as pd
import os
from datetime import datetime


def run_codeql_analysis(database_path: str, output_json: str = 'data/output/codeql_results.json') -> dict:
    """
    运行 CodeQL 默认安全查询套件
    
    参数:
        database_path (str): CodeQL 数据库路径
        output_json (str): 输出 JSON 文件名
    
    返回:
        dict: 分析结果
    """
    
    if not os.path.exists(database_path):
        raise FileNotFoundError(f"CodeQL 数据库不存在: {database_path}")
    
    print(f"开始 CodeQL 分析: {database_path}")
    
    try:
        # 运行 CodeQL 默认安全查询
        # 使用 security-and-quality.qls 包含所有默认安全检查
        cmd = [
            'codeql', 'database', 'analyze', database_path,
            'security-and-quality.qls',
            '--format=json',
            f'--output={output_json}',
            '--download'  # 自动下载必要的查询
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"CodeQL 分析出错: {result.stderr}")
            return {'error': result.stderr}
        
        print(f"CodeQL 分析完成，结果保存到 {output_json}")
        
        # 解析结果
        if os.path.exists(output_json):
            with open(output_json, 'r') as f:
                results = json.load(f)
            return results
        
        return {'status': 'completed'}
        
    except FileNotFoundError:
        raise RuntimeError("CodeQL 未安装或不在 PATH 中，请先安装 CodeQL")
    except Exception as e:
        print(f"错误: {e}")
        return {'error': str(e)}


def compare_llm_vs_codeql(samples_csv: str, llm_results_csv: str, 
                          codeql_json: str) -> pd.DataFrame:
    """
    对比 LLM 审计结果和 CodeQL 分析结果
    
    参数:
        samples_csv (str): 样本 CSV 文件
        llm_results_csv (str): LLM 审计结果 CSV
        codeql_json (str): CodeQL 分析结果 JSON
    
    返回:
        pd.DataFrame: 对比结果
    """
    
    # 读取 LLM 结果
    if not os.path.exists(llm_results_csv):
        print(f"警告: LLM 结果文件不存在: {llm_results_csv}")
        df_llm = pd.DataFrame()
    else:
        df_llm = pd.read_csv(llm_results_csv, encoding='utf-8')
    
    # 读取 CodeQL 结果
    codeql_findings = []
    if os.path.exists(codeql_json):
        try:
            with open(codeql_json, 'r') as f:
                codeql_data = json.load(f)
            
            # 提取漏洞
            if isinstance(codeql_data, dict):
                if 'runs' in codeql_data:
                    for run in codeql_data['runs']:
                        if 'results' in run:
                            for result in run['results']:
                                finding = {
                                    'rule_id': result.get('ruleId', 'unknown'),
                                    'message': result.get('message', {}).get('text', ''),
                                    'severity': result.get('level', 'unknown'),
                                    'location': result.get('locations', [{}])[0].get('physicalLocation', {}).get('artifactLocation', {}).get('uri', '')
                                }
                                codeql_findings.append(finding)
        except json.JSONDecodeError:
            print("警告: CodeQL 结果 JSON 解析失败")
    
    print(f"CodeQL 发现 {len(codeql_findings)} 个漏洞")
    
    # 汇总对比结果
    comparison = {
        'timestamp': datetime.now().isoformat(),
        'total_samples': len(df_llm) if not df_llm.empty else 0,
        'llm_detections': (df_llm['llm_prediction'] == True).sum() if not df_llm.empty else 0,
        'codeql_findings': len(codeql_findings),
        'codeql_details': codeql_findings[:20]  # 保存前 20 个
    }
    
    return comparison


def generate_comparison_report(samples_csv: str, llm_results_csv: str, 
                               codeql_json: str, output_csv: str = 'data/output/comparison_report.csv') -> None:
    """
    生成 LLM vs CodeQL 对比报告
    
    参数:
        samples_csv (str): 样本 CSV
        llm_results_csv (str): LLM 结果 CSV
        codeql_json (str): CodeQL 结果 JSON
        output_csv (str): 输出报告文件名
    """
    
    # 读取数据
    df_samples = pd.read_csv(samples_csv, encoding='utf-8') if os.path.exists(samples_csv) else pd.DataFrame()
    df_llm = pd.read_csv(llm_results_csv, encoding='utf-8') if os.path.exists(llm_results_csv) else pd.DataFrame()
    
    codeql_findings = []
    if os.path.exists(codeql_json):
        try:
            with open(codeql_json, 'r') as f:
                codeql_data = json.load(f)
            if isinstance(codeql_data, dict) and 'runs' in codeql_data:
                for run in codeql_data['runs']:
                    if 'results' in run:
                        codeql_findings.extend(run['results'])
        except:
            pass
    
    # 合并结果
    if not df_llm.empty:
        report_data = []
        for idx, row in df_llm.iterrows():
            report_row = {
                'tcName': row.get('tcName', ''),
                'URL': row.get('URL', ''),
                'ground_truth': row.get('ground_truth', ''),
                'llm_prediction': row.get('llm_prediction', ''),
                'llm_correct': row.get('ground_truth') == row.get('llm_prediction'),
                'codeql_findings_count': len(codeql_findings),  # 简化版
                'timestamp': datetime.now().isoformat()
            }
            report_data.append(report_row)
        
        df_report = pd.DataFrame(report_data)
        df_report.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"对比报告已保存到 {output_csv}")
        
        # 打印统计
        print("\n=== LLM vs CodeQL 对比 ===")
        print(f"LLM 检测出漏洞: {(df_llm['llm_prediction'] == True).sum()} 个")
        print(f"CodeQL 检测出漏洞: {len(codeql_findings)} 个")
        print(f"LLM 准确率: {(df_llm['llm_prediction'] == df_llm['ground_truth']).sum() / len(df_llm) * 100:.2f}%")


if __name__ == "__main__":
    # 使用示例
    # 假设已有 CodeQL 数据库
    # codeql_db = "path/to/codeql/database"
    # run_codeql_analysis(codeql_db)
    # compare_llm_vs_codeql('benchmark_sample.csv', 'benchmark_sample_results.csv', 'codeql_results.json')
    print("CodeQL 分析模块已加载")
