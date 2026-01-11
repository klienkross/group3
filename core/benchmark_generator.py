import pandas as pd
import xml.etree.ElementTree as ET
import random
from datetime import datetime


def extract_sample_from_benchmark(sample_size=50, output_csv='data/output/benchmark_sample.csv'):
    """
    从benchmark XML文件随机抽取样本，保存为CSV
    
    参数:
        sample_size (int): 要抽取的样本数量，默认50
        output_csv (str): 输出CSV文件名
    
    返回:
        pd.DataFrame: 包含样本数据的DataFrame
    """
    
    # 1. 解析XML文件
    xml_file = 'data/input/benchmark-crawler-http.xml'
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # 2. 提取所有benchmarkTest
    tests = []
    for test in root.findall('benchmarkTest'):
        url = test.get('URL')
        
        # 从URL提取漏洞类型作为ground truth标签
        # URL格式: https://localhost:8443/benchmark/{vuln-type}/BenchmarkTest...
        vuln_type = 'unknown'
        if '/benchmark/' in url:
            parts = url.split('/benchmark/')[1].split('/')
            if len(parts) > 0:
                vuln_type = parts[0]  # 例如: pathtraver-00, sqli-00, cmdi-00
        
        # 标注是否为漏洞（含有漏洞类型的被认为是异常样本）
        # 正常样本可以后续手动添加，这里所有样本都标记为有漏洞
        has_vulnerability = True
        
        test_data = {
            'tcName': test.get('tcName'),
            'URL': test.get('URL'),
            'tcType': test.get('tcType'),
            'vuln_type': vuln_type,  # 漏洞类型（不给LLM看）
            'has_vulnerability': has_vulnerability  # True=异常, False=正常（不给LLM看）
        }
        tests.append(test_data)
    
    print(f"总共找到 {len(tests)} 条测试用例")
    
    # 3. 随机打乱并抽取样本
    samples = random.sample(tests, min(sample_size, len(tests)))
    print(f"随机抽取 {len(samples)} 条样本")
    
    # 4. 保存为CSV
    df_samples = pd.DataFrame(samples)
    df_samples.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"样本已保存到 {output_csv}")
    
    return df_samples


if __name__ == "__main__":
    extract_sample_from_benchmark(sample_size=50, output_csv='data/output/benchmark_sample.csv')
