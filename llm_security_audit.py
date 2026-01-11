import json, time, pandas as pd
from config import DEEPSEEK_API_KEY
import os
from openai import OpenAI
from datetime import datetime
from benchmark_generator import extract_sample_from_benchmark

# openai.api_key = OPENAI_API_KEY
# DEEPSEEK_API_KEY

prompt = """你是一名代码审计专家。  
下面给出 Java 函数源码，请判断是否存在安全漏洞（如注入、越界、XXE 等）。  
按 JSON 回答：{"vuln": true/false, "type": "OWASP Top10 类别", "reason": "一句话原因", "patch": "给出修改后代码片段"}  """


def audit_with_llm(samples_csv='benchmark_sample.csv', output_results_csv='benchmark_sample_results.csv'):
    """
    调用LLM对CSV中的样本进行审计，保存结果
    
    参数:
        samples_csv (str): 包含样本的CSV文件
        output_results_csv (str): 输出结果的CSV文件名
    
    返回:
        list: 包含LLM回复的结果列表
    """
    
    # 读取样本CSV（包含ground truth标签）
    df_samples = pd.read_csv(samples_csv, encoding='utf-8')
    print(f"读取 {len(df_samples)} 条样本")
    
    # 调用LLM获取回复
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com")
    
    results = []
    for idx, row in df_samples.iterrows():
        print(f"处理第 {idx+1}/{len(df_samples)} 条: {row['tcName']}")
        
        # 只发送tcName、URL、tcType给LLM，不发送ground truth标签
        src = f"URL='{row['URL']}' tcName='{row['tcName']}' tcType='{row['tcType']}'"
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt + src}],
                temperature=0,
                stream=False
            )
            
            reply_content = response.choices[0].message.content
            
            # 尝试解析JSON回复
            llm_has_vuln = None
            try:
                reply_json = json.loads(reply_content)
                llm_has_vuln = reply_json.get('vuln', None)
            except json.JSONDecodeError:
                reply_json = {"raw_reply": reply_content}
            
            result = {
                'tcName': row['tcName'],
                'URL': row['URL'],
                'ground_truth': row.get('has_vulnerability', None),  # 真实标签
                'vuln_type': row.get('vuln_type', 'unknown'),  # 漏洞类型
                'llm_prediction': llm_has_vuln,  # LLM预测
                'reply': reply_content,
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
            
            # 避免速率限制
            time.sleep(1)
            
        except Exception as e:
            print(f"错误: {e}")
            result = {
                'tcName': row['tcName'],
                'URL': row['URL'],
                'ground_truth': row.get('has_vulnerability', None),
                'vuln_type': row.get('vuln_type', 'unknown'),
                'llm_prediction': None,
                'reply': f"Error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
    
    # 保存结果
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_results_csv, index=False, encoding='utf-8')
    print(f"结果已保存到 {output_results_csv}")
    
    return results


def calculate_accuracy(results_csv='benchmark_sample_results.csv'):
    """
    计算LLM审计的准确率
    
    参数:
        results_csv (str): 包含审计结果的CSV文件
    
    返回:
        dict: 包含准确率统计的字典
    """
    df = pd.read_csv(results_csv, encoding='utf-8')
    
    # 过滤掉预测失败的样本
    df_valid = df[df['llm_prediction'].notna()].copy()
    
    if len(df_valid) == 0:
        print("没有有效的预测结果")
        return {}
    
    # 计算准确率
    correct = (df_valid['ground_truth'] == df_valid['llm_prediction']).sum()
    total = len(df_valid)
    accuracy = correct / total if total > 0 else 0
    
    # 计算混淆矩阵
    true_positive = ((df_valid['ground_truth'] == True) & (df_valid['llm_prediction'] == True)).sum()
    true_negative = ((df_valid['ground_truth'] == False) & (df_valid['llm_prediction'] == False)).sum()
    false_positive = ((df_valid['ground_truth'] == False) & (df_valid['llm_prediction'] == True)).sum()
    false_negative = ((df_valid['ground_truth'] == True) & (df_valid['llm_prediction'] == False)).sum()
    
    # 计算精确率和召回率
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    stats = {
        'total_samples': len(df),
        'valid_predictions': total,
        'correct': correct,
        'accuracy': accuracy,
        'true_positive': true_positive,
        'true_negative': true_negative,
        'false_positive': false_positive,
        'false_negative': false_negative,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }
    
    print("\n=== 审计准确率统计 ===")
    print(f"总样本数: {stats['total_samples']}")
    print(f"有效预测数: {stats['valid_predictions']}")
    print(f"正确预测数: {stats['correct']}")
    print(f"准确率 (Accuracy): {stats['accuracy']:.2%}")
    print(f"\n混淆矩阵:")
    print(f"  真阳性 (TP): {stats['true_positive']}")
    print(f"  真阴性 (TN): {stats['true_negative']}")
    print(f"  假阳性 (FP): {stats['false_positive']}")
    print(f"  假阴性 (FN): {stats['false_negative']}")
    print(f"\n性能指标:")
    print(f"  精确率 (Precision): {stats['precision']:.2%}")
    print(f"  召回率 (Recall): {stats['recall']:.2%}")
    print(f"  F1分数: {stats['f1_score']:.2%}")
    
    return stats


# 调用函数
if __name__ == "__main__":
    # 先生成测试集样本
    extract_sample_from_benchmark(sample_size=50, output_csv='benchmark_sample.csv')
    # 再调用LLM进行审计
    results = audit_with_llm('benchmark_sample.csv', 'benchmark_sample_results.csv')
    # 计算准确率
    calculate_accuracy('benchmark_sample_results.csv')