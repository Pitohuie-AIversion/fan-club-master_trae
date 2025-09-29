################################################################################
##----------------------------------------------------------------------------##
##                            WESTLAKE UNIVERSITY                            ##
##                      ADVANCED SYSTEMS LABORATORY                         ##
##----------------------------------------------------------------------------##
##  ███████╗██╗  ██╗ █████╗  ██████╗ ██╗   ██╗ █████╗ ███╗   ██╗ ██████╗     ##
##  ╚══███╔╝██║  ██║██╔══██╗██╔═══██╗╚██╗ ██╔╝██╔══██╗████╗  ██║██╔════╝     ##
##    ███╔╝ ███████║███████║██║   ██║ ╚████╔╝ ███████║██╔██╗ ██║██║  ███╗    ##
##   ███╔╝  ██╔══██║██╔══██║██║   ██║  ╚██╔╝  ██╔══██║██║╚██╗██║██║   ██║    ##
##  ███████╗██║  ██║██║  ██║╚██████╔╝   ██║   ██║  ██║██║ ╚████║╚██████╔╝    ##
##  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝     ##
##                                                                            ##
##  ██████╗  █████╗ ███████╗██╗  ██╗██╗   ██╗ █████╗ ██╗                     ##
##  ██╔══██╗██╔══██╗██╔════╝██║  ██║██║   ██║██╔══██╗██║                     ##
##  ██║  ██║███████║███████╗███████║██║   ██║███████║██║                     ##
##  ██║  ██║██╔══██║╚════██║██╔══██║██║   ██║██╔══██║██║                     ##
##  ██████╔╝██║  ██║███████║██║  ██║╚██████╔╝██║  ██║██║                     ##
##  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝                     ##
##                                                                            ##
##----------------------------------------------------------------------------##
## zhaoyang                   ## <mzymuzhaoyang@gmail.com> ##                 ##
## dashuai                    ## <dschen2018@gmail.com>    ##                 ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + 数据存储和导出功能模块
 + 提供多种数据格式的存储和导出功能
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

import os
import json
import csv
import h5py
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from abc import ABC, abstractmethod
import sqlite3
import pickle
from pathlib import Path

class DataFormat(Enum):
    """支持的数据格式"""
    CSV = "csv"
    JSON = "json"
    HDF5 = "hdf5"
    NUMPY = "npy"
    PICKLE = "pkl"
    EXCEL = "xlsx"
    SQLITE = "db"
    BINARY = "bin"

class CompressionType(Enum):
    """压缩类型"""
    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bz2"
    LZMA = "xz"

class StorageConfig:
    """存储配置参数"""
    def __init__(self):
        self.base_path = "./data"
        self.auto_create_dirs = True
        self.compression = CompressionType.NONE
        self.max_file_size_mb = 100
        self.backup_enabled = True
        self.metadata_enabled = True
        self.timestamp_format = "%Y%m%d_%H%M%S"
        
class DataMetadata:
    """数据元信息"""
    def __init__(self, data_type: str, channels: List[str], 
                 sample_rate: float, duration: float):
        self.data_type = data_type
        self.channels = channels
        self.sample_rate = sample_rate
        self.duration = duration
        self.created_at = datetime.now()
        self.file_size = 0
        self.checksum = ""
        self.description = ""
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "data_type": self.data_type,
            "channels": self.channels,
            "sample_rate": self.sample_rate,
            "duration": self.duration,
            "created_at": self.created_at.isoformat(),
            "file_size": self.file_size,
            "checksum": self.checksum,
            "description": self.description
        }

class DataExporter(ABC):
    """数据导出器抽象基类"""
    
    @abstractmethod
    def export(self, data: np.ndarray, metadata: DataMetadata, 
               filepath: str, **kwargs) -> bool:
        """导出数据"""
        pass
    
    @abstractmethod
    def import_data(self, filepath: str) -> tuple[np.ndarray, DataMetadata]:
        """导入数据"""
        pass

