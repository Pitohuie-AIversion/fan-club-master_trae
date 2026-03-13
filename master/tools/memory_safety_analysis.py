#!/usr/bin/env python3
"""
Fan Club MkIV 内存安全分析工具
针对上位机(Python)和下位机(C++)代码进行内存安全检测
"""

import re
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple


class MemorySafetyAnalyzer:
    """内存安全分析器"""

    def __init__(self):
        self.issues = []
        self.critical_patterns = [
            # C/C++ 危险函数模式
            {
                "pattern": r"strcpy\s*\(",
                "type": "buffer_overflow",
                "severity": "CRITICAL",
                "description": "使用不安全的strcpy函数，可能导致缓冲区溢出",
            },
            {
                "pattern": r"sprintf\s*\(",
                "type": "buffer_overflow",
                "severity": "CRITICAL",
                "description": "使用不安全的sprintf函数，可能导致格式化字符串攻击",
            },
            {
                "pattern": r"gets\s*\(",
                "type": "buffer_overflow",
                "severity": "CRITICAL",
                "description": "使用危险的gets函数，已知会导致缓冲区溢出",
            },
            {
                "pattern": r"strcat\s*\(",
                "type": "buffer_overflow",
                "severity": "HIGH",
                "description": "使用不安全的strcat函数，可能导致缓冲区溢出",
            },
            {
                "pattern": r"memcpy\s*\([^,]+,\s*[^,]+,\s*[^)]+\)",
                "type": "buffer_overflow",
                "severity": "HIGH",
                "description": "使用memcpy函数，需要确保目标缓冲区足够大",
            },
            {
                "pattern": r"new\s+\w+\s*\[\s*\]",
                "type": "memory_leak",
                "severity": "MEDIUM",
                "description": "使用new[]分配数组，需要确保有对应的delete[]",
            },
            {
                "pattern": r"malloc\s*\(",
                "type": "memory_leak",
                "severity": "MEDIUM",
                "description": "使用malloc分配内存，需要确保有对应的free",
            },
            {
                "pattern": r"free\s*\(",
                "type": "use_after_free",
                "severity": "HIGH",
                "description": "使用free释放内存，需要确保没有后续使用",
            },
            {
                "pattern": r"delete\s+",
                "type": "use_after_free",
                "severity": "HIGH",
                "description": "使用delete释放内存，需要确保没有后续使用",
            },
        ]

        self.python_patterns = [
            {
                "pattern": r"eval\s*\(",
                "type": "code_injection",
                "severity": "CRITICAL",
                "description": "使用eval函数，可能导致代码注入攻击",
            },
            {
                "pattern": r"exec\s*\(",
                "type": "code_injection",
                "severity": "CRITICAL",
                "description": "使用exec函数，可能导致代码注入攻击",
            },
            {
                "pattern": r"__import__\s*\(",
                "type": "code_injection",
                "severity": "HIGH",
                "description": "动态导入模块，需要验证输入安全性",
            },
            {
                "pattern": r"pickle\.loads?\s*\(",
                "type": "deserialization_attack",
                "severity": "CRITICAL",
                "description": "使用pickle反序列化，可能导致任意代码执行",
            },
            {
                "pattern": r"yaml\.load\s*\(",
                "type": "deserialization_attack",
                "severity": "CRITICAL",
                "description": "使用yaml.load，可能导致任意代码执行",
            },
        ]

        self.array_patterns = [
            {
                "pattern": r"\w+\s*\[\s*\w+\s*\]",
                "type": "array_bounds",
                "severity": "MEDIUM",
                "description": "数组访问，需要确保索引在有效范围内",
            }
        ]

    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """分析单个文件"""
        issues = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            file_ext = Path(file_path).suffix.lower()

            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # 跳过注释和空行
                if (
                    not line_stripped
                    or line_stripped.startswith("//")
                    or line_stripped.startswith("#")
                ):
                    continue

                # 根据文件类型选择模式
                if file_ext in [".cpp", ".c", ".h", ".hpp"]:
                    patterns = self.critical_patterns + self.array_patterns
                elif file_ext in [".py"]:
                    patterns = self.python_patterns
                else:
                    patterns = []

                for pattern_info in patterns:
                    if re.search(pattern_info["pattern"], line_stripped, re.IGNORECASE):
                        issues.append(
                            {
                                "file": file_path,
                                "line": line_num,
                                "column": line.find(line_stripped) + 1,
                                "type": pattern_info["type"],
                                "severity": pattern_info["severity"],
                                "description": pattern_info["description"],
                                "code": line_stripped[:100],  # 限制代码长度
                            }
                        )

        except Exception as e:
            print(f"分析文件 {file_path} 时出错: {e}")

        return issues

    def analyze_buffer_sizes(self, file_path: str) -> List[Dict[str, Any]]:
        """分析缓冲区大小声明"""
        issues = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 查找固定大小的缓冲区声明
            buffer_patterns = [
                r"char\s+(\w+)\s*\[\s*(\d+)\s*\]",  # char buffer[SIZE]
                r"wchar_t\s+(\w+)\s*\[\s*(\d+)\s*\]",  # wchar_t buffer[SIZE]
                r"uint8_t\s+(\w+)\s*\[\s*(\d+)\s*\]",  # uint8_t buffer[SIZE]
                r"\#define\s+(\w+_SIZE|MAX_\w+_LENGTH)\s+(\d+)",  # #define BUFFER_SIZE 256
            ]

            for pattern in buffer_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    var_name = match.group(1)
                    size = int(match.group(2))

                    # 检查小缓冲区
                    if size < 64 and "buffer" in var_name.lower():
                        issues.append(
                            {
                                "file": file_path,
                                "line": content[: match.start()].count("\n") + 1,
                                "type": "small_buffer",
                                "severity": "MEDIUM",
                                "description": f"缓冲区 {var_name} 大小只有 {size} 字节，可能不够用",
                                "code": match.group(0),
                            }
                        )

                    # 检查大缓冲区
                    if size > 4096:
                        issues.append(
                            {
                                "file": file_path,
                                "line": content[: match.start()].count("\n") + 1,
                                "type": "large_buffer",
                                "severity": "LOW",
                                "description": f"缓冲区 {var_name} 大小为 {size} 字节，可能浪费内存",
                                "code": match.group(0),
                            }
                        )

        except Exception as e:
            print(f"分析缓冲区大小时出错: {e}")

        return issues

    def analyze_pointer_usage(self, file_path: str) -> List[Dict[str, Any]]:
        """分析指针使用"""
        issues = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # 跳过注释
                if line_stripped.startswith("//"):
                    continue

                # 检查指针解引用
                if re.search(r"\*\s*\w+\s*=", line_stripped):
                    issues.append(
                        {
                            "file": file_path,
                            "line": line_num,
                            "type": "pointer_dereference",
                            "severity": "MEDIUM",
                            "description": "指针解引用赋值，需要确保指针有效",
                            "code": line_stripped[:100],
                        }
                    )

                # 检查数组到指针转换
                if re.search(r"\w+\s*=\s*&\s*\w+\[", line_stripped):
                    issues.append(
                        {
                            "file": file_path,
                            "line": line_num,
                            "type": "array_to_pointer",
                            "severity": "LOW",
                            "description": "数组地址赋值给指针，需要确保数组生命周期",
                            "code": line_stripped[:100],
                        }
                    )

        except Exception as e:
            print(f"分析指针使用时出错: {e}")

        return issues

    def analyze_string_operations(self, file_path: str) -> List[Dict[str, Any]]:
        """分析字符串操作"""
        issues = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # 跳过注释
                if line_stripped.startswith("//"):
                    continue

                # 检查字符串长度函数
                if re.search(r"strlen\s*\(", line_stripped):
                    issues.append(
                        {
                            "file": file_path,
                            "line": line_num,
                            "type": "string_length",
                            "severity": "MEDIUM",
                            "description": "使用strlen需要确保字符串以null结尾",
                            "code": line_stripped[:100],
                        }
                    )

                # 检查字符串比较
                if re.search(r"strcmp\s*\(", line_stripped):
                    issues.append(
                        {
                            "file": file_path,
                            "line": line_num,
                            "type": "string_compare",
                            "severity": "LOW",
                            "description": "使用strcmp需要确保两个字符串都以null结尾",
                            "code": line_stripped[:100],
                        }
                    )

        except Exception as e:
            print(f"分析字符串操作时出错: {e}")

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

                # C/C++ 特定分析
                if file_path.endswith((".cpp", ".c", ".h", ".hpp")):
                    buffer_issues = self.analyze_buffer_sizes(file_path)
                    all_issues.extend(buffer_issues)

                    pointer_issues = self.analyze_pointer_usage(file_path)
                    all_issues.extend(pointer_issues)

                    string_issues = self.analyze_string_operations(file_path)
                    all_issues.extend(string_issues)
            else:
                print(f"文件不存在: {file_path}")

        # 分类统计
        severity_counts = {}
        type_counts = {}

        for issue in all_issues:
            severity = issue["severity"]
            issue_type = issue["type"]

            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1

        return {
            "summary": {
                "total_issues": len(all_issues),
                "severity_counts": severity_counts,
                "type_counts": type_counts,
            },
            "issues": all_issues,
        }


