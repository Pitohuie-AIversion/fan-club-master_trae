#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tach信号诊断工具
用于诊断和分析风机转速反馈信号的问题
"""

import time
import json
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import os

@dataclass
class TachDiagnosticResult:
    """Tach诊断结果"""
    fan_id: str
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    recommendation: str
    data_points: List[Dict]
    
class TachSignalDiagnostics:
    """Tach信号诊断器"""
    
    def __init__(self):
        self.diagnostic_rules = {
            'no_signal': self._check_no_signal,
            'erratic_rpm': self._check_erratic_rpm,
            'stuck_rpm': self._check_stuck_rpm,
            'low_signal_quality': self._check_low_signal_quality,
            'rpm_dc_mismatch': self._check_rpm_dc_mismatch,
            'timeout_issues': self._check_timeout_issues,
            'pulse_count_anomaly': self._check_pulse_count_anomaly
        }
        
        # 诊断阈值
        self.thresholds = {
            'min_rpm_variance': 10,      # 最小RPM变化
            'max_rpm_variance': 1000,    # 最大RPM变化
            'min_signal_quality': 0.7,   # 最小信号质量
            'max_timeout_rate': 0.1,     # 最大超时率
            'rpm_dc_correlation': 0.8,   # RPM与占空比相关性
            'stuck_rpm_duration': 10,    # 卡死RPM持续时间(秒)
        }
        
    def diagnose_data(self, data: List[Dict]) -> List[TachDiagnosticResult]:
        """诊断数据"""
        results = []
        
        # 按风机分组数据
        fan_data = self._group_by_fan(data)
        
        # 对每个风机运行诊断
        for fan_id, fan_readings in fan_data.items():
            for rule_name, rule_func in self.diagnostic_rules.items():
                try:
                    result = rule_func(fan_id, fan_readings)
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"诊断规则 {rule_name} 执行失败: {e}")
                    
        return results
        
    def _group_by_fan(self, data: List[Dict]) -> Dict[str, List[Dict]]:
        """按风机分组数据"""
        fan_data = defaultdict(list)
        
        for reading in data:
            if 'slave_id' in reading and 'fan_id' in reading:
                fan_key = f"S{reading['slave_id']}F{reading['fan_id']}"
            elif 'fan_id' in reading:
                fan_key = f"F{reading['fan_id']}"
            else:
                fan_key = "Unknown"
                
            fan_data[fan_key].append(reading)
            
        return dict(fan_data)
        
    def _check_no_signal(self, fan_id: str, readings: List[Dict]) -> Optional[TachDiagnosticResult]:
        """检查无信号问题"""
        if not readings:
            return TachDiagnosticResult(
                fan_id=fan_id,
                issue_type="no_signal",
                severity="critical",
                description="完全没有接收到tach信号",
                recommendation="检查tach信号线连接和风机电源",
                data_points=[]
            )
            
        # 检查是否所有RPM都为0
        rpms = [r.get('rpm', 0) for r in readings]
        if all(rpm == 0 for rpm in rpms):
            return TachDiagnosticResult(
                fan_id=fan_id,
                issue_type="no_signal",
                severity="high",
                description="所有RPM读数为0，可能tach信号线断开",
                recommendation="检查tach信号线连接和风机运行状态",
                data_points=readings[-10:]  # 最近10个读数
            )
            
        return None
        
    def _check_erratic_rpm(self, fan_id: str, readings: List[Dict]) -> Optional[TachDiagnosticResult]:
        """检查RPM波动异常"""
        if len(readings) < 10:
            return None
            
        rpms = [r.get('rpm', 0) for r in readings if r.get('rpm', 0) > 0]
        if len(rpms) < 5:
            return None
            
        # 计算RPM变化率
        rpm_changes = [abs(rpms[i] - rpms[i-1]) for i in range(1, len(rpms))]
        avg_change = np.mean(rpm_changes)
        max_change = max(rpm_changes)
        
        if max_change > self.thresholds['max_rpm_variance']:
            return TachDiagnosticResult(
                fan_id=fan_id,
                issue_type="erratic_rpm",
                severity="medium",
                description=f"RPM波动异常，最大变化: {max_change:.0f} RPM",
                recommendation="检查风机机械状态和tach信号稳定性",
                data_points=readings[-20:]
            )
            
        return None
        
    def _check_stuck_rpm(self, fan_id: str, readings: List[Dict]) -> Optional[TachDiagnosticResult]:
        """检查RPM卡死"""
        if len(readings) < 20:
            return None
            
        rpms = [r.get('rpm', 0) for r in readings]
        timestamps = [r.get('timestamp', 0) for r in readings]
        
        # 查找连续相同RPM的最长时间
        max_stuck_duration = 0
        current_stuck_duration = 0
        current_rpm = None
        start_time = None
        
        for i, (rpm, timestamp) in enumerate(zip(rpms, timestamps)):
            if rpm == current_rpm and rpm > 0:
                if start_time is None:
                    start_time = timestamp
                current_stuck_duration = timestamp - start_time
            else:
                max_stuck_duration = max(max_stuck_duration, current_stuck_duration)
                current_rpm = rpm
                start_time = timestamp
                current_stuck_duration = 0
                
        max_stuck_duration = max(max_stuck_duration, current_stuck_duration)
        
        if max_stuck_duration > self.thresholds['stuck_rpm_duration']:
            return TachDiagnosticResult(
                fan_id=fan_id,
                issue_type="stuck_rpm",
                severity="high",
                description=f"RPM卡死 {max_stuck_duration:.1f} 秒，值: {current_rpm}",
                recommendation="检查风机是否卡死或tach信号处理电路",
                data_points=readings[-15:]
            )
            
        return None
        
    def _check_low_signal_quality(self, fan_id: str, readings: List[Dict]) -> Optional[TachDiagnosticResult]:
        """检查信号质量低"""
        qualities = [r.get('signal_quality', 1.0) for r in readings]
        if not qualities:
            return None
            
        avg_quality = np.mean(qualities)
        min_quality = min(qualities)
        
        if avg_quality < self.thresholds['min_signal_quality']:
            return TachDiagnosticResult(
                fan_id=fan_id,
                issue_type="low_signal_quality",
                severity="medium",
                description=f"信号质量低，平均: {avg_quality:.3f}, 最低: {min_quality:.3f}",
                recommendation="检查tach信号线屏蔽和接地",
                data_points=readings[-10:]
            )
            
        return None
        
    def _check_rpm_dc_mismatch(self, fan_id: str, readings: List[Dict]) -> Optional[TachDiagnosticResult]:
        """检查RPM与占空比不匹配"""
        if len(readings) < 10:
            return None
            
        rpms = [r.get('rpm', 0) for r in readings if r.get('rpm', 0) > 0]
        dcs = [r.get('duty_cycle', 0) for r in readings if r.get('rpm', 0) > 0]
        
        if len(rpms) < 5 or len(dcs) < 5:
            return None
            
        # 计算相关性
        correlation = np.corrcoef(rpms, dcs)[0, 1] if len(rpms) > 1 else 1.0
        
        if abs(correlation) < self.thresholds['rpm_dc_correlation']:
            return TachDiagnosticResult(
                fan_id=fan_id,
                issue_type="rpm_dc_mismatch",
                severity="medium",
                description=f"RPM与占空比相关性低: {correlation:.3f}",
                recommendation="检查风机响应特性和控制回路",
                data_points=readings[-15:]
            )
            
        return None
        
    def _check_timeout_issues(self, fan_id: str, readings: List[Dict]) -> Optional[TachDiagnosticResult]:
        """检查超时问题"""
        timeouts = [r.get('timeout_occurred', False) for r in readings]
        if not timeouts:
            return None
            
        timeout_rate = sum(timeouts) / len(timeouts)
        
        if timeout_rate > self.thresholds['max_timeout_rate']:
            return TachDiagnosticResult(
                fan_id=fan_id,
                issue_type="timeout_issues",
                severity="high",
                description=f"超时率过高: {timeout_rate:.3f}",
                recommendation="检查tach信号频率和计数器配置",
                data_points=[r for r in readings if r.get('timeout_occurred', False)][-5:]
            )
            
        return None
        
    def _check_pulse_count_anomaly(self, fan_id: str, readings: List[Dict]) -> Optional[TachDiagnosticResult]:
        """检查脉冲计数异常"""
        pulse_counts = [r.get('pulse_count', 0) for r in readings]
        if not pulse_counts:
            return None
            
        # 检查脉冲计数的一致性
        unique_counts = set(pulse_counts)
        if len(unique_counts) > 5:  # 脉冲计数变化过多
            return TachDiagnosticResult(
                fan_id=fan_id,
                issue_type="pulse_count_anomaly",
                severity="low",
                description=f"脉冲计数变化异常，发现 {len(unique_counts)} 种不同计数",
                recommendation="检查tach信号稳定性和噪声",
                data_points=readings[-10:]
            )
            
        return None
        
    def generate_report(self, results: List[TachDiagnosticResult]) -> str:
        """生成诊断报告"""
        report = ["=== Tach信号诊断报告 ==="]
        report.append(f"诊断时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"发现问题数: {len(results)}")
        report.append("")
        
        # 按严重程度分组
        by_severity = defaultdict(list)
        for result in results:
            by_severity[result.severity].append(result)
            
        severity_order = ['critical', 'high', 'medium', 'low']
        severity_names = {
            'critical': '严重',
            'high': '高',
            'medium': '中等',
            'low': '低'
        }
        
        for severity in severity_order:
            if severity in by_severity:
                report.append(f"=== {severity_names[severity]}严重程度问题 ===")
                for result in by_severity[severity]:
                    report.append(f"风机: {result.fan_id}")
                    report.append(f"问题类型: {result.issue_type}")
                    report.append(f"描述: {result.description}")
                    report.append(f"建议: {result.recommendation}")
                    report.append("")
                    
        # 统计摘要
        report.append("=== 统计摘要 ===")
        issue_types = defaultdict(int)
        for result in results:
            issue_types[result.issue_type] += 1
            
        for issue_type, count in issue_types.items():
            report.append(f"{issue_type}: {count} 个风机")
            
        return "\n".join(report)
        
    def plot_diagnostic_summary(self, results: List[TachDiagnosticResult]):
        """绘制诊断摘要图表"""
        if not results:
            print("没有诊断结果可绘制")
            return
            
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 按问题类型统计
        issue_types = defaultdict(int)
        for result in results:
            issue_types[result.issue_type] += 1
            
        if issue_types:
            ax1.pie(issue_types.values(), labels=issue_types.keys(), autopct='%1.1f%%')
            ax1.set_title('问题类型分布')
            
        # 按严重程度统计
        severities = defaultdict(int)
        for result in results:
            severities[result.severity] += 1
            
        severity_colors = {
            'critical': 'red',
            'high': 'orange', 
            'medium': 'yellow',
            'low': 'green'
        }
        
        if severities:
            colors = [severity_colors.get(sev, 'gray') for sev in severities.keys()]
            ax2.bar(severities.keys(), severities.values(), color=colors)
            ax2.set_title('严重程度分布')
            ax2.set_ylabel('问题数量')
            
        plt.tight_layout()
        plt.show()
        
def load_tach_data(filename: str) -> List[Dict]:
    """加载tach数据"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if 'raw_data' in data:
            return data['raw_data']
        elif isinstance(data, list):
            return data
        else:
            print(f"无法识别的数据格式: {filename}")
            return []
            
    except Exception as e:
        print(f"加载数据失败: {e}")
        return []
        
def main():
    """主函数"""
    print("=== Tach信号诊断工具 ===")
    print("用于诊断风机转速反馈信号问题")
    
    # 查找数据文件
    data_files = [f for f in os.listdir('.') if f.startswith('tach_') and f.endswith('.json')]
    
    if not data_files:
        print("未找到tach数据文件")
        print("请先运行 tach_signal_analyzer.py 或 tach_monitor.py 生成数据")
        return
        
    print(f"\n找到 {len(data_files)} 个数据文件:")
    for i, filename in enumerate(data_files, 1):
        print(f"{i}. {filename}")
        
    try:
        choice = int(input("\n请选择要诊断的文件 (输入序号): ")) - 1
        if 0 <= choice < len(data_files):
            filename = data_files[choice]
        else:
            print("无效选择")
            return
    except ValueError:
        print("无效输入")
        return
        
    # 加载数据
    print(f"\n加载数据文件: {filename}")
    data = load_tach_data(filename)
    
    if not data:
        print("数据加载失败")
        return
        
    print(f"加载了 {len(data)} 条记录")
    
    # 运行诊断
    diagnostics = TachSignalDiagnostics()
    print("\n运行诊断...")
    results = diagnostics.diagnose_data(data)
    
    # 生成报告
    report = diagnostics.generate_report(results)
    print("\n" + report)
    
    # 保存报告
    report_filename = f"tach_diagnostic_report_{int(time.time())}.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n诊断报告已保存到: {report_filename}")
    
    # 绘制图表
    if results:
        try:
            diagnostics.plot_diagnostic_summary(results)
        except Exception as e:
            print(f"绘图失败: {e}")
    else:
        print("\n未发现问题，系统运行正常！")

if __name__ == "__main__":
    main()