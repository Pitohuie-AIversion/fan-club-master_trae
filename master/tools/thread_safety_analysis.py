#!/usr/bin/env python3
"""
Fan Club MkIV 多线程安全分析工具
针对上位机(Python)和下位机(C++)代码进行线程安全检测
"""

import re
import os
import json
from typing import List, Dict, Any

class ThreadSafetyAnalyzer:
    """多线程安全分析器"""
    
    def __init__(self):
        self.issues = []
        
        # C/C++ 线程安全问题模式
        self.cpp_thread_patterns = [
            {
                'pattern': r'Thread\s+\w+\s*\(',
                'type': 'thread_creation',
                'severity': 'INFO',
                'description': '线程创建，需要确保线程安全'
            },
            {
                'pattern': r'Mutex\s+\w+',
                'type': 'mutex_usage',
                'severity': 'INFO',
                'description': '互斥锁使用，需要检查是否正确锁定'
            },
            {
                'pattern': r'\.lock\s*\(',
                'type': 'locking',
                'severity': 'MEDIUM',
                'description': '互斥锁锁定，需要确保有对应的解锁'
            },
            {
                'pattern': r'\.unlock\s*\(',
                'type': 'unlocking',
                'severity': 'MEDIUM',
                'description': '互斥锁解锁，需要确保之前已锁定'
            },
            {
                'pattern': r'while\s*\(\s*true\s*\)',
                'type': 'infinite_loop',
                'severity': 'HIGH',
                'description': '无限循环，需要确保有退出条件和线程安全'
            },
            {
                'pattern': r'while\s*\([^)]*\)\s*{[^}]*Thread::wait',
                'type': 'polling_loop',
                'severity': 'MEDIUM',
                'description': '轮询循环，可能导致CPU占用过高'
            },
            {
                'pattern': r'flag\s*=\s*(true|false)',
                'type': 'flag_modification',
                'severity': 'HIGH',
                'description': '标志位修改，需要确保线程间同步'
            },
            {
                'pattern': r'if\s*\([^)]*flag[^)]*\)',
                'type': 'flag_check',
                'severity': 'HIGH',
                'description': '标志位检查，需要确保线程安全'
            }
        ]
        
        # Python 线程安全问题模式
        self.python_thread_patterns = [
            {
                'pattern': r'threading\.Thread\s*\(',
                'type': 'thread_creation',
                'severity': 'INFO',
                'description': '线程创建，需要确保线程安全'
            },
            {
                'pattern': r'multiprocessing\.Process\s*\(',
                'type': 'process_creation',
                'severity': 'INFO',
                'description': '进程创建，需要确保进程间通信安全'
            },
            {
                'pattern': r'Queue\s*\(',
                'type': 'queue_usage',
                'severity': 'MEDIUM',
                'description': '队列使用，需要确保线程安全的put/get'
            },
            {
                'pattern': r'\.put\s*\(',
                'type': 'queue_put',
                'severity': 'MEDIUM',
                'description': '队列放入，需要确保不会阻塞'
            },
            {
                'pattern': r'\.get\s*\(',
                'type': 'queue_get',
                'severity': 'MEDIUM',
                'description': '队列取出，需要确保超时处理'
            },
            {
                'pattern': r'Pipe\s*\(',
                'type': 'pipe_usage',
                'severity': 'MEDIUM',
                'description': '管道使用，需要确保正确关闭'
            },
            {
                'pattern': r'\.send\s*\(',
                'type': 'pipe_send',
                'severity': 'MEDIUM',
                'description': '管道发送，需要确保接收端存在'
            },
            {
                'pattern': r'\.recv\s*\(',
                'type': 'pipe_receive',
                'severity': 'MEDIUM',
                'description': '管道接收，需要确保超时处理'
            }
        ]
        
        # 共享变量访问模式
        self.shared_variable_patterns = [
            {
                'pattern': r'self\.\w+\s*=',
                'type': 'instance_variable_write',
                'severity': 'HIGH',
                'description': '实例变量写入，需要确保线程安全'
            },
            {
                'pattern': r'global\s+\w+',
                'type': 'global_variable',
                'severity': 'CRITICAL',
                'description': '全局变量使用，需要确保线程安全'
            },
            {
                'pattern': r'static\s+\w+',
                'type': 'static_variable',
                'severity': 'CRITICAL',
                'description': '静态变量使用，需要确保线程安全'
            }
        ]

    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """分析单个文件"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # 根据文件类型选择模式
            if file_ext in ['.cpp', '.c', '.h', '.hpp']:
                patterns = self.cpp_thread_patterns + self.shared_variable_patterns
            elif file_ext in ['.py']:
                patterns = self.python_thread_patterns + self.shared_variable_patterns
            else:
                patterns = []
            
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # 跳过注释和空行
                if not line_stripped or line_stripped.startswith('//') or line_stripped.startswith('#'):
                    continue
                
                for pattern_info in patterns:
                    if re.search(pattern_info['pattern'], line_stripped, re.IGNORECASE):
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'column': line.find(line_stripped) + 1,
                            'type': pattern_info['type'],
                            'severity': pattern_info['severity'],
                            'description': pattern_info['description'],
                            'code': line_stripped[:100]
                        })
                        
        except Exception as e:
            print(f"分析文件 {file_path} 时出错: {e}")
            
        return issues

    def analyze_race_conditions(self, file_path: str) -> List[Dict[str, Any]]:
        """分析竞态条件"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # 查找可能的竞态条件模式
            race_patterns = [
                {
                    'pattern': r'(\w+)\s*=\s*([^;]+);\s*.*?\1\s*=',
                    'type': 'read_modify_write',
                    'severity': 'HIGH',
                    'description': '读-修改-写操作，可能存在竞态条件'
                },
                {
                    'pattern': r'if\s*\([^)]*(\w+)[^)]*\)\s*{[^}]*\1\s*=',
                    'type': 'check_then_act',
                    'severity': 'HIGH',
                    'description': '检查-然后-行动模式，可能存在竞态条件'
                }
            ]
            
            for pattern_info in race_patterns:
                matches = re.finditer(pattern_info['pattern'], content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        'file': file_path,
                        'line': line_num,
                        'type': pattern_info['type'],
                        'severity': pattern_info['severity'],
                        'description': pattern_info['description'],
                        'code': match.group(0)[:100]
                    })
                    
        except Exception as e:
            print(f"分析竞态条件时出错: {e}")
            
        return issues

    def analyze_deadlock_potential(self, file_path: str) -> List[Dict[str, Any]]:
        """分析死锁可能性"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # 查找可能的死锁模式
            deadlock_patterns = [
                {
                    'pattern': r'\.lock\s*\([^)]*\).*?\.lock\s*\([^)]*\)',
                    'type': 'multiple_locks',
                    'severity': 'HIGH',
                    'description': '多个锁的获取，可能存在死锁风险'
                },
                {
                    'pattern': r'\.lock\s*\([^)]*\).*?while\s*\([^)]*\)',
                    'type': 'lock_with_loop',
                    'severity': 'MEDIUM',
                    'description': '在循环中获取锁，可能导致性能问题'
                }
            ]
            
            for pattern_info in deadlock_patterns:
                matches = re.finditer(pattern_info['pattern'], content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        'file': file_path,
                        'line': line_num,
                        'type': pattern_info['type'],
                        'severity': pattern_info['severity'],
                        'description': pattern_info['description'],
                        'code': match.group(0)[:100]
                    })
                    
        except Exception as e:
            print(f"分析死锁可能性时出错: {e}")
            
        return issues

    def analyze_thread_safety_violations(self, file_path: str) -> List[Dict[str, Any]]:
        """分析线程安全违规"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            # 查找线程安全违规
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # 检查未受保护的共享变量访问
                if re.search(r'self\.\w+.*=.*self\.\w+', line_stripped):
                    issues.append({
                        'file': file_path,
                        'line': line_num,
                        'type': 'unprotected_shared_access',
                        'severity': 'HIGH',
                        'description': '未受保护的共享变量访问，可能导致竞态条件',
                        'code': line_stripped[:100]
                    })
                
                # 检查非线程安全的集合操作
                if re.search(r'\.append\(|\.remove\(|\.pop\(', line_stripped):
                    issues.append({
                        'file': file_path,
                        'line': line_num,
                        'type': 'non_thread_safe_collection',
                        'severity': 'MEDIUM',
                        'description': '非线程安全的集合操作，可能导致数据竞争',
                        'code': line_stripped[:100]
                    })
                    
        except Exception as e:
            print(f"分析线程安全违规时出错: {e}")
            
        return issues

    def generate_report(self, target_files: List[str]) -> Dict[str, Any]:
        """生成完整报告"""
        all_issues = []
        
        for file_path in target_files:
            if os.path.exists(file_path):
                print(f"分析文件: {file_path}")
                
                # 基础分析
                issues = self.analyze_file(file_path)
                all_issues.extend(issues)
                
                # 高级分析
                race_issues = self.analyze_race_conditions(file_path)
                all_issues.extend(race_issues)
                
                deadlock_issues = self.analyze_deadlock_potential(file_path)
                all_issues.extend(deadlock_issues)
                
                safety_issues = self.analyze_thread_safety_violations(file_path)
                all_issues.extend(safety_issues)
            else:
                print(f"文件不存在: {file_path}")
        
        # 分类统计
        severity_counts = {}
        type_counts = {}
        
        for issue in all_issues:
            severity = issue['severity']
            issue_type = issue['type']
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        return {
            'summary': {
                'total_issues': len(all_issues),
                'severity_counts': severity_counts,
                'type_counts': type_counts
            },
            'issues': all_issues
        }