def main():
    """主函数"""
    analyzer = MemorySafetyAnalyzer()

    # 目标文件
    target_files = [
        # Master上位机 (Python)
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/master/main.py",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/master/fc/backend/communicator.py",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/master/fc/backend/mkiii/FCCommunicator.py",
        # Slave下位机 (C++) - 全版本目录
        # f439 chasemode
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f439 chasemode/slave/main.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f439 chasemode/slave/Communicator.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f439 chasemode/slave/Processor.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f439 chasemode/slave/Fan.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f439 chasemode/slave/settings.h",
        # f429
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f429/slave/main.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f429/slave/Communicator.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9-f429/slave/Processor.cpp",
        # mbed6.16
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed6.16/slave/main.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed6.16/slave/Communicator.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed6.16/slave/Processor.cpp",
        # mbed5.9
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9/slave/main.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9/slave/Communicator.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/mbed5.9/slave/Processor.cpp",
        # 主 slave 目录
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/slave/main.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/slave/Communicator.cpp",
        "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/slave/Processor.cpp",
    ]

    # 生成报告
    report = analyzer.generate_report(target_files)

    # 保存报告
    report_file = "d:/2025/chendashuai_wind_turnnal/fan-club-master/fan-club-master_trae/master/tools/memory_safety_report.json"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 打印摘要
    print("\n" + "=" * 60)
    print("内存安全分析报告")
    print("=" * 60)
    print(f"总问题数: {report['summary']['total_issues']}")
    print("\n严重级别统计:")
    for severity, count in report["summary"]["severity_counts"].items():
        print(f"  {severity}: {count}")
    print("\n问题类型统计:")
    for issue_type, count in report["summary"]["type_counts"].items():
        print(f"  {issue_type}: {count}")

    # 显示关键问题
    critical_issues = [
        issue for issue in report["issues"] if issue["severity"] == "CRITICAL"
    ]
    if critical_issues:
        print("\n关键问题 (CRITICAL):")
        for issue in critical_issues[:5]:  # 显示前5个
            print(f"\n文件: {issue['file']}")
            print(f"行号: {issue['line']}")
            print(f"类型: {issue['type']}")
            print(f"描述: {issue['description']}")
            print(f"代码: {issue['code']}")

    print(f"\n详细报告已保存到: {report_file}")
    return report


if __name__ == "__main__":
    main()