class CSVExporter(DataExporter):
    """CSV格式导出器"""
    
    def export(self, data: np.ndarray, metadata: DataMetadata, 
               filepath: str, **kwargs) -> bool:
        try:
            # 创建DataFrame
            df = pd.DataFrame(data, columns=metadata.channels)
            
            # 添加时间戳列
            time_col = np.arange(len(data)) / metadata.sample_rate
            df.insert(0, 'timestamp', time_col)
            
            # 导出CSV
            df.to_csv(filepath, index=False, **kwargs)
            
            # 保存元数据
            meta_path = filepath.replace('.csv', '_metadata.json')
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"CSV导出失败: {e}")
            return False
    
    def import_data(self, filepath: str) -> tuple[np.ndarray, DataMetadata]:
        try:
            # 读取CSV数据
            df = pd.read_csv(filepath)
            
            # 分离时间戳和数据
            if 'timestamp' in df.columns:
                data = df.drop('timestamp', axis=1).values
                channels = df.drop('timestamp', axis=1).columns.tolist()
            else:
                data = df.values
                channels = df.columns.tolist()
            
            # 读取元数据
            meta_path = filepath.replace('.csv', '_metadata.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_dict = json.load(f)
                metadata = DataMetadata(
                    meta_dict['data_type'],
                    meta_dict['channels'],
                    meta_dict['sample_rate'],
                    meta_dict['duration']
                )
            else:
                # 创建默认元数据
                metadata = DataMetadata(
                    "imported", channels, 1000.0, len(data) / 1000.0
                )
            
            return data, metadata
        except Exception as e:
            print(f"CSV导入失败: {e}")
            return None, None

class HDF5Exporter(DataExporter):
    """HDF5格式导出器"""
    
    def export(self, data: np.ndarray, metadata: DataMetadata, 
               filepath: str, **kwargs) -> bool:
        try:
            with h5py.File(filepath, 'w') as f:
                # 保存数据
                f.create_dataset('data', data=data, compression='gzip')
                
                # 保存元数据
                meta_group = f.create_group('metadata')
                meta_group.attrs['data_type'] = metadata.data_type
                meta_group.attrs['sample_rate'] = metadata.sample_rate
                meta_group.attrs['duration'] = metadata.duration
                meta_group.attrs['created_at'] = metadata.created_at.isoformat()
                
                # 保存通道信息
                channels_data = [ch.encode('utf-8') for ch in metadata.channels]
                meta_group.create_dataset('channels', data=channels_data)
            
            return True
        except Exception as e:
            print(f"HDF5导出失败: {e}")
            return False
    
    def import_data(self, filepath: str) -> tuple[np.ndarray, DataMetadata]:
        try:
            with h5py.File(filepath, 'r') as f:
                # 读取数据
                data = f['data'][:]
                
                # 读取元数据
                meta_group = f['metadata']
                channels = [ch.decode('utf-8') for ch in meta_group['channels'][:]]
                
                metadata = DataMetadata(
                    meta_group.attrs['data_type'],
                    channels,
                    meta_group.attrs['sample_rate'],
                    meta_group.attrs['duration']
                )
            
            return data, metadata
        except Exception as e:
            print(f"HDF5导入失败: {e}")
            return None, None

class SQLiteExporter(DataExporter):
    """SQLite数据库导出器"""
    
    def export(self, data: np.ndarray, metadata: DataMetadata, 
               filepath: str, **kwargs) -> bool:
        try:
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()
            
            # 创建数据表
            columns = ['timestamp REAL'] + [f'{ch} REAL' for ch in metadata.channels]
            create_sql = f"CREATE TABLE IF NOT EXISTS signal_data ({', '.join(columns)})"
            cursor.execute(create_sql)
            
            # 插入数据
            time_col = np.arange(len(data)) / metadata.sample_rate
            full_data = np.column_stack([time_col, data])
            
            placeholders = ', '.join(['?'] * (len(metadata.channels) + 1))
            insert_sql = f"INSERT INTO signal_data VALUES ({placeholders})"
            cursor.executemany(insert_sql, full_data.tolist())
            
            # 创建元数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # 插入元数据
            meta_dict = metadata.to_dict()
            for key, value in meta_dict.items():
                cursor.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)", 
                             (key, json.dumps(value)))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"SQLite导出失败: {e}")
            return False
    
    def import_data(self, filepath: str) -> tuple[np.ndarray, DataMetadata]:
        try:
            conn = sqlite3.connect(filepath)
            
            # 读取数据
            df = pd.read_sql_query("SELECT * FROM signal_data", conn)
            data = df.drop('timestamp', axis=1).values
            channels = df.drop('timestamp', axis=1).columns.tolist()
            
            # 读取元数据
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM metadata")
            meta_rows = cursor.fetchall()
            
            meta_dict = {}
            for key, value in meta_rows:
                meta_dict[key] = json.loads(value)
            
            metadata = DataMetadata(
                meta_dict['data_type'],
                meta_dict['channels'],
                meta_dict['sample_rate'],
                meta_dict['duration']
            )
            
            conn.close()
            return data, metadata
        except Exception as e:
            print(f"SQLite导入失败: {e}")
            return None, None

