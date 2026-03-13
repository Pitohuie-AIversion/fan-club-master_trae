#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 档案系统功能验证
测试archive.py中FCArchive类的所有功能
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from archive import FCArchive

    print("✓ 成功导入archive模块")
except ImportError as e:
    print(f"✗ 导入archive模块失败: {e}")
    sys.exit(1)


# 定义异常类（如果archive.py中没有定义的话）
class FCArchiveError(Exception):
    """档案系统基础异常"""

    pass


class ValidationError(FCArchiveError):
    """验证错误异常"""

    pass


class ArchiveTestSuite:
    """档案系统测试套件"""

    def __init__(self):
        self.test_dir = None
        self.test_file = None
        self.passed = 0
        self.failed = 0

    def setup(self):
        """设置测试环境"""
        print("\n=== 设置测试环境 ===")
        self.test_dir = tempfile.mkdtemp(prefix="fc_archive_test_")
        self.test_file = os.path.join(self.test_dir, "test_config.json")
        print(f"测试目录: {self.test_dir}")

    def teardown(self):
        """清理测试环境"""
        print("\n=== 清理测试环境 ===")
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print("测试目录已清理")

    def assert_test(self, condition, test_name, error_msg=""):
        """断言测试结果"""
        if condition:
            print(f"✓ {test_name}")
            self.passed += 1
        else:
            print(f"✗ {test_name}: {error_msg}")
            self.failed += 1

    def test_basic_creation(self):
        """测试基本创建功能"""
        print("\n--- 测试基本创建功能 ---")

        try:
            # 测试创建新档案
            archive = FCArchive(self.test_file)
            self.assert_test(True, "创建FCArchive实例")

            # 测试设置基本配置
            archive.set("app.name", "Test App")
            archive.set("app.version", "1.0.0")
            archive.set("database.host", "localhost")
            archive.set("database.port", 5432)

            self.assert_test(
                archive.get("app.name") == "Test App", "设置和获取字符串值"
            )

            self.assert_test(archive.get("database.port") == 5432, "设置和获取数字值")

        except Exception as e:
            self.assert_test(False, "基本创建功能", str(e))

    def test_file_operations(self):
        """测试文件操作"""
        print("\n--- 测试文件操作 ---")

        try:
            archive = FCArchive(self.test_file)
            archive.set("test.key", "test_value")

            # 测试保存
            archive.save()
            self.assert_test(os.path.exists(self.test_file), "保存配置文件")

            # 测试加载
            new_archive = FCArchive(self.test_file)
            new_archive.load()
            self.assert_test(
                new_archive.get("test.key") == "test_value", "加载配置文件"
            )

        except Exception as e:
            self.assert_test(False, "文件操作", str(e))

    def test_encoding_support(self):
        """测试编码支持"""
        print("\n--- 测试编码支持 ---")

        try:
            # 测试UTF-8编码
            utf8_file = os.path.join(self.test_dir, "utf8_config.json")
            archive = FCArchive(utf8_file, encoding="utf-8")
            archive.set("chinese", "中文测试")
            archive.set("emoji", "🎉✨")
            archive.save()

            # 重新加载验证
            new_archive = FCArchive(utf8_file, encoding="utf-8")
            new_archive.load()

            self.assert_test(
                new_archive.get("chinese") == "中文测试", "UTF-8编码中文支持"
            )

            self.assert_test(new_archive.get("emoji") == "🎉✨", "UTF-8编码emoji支持")

        except Exception as e:
            self.assert_test(False, "编码支持", str(e))

    def test_validation(self):
        """测试验证功能"""
        print("\n--- 测试验证功能 ---")

        try:
            archive = FCArchive(self.test_file)

            # 设置测试数据
            archive.set("app.name", "Test App")
            archive.set("app.version", "1.0.0")
            archive.set("database.host", "localhost")
            archive.set("database.port", 5432)

            # 测试数据完整性验证
            is_valid = archive.validate_data_integrity()
            self.assert_test(is_valid, "数据完整性验证")

            # 测试验证报告
            report = archive.get_validation_report()
            self.assert_test(
                isinstance(report, dict) and "summary" in report, "生成验证报告"
            )

        except Exception as e:
            self.assert_test(False, "验证功能", str(e))

    def test_error_handling(self):
        """测试错误处理"""
        print("\n--- 测试错误处理 ---")

        try:
            archive = FCArchive(self.test_file)

            # 测试备份功能
            archive.set("test.data", "original")
            backup_path = archive.create_backup()
            self.assert_test(os.path.exists(backup_path), "创建备份文件")

            # 测试安全设置值
            success = archive.safe_set_value("test.data", "modified")
            self.assert_test(success, "安全设置值")

            # 测试从备份恢复
            archive.restore_from_backup(backup_path)
            self.assert_test(archive.get("test.data") == "original", "从备份恢复")

        except Exception as e:
            self.assert_test(False, "错误处理", str(e))

    def test_advanced_features(self):
        """测试高级功能"""
        print("\n--- 测试高级功能 ---")

        try:
            archive = FCArchive(self.test_file)

            # 测试嵌套配置
            archive.set("server.database.primary.host", "db1.example.com")
            archive.set("server.database.primary.port", 5432)
            archive.set("server.database.replica.host", "db2.example.com")
            archive.set("server.database.replica.port", 5433)

            # 测试获取嵌套值
            self.assert_test(
                archive.get("server.database.primary.host") == "db1.example.com",
                "嵌套配置设置和获取",
            )

            # 测试获取所有键
            all_keys = archive.get_all_keys()
            self.assert_test(len(all_keys) > 0, "获取所有配置键")

            # 测试修改状态
            archive.set("new.key", "new_value")
            self.assert_test(archive.modified(), "检测修改状态")

        except Exception as e:
            self.assert_test(False, "高级功能", str(e))

    def test_edge_cases(self):
        """测试边界情况"""
        print("\n--- 测试边界情况 ---")

        try:
            archive = FCArchive(self.test_file)

            # 测试空值
            archive.set("empty.string", "")
            archive.set("null.value", None)
            archive.set("zero.number", 0)
            archive.set("false.boolean", False)

            self.assert_test(archive.get("empty.string") == "", "空字符串处理")

            self.assert_test(archive.get("null.value") is None, "None值处理")

            self.assert_test(archive.get("zero.number") == 0, "零值处理")

            self.assert_test(archive.get("false.boolean") is False, "False值处理")

            # 测试不存在的键
            default_value = archive.get("nonexistent.key", "default")
            self.assert_test(default_value == "default", "不存在键的默认值")

        except Exception as e:
            self.assert_test(False, "边界情况", str(e))

    def run_all_tests(self):
        """运行所有测试"""
        print("开始运行档案系统测试套件...")

        self.setup()

        try:
            self.test_basic_creation()
            self.test_file_operations()
            self.test_encoding_support()
            self.test_validation()
            self.test_error_handling()
            self.test_advanced_features()
            self.test_edge_cases()

        finally:
            self.teardown()

        # 输出测试结果
        print(f"\n=== 测试结果 ===")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"总计: {self.passed + self.failed}")

        if self.failed == 0:
            print("🎉 所有测试通过！")
            return True
        else:
            print(f"❌ {self.failed} 个测试失败")
            return False


def main():
    """主函数"""
    print("档案系统功能测试")
    print("=" * 50)

    test_suite = ArchiveTestSuite()
    success = test_suite.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