def main():
    """主函数"""
    analyzer = ThreadSafetyAnalyzer()
    
    # 目标文件
    target_files = [
        # Master上位机 (Python)
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/master/main.py",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/master/fc/backend/communicator.py",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/master/fc/backend/mkiii/FCCommunicator.py",
        
        # Slave下位机 (C++)
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f439 chasemode/slave/main.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f439 chasemode/slave/Communicator.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f439 chasemode/slave/Processor.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f439 chasemode/slave/Fan.cpp"
    ]
    
    # 生成报告
    report = analyzer.generate_report(target_files)
    
    # 保存报告
    report_file = "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/master/tools/thread_safety_report.json"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 打印摘要
    print("\n" + "="*60)
    print("多线程安全分析报告")
    print("="*60)
    print(f"总问题数: {report['summary']['total_issues']}")
    print("\n严重级别统计:")
    for severity, count in report['summary']['severity_counts'].items():
        print(f"  {severity}: {count}")
    print("\n问题类型统计:")
    for issue_type, count in report['summary']['type_counts'].items():
        print(f"  {issue_type}: {count}")
    
    # 显示关键问题
    high_issues = [issue for issue in report['issues'] if issue['severity'] in ['HIGH', 'CRITICAL']]
    if high_issues:
        print("\n高严重级别问题 (HIGH/CRITICAL):")
        for issue in high_issues[:5]:  # 显示前5个
            print(f"\n文件: {issue['file']}")
            print(f"行号: {issue['line']}")
            print(f"类型: {issue['type']}")
            print(f"描述: {issue['description']}")
            print(f"代码: {issue['code']}")
    
    print(f"\n详细报告已保存到: {report_file}")
    return report

if __name__ == "__main__":
    main()