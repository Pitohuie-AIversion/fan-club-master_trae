#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
档案系统演示脚本
展示archive.py的实际使用方法和功能特性
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path


# 简化版的FCArchive类用于演示
class DemoFCArchive:
    """演示版的FCArchive类"""

    def __init__(self, file_path, encoding="utf-8"):
        self.file_path = file_path
        self.encoding = encoding
        self.data = {}
        self._modified = False
        print(f"📁 创建档案实例: {file_path}")

    def set(self, key, value):
        """设置配置值"""
        keys = key.split(".")
        current = self.data

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
        self._modified = True
        print(f"✏️  设置 {key} = {value}")

    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split(".")
        current = self.data

        try:
            for k in keys:
                current = current[k]
            print(f"📖 获取 {key} = {current}")
            return current
        except (KeyError, TypeError):
            print(f"📖 获取 {key} = {default} (默认值)")
            return default

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.file_path, "w", encoding=self.encoding) as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            self._modified = False
            print(f"💾 配置已保存到: {self.file_path}")
            return True
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False

    def load(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding=self.encoding) as f:
                    self.data = json.load(f)
                self._modified = False
                print(f"📂 配置已从文件加载: {self.file_path}")
                return True
            else:
                print(f"⚠️  文件不存在: {self.file_path}")
                return False
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return False

    def display_config(self):
        """显示当前配置"""
        print("\n📋 当前配置:")
        print(json.dumps(self.data, indent=2, ensure_ascii=False))

    def get_stats(self):
        """获取统计信息"""

        def count_keys(d):
            count = 0
            for k, v in d.items():
                count += 1
                if isinstance(v, dict):
                    count += count_keys(v)
            return count

        stats = {
            "total_keys": count_keys(self.data),
            "is_modified": self._modified,
            "encoding": self.encoding,
            "file_exists": os.path.exists(self.file_path),
        }

        print(f"\n📊 统计信息:")
        for key, value in stats.items():
            print(f"   {key}: {value}")

        return stats


def demo_basic_usage():
    """演示基本使用方法"""
    print("\n" + "=" * 60)
    print("🚀 演示1: 基本使用方法")
    print("=" * 60)

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    temp_file.close()

    try:
        # 创建档案实例
        archive = DemoFCArchive(temp_file.name)

        # 设置基本配置
        archive.set("app.name", "Fan Club MkIV")
        archive.set("app.version", "4.0.0")
        archive.set("app.author", "开发团队")

        # 设置数据库配置
        archive.set("database.host", "localhost")
        archive.set("database.port", 5432)
        archive.set("database.name", "fanclub_db")

        # 显示配置
        archive.display_config()

        # 保存配置
        archive.save()

        # 获取统计信息
        archive.get_stats()

    finally:
        # 清理临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def demo_encoding_support():
    """演示编码支持"""
    print("\n" + "=" * 60)
    print("🌍 演示2: 多编码格式支持")
    print("=" * 60)

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    temp_file.close()

    try:
        # 创建UTF-8编码的档案
        archive = DemoFCArchive(temp_file.name, encoding="utf-8")

        # 设置多语言配置
        archive.set("messages.welcome", "欢迎使用Fan Club系统")
        archive.set("messages.goodbye", "再见！👋")
        archive.set("messages.error", "发生错误 ❌")
        archive.set("messages.success", "操作成功 ✅")

        # 设置emoji配置
        archive.set("ui.icons.fan", "🌀")
        archive.set("ui.icons.settings", "⚙️")
        archive.set("ui.icons.user", "👤")

        # 显示和保存
        archive.display_config()
        archive.save()

        # 重新加载验证
        new_archive = DemoFCArchive(temp_file.name, encoding="utf-8")
        new_archive.load()

        print("\n🔄 重新加载后的配置:")
        new_archive.display_config()

    finally:
        # 清理临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def demo_nested_config():
    """演示嵌套配置"""
    print("\n" + "=" * 60)
    print("🏗️  演示3: 嵌套配置管理")
    print("=" * 60)

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    temp_file.close()

    try:
        archive = DemoFCArchive(temp_file.name)

        # 设置复杂的嵌套配置
        archive.set("server.web.host", "0.0.0.0")
        archive.set("server.web.port", 8080)
        archive.set("server.web.ssl.enabled", True)
        archive.set("server.web.ssl.cert_path", "/etc/ssl/cert.pem")
        archive.set("server.web.ssl.key_path", "/etc/ssl/key.pem")

        archive.set("server.database.primary.host", "db1.example.com")
        archive.set("server.database.primary.port", 5432)
        archive.set("server.database.replica.host", "db2.example.com")
        archive.set("server.database.replica.port", 5433)

        archive.set("logging.level", "INFO")
        archive.set("logging.file.path", "/var/log/fanclub.log")
        archive.set("logging.file.max_size", "100MB")
        archive.set("logging.file.backup_count", 5)

        # 显示配置
        archive.display_config()

        # 演示获取嵌套值
        print("\n🔍 获取嵌套配置值:")
        archive.get("server.web.host")
        archive.get("server.database.primary.port")
        archive.get("logging.level")
        archive.get("nonexistent.key", "默认值")

        # 获取统计信息
        archive.get_stats()

    finally:
        # 清理临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def demo_data_types():
    """演示不同数据类型支持"""
    print("\n" + "=" * 60)
    print("🎯 演示4: 多种数据类型支持")
    print("=" * 60)

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    temp_file.close()

    try:
        archive = DemoFCArchive(temp_file.name)

        # 设置不同类型的数据
        archive.set("string_value", "这是一个字符串")
        archive.set("integer_value", 42)
        archive.set("float_value", 3.14159)
        archive.set("boolean_true", True)
        archive.set("boolean_false", False)
        archive.set("null_value", None)
        archive.set("empty_string", "")
        archive.set("zero_number", 0)

        # 设置列表和对象
        archive.set("list_value", [1, 2, 3, "四", "五"])
        archive.set("object_value", {"key1": "value1", "key2": 123})

        # 显示配置
        archive.display_config()

        # 演示获取不同类型的值
        print("\n🔍 获取不同类型的值:")
        archive.get("string_value")
        archive.get("integer_value")
        archive.get("float_value")
        archive.get("boolean_true")
        archive.get("boolean_false")
        archive.get("null_value")
        archive.get("empty_string")
        archive.get("zero_number")

        # 获取统计信息
        archive.get_stats()

    finally:
        # 清理临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def main():
    """主函数"""
    print("🎉 Fan Club 档案系统演示")
    print("展示archive.py的功能特性和使用方法")

    try:
        demo_basic_usage()
        demo_encoding_support()
        demo_nested_config()
        demo_data_types()

        print("\n" + "=" * 60)
        print("✅ 演示完成！")
        print("=" * 60)
        print("\n📝 总结:")
        print("   ✓ 基本配置管理功能")
        print("   ✓ 多编码格式支持 (UTF-8, 中文, Emoji)")
        print("   ✓ 嵌套配置结构")
        print("   ✓ 多种数据类型支持")
        print("   ✓ 文件保存和加载")
        print("   ✓ 统计信息和状态监控")

    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