class DataStorageManager:
    """数据存储管理器"""
    
    def __init__(self, config: StorageConfig = None):
        self.config = config or StorageConfig()
        self.exporters = {
            DataFormat.CSV: CSVExporter(),
            DataFormat.HDF5: HDF5Exporter(),
            DataFormat.SQLITE: SQLiteExporter()
        }
        
        # 确保存储目录存在
        if self.config.auto_create_dirs:
            Path(self.config.base_path).mkdir(parents=True, exist_ok=True)
    
    def save_data(self, data: np.ndarray, metadata: DataMetadata, 
                  filename: str, format_type: DataFormat = DataFormat.HDF5,
                  **kwargs) -> str:
        """保存数据"""
        try:
            # 生成完整文件路径
            timestamp = datetime.now().strftime(self.config.timestamp_format)
            base_name = f"{timestamp}_{filename}"
            filepath = os.path.join(self.config.base_path, 
                                  f"{base_name}.{format_type.value}")
            
            # 检查文件大小限制
            estimated_size = data.nbytes / (1024 * 1024)  # MB
            if estimated_size > self.config.max_file_size_mb:
                print(f"警告: 文件大小 {estimated_size:.1f}MB 超过限制 {self.config.max_file_size_mb}MB")
            
            # 使用对应的导出器保存数据
            exporter = self.exporters.get(format_type)
            if exporter:
                success = exporter.export(data, metadata, filepath, **kwargs)
                if success:
                    print(f"数据已保存到: {filepath}")
                    
                    # 创建备份
                    if self.config.backup_enabled:
                        self._create_backup(filepath)
                    
                    return filepath
            
            return None
        except Exception as e:
            print(f"保存数据失败: {e}")
            return None
    
    def load_data(self, filepath: str, format_type: DataFormat = None) -> tuple[np.ndarray, DataMetadata]:
        """加载数据"""
        try:
            # 自动检测格式
            if format_type is None:
                ext = os.path.splitext(filepath)[1][1:]
                format_type = DataFormat(ext)
            
            exporter = self.exporters.get(format_type)
            if exporter:
                return exporter.import_data(filepath)
            
            return None, None
        except Exception as e:
            print(f"加载数据失败: {e}")
            return None, None
    
    def export_to_multiple_formats(self, data: np.ndarray, metadata: DataMetadata,
                                 filename: str, formats: List[DataFormat]) -> List[str]:
        """导出到多种格式"""
        exported_files = []
        for format_type in formats:
            filepath = self.save_data(data, metadata, filename, format_type)
            if filepath:
                exported_files.append(filepath)
        return exported_files
    
    def _create_backup(self, filepath: str):
        """创建备份文件"""
        try:
            backup_dir = os.path.join(self.config.base_path, "backups")
            Path(backup_dir).mkdir(exist_ok=True)
            
            filename = os.path.basename(filepath)
            backup_path = os.path.join(backup_dir, f"backup_{filename}")
            
            import shutil
            shutil.copy2(filepath, backup_path)
            print(f"备份已创建: {backup_path}")
        except Exception as e:
            print(f"创建备份失败: {e}")
    
    def list_stored_files(self) -> List[Dict[str, Any]]:
        """列出已存储的文件"""
        files_info = []
        try:
            for root, dirs, files in os.walk(self.config.base_path):
                for file in files:
                    if file.endswith(('.hdf5', '.csv', '.db', '.npy', '.pkl')):
                        filepath = os.path.join(root, file)
                        stat = os.stat(filepath)
                        files_info.append({
                            'filename': file,
                            'filepath': filepath,
                            'size_mb': stat.st_size / (1024 * 1024),
                            'modified': datetime.fromtimestamp(stat.st_mtime),
                            'format': os.path.splitext(file)[1][1:]
                        })
        except Exception as e:
            print(f"列出文件失败: {e}")
        
        return sorted(files_info, key=lambda x: x['modified'], reverse=True)
    
    def cleanup_old_files(self, days_old: int = 30):
        """清理旧文件"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            
            for root, dirs, files in os.walk(self.config.base_path):
                for file in files:
                    filepath = os.path.join(root, file)
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
                        print(f"已删除旧文件: {filepath}")
        except Exception as e:
            print(f"清理文件失败: {e}")

# 使用示例
if __name__ == "__main__":
    # 创建存储管理器
    config = StorageConfig()
    config.base_path = "./signal_data"
    storage_manager = DataStorageManager(config)
    
    # 模拟信号数据
    sample_rate = 1000.0
    duration = 10.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 多通道信号
    signal1 = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(len(t))
    signal2 = np.cos(2 * np.pi * 5 * t) + 0.1 * np.random.randn(len(t))
    data = np.column_stack([signal1, signal2])
    
    # 创建元数据
    metadata = DataMetadata(
        data_type="test_signal",
        channels=["Channel_1", "Channel_2"],
        sample_rate=sample_rate,
        duration=duration
    )
    
    # 保存到多种格式
    formats = [DataFormat.HDF5, DataFormat.CSV, DataFormat.SQLITE]
    exported_files = storage_manager.export_to_multiple_formats(
        data, metadata, "test_signal", formats
    )
    
    print(f"导出的文件: {exported_files}")
    
    # 列出存储的文件
    stored_files = storage_manager.list_stored_files()
    print(f"存储的文件数量: {len(stored_files)}")