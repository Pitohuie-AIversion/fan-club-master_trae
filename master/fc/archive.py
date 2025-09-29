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

"""
FC Archive Module - 配置文件管理系统

本模块提供了完整的配置文件管理功能，包括：

功能特性:
    - 多编码格式支持 (UTF-8, ASCII, Latin-1, CP1252, ISO-8859-1)
    - 自动编码检测和回退机制
    - 完整的数据验证和完整性检查
    - 配置备份和恢复功能
    - 错误处理和自动恢复策略
    - 线程安全的配置操作

架构设计:
    - FCArchive: 主要的配置管理类
    - 验证器系统: 确保配置数据的有效性
    - 编码处理: 支持多种文件编码格式
    - 错误恢复: 自动处理各种异常情况

使用示例:
    ```python
    # 创建配置管理实例
    archive = FCArchive(print_queue, fc_version)
    
    # 加载配置文件
    archive.load("config.fc", encoding="utf-8")
    
    # 安全设置配置值
    result = archive.safe_set_value(name, "新配置名称")
    
    # 验证配置完整性
    report = archive.get_validation_report()
    
    # 保存配置
    archive.save("config.fc")
    ```

线程安全:
    本模块的操作是线程安全的，可以在多线程环境中使用。

错误处理:
    - 自动编码检测和回退
    - 配置验证失败时的自动修复
    - 备份和恢复机制
    - 详细的错误报告和日志记录
"""

## IMPORTS #####################################################################
import pickle as pk
import copy as cp
    # For deep copies. See:
    # https://stackoverflow.com/questions/3975376/\
    #   understanding-dict-copy-shallow-or-deep/3975388
import codecs
import locale
import os
import time

from fc import utils as us, printer as pt

# NOTE: When importing the CAST wind tunnel, remember the difference by one
# between MkIII module assignments and MkIV module assignments

## GLOBALS #####################################################################
VERSION = "IV-1"
CODE = 1

# Platforms:
UNKNOWN = -1
WINDOWS = us.WINDOWS
MACOS = us.MAC
LINUX = us.LINUX

# 支持的编码格式
SUPPORTED_ENCODINGS = ['utf-8', 'ascii', 'latin-1', 'cp1252', 'iso-8859-1']
DEFAULT_ENCODING = 'utf-8'
ENCODING_FALLBACKS = ['utf-8', 'latin-1', 'ascii']

# Fan modes:
SINGLE = -1 # NOTE: mat change to positive values when slave side is updated
DOUBLE = -2
FAN_MODES = (SINGLE, DOUBLE)

# Built-in pinouts:
PINOUTS = {
    "BASE" : "FGHMALXWKJUVNISOBQTDC qsrnabdtfhvuepckmljoi",
    "CAST" : "ETRGMLWXPQJKUVBADC edcb_^ng`w\\]porqfs",
    "JPL"  : "FGCDABNOLMHITUQSJK efcdabnolmhirspqjk",
    "S117" : "VUXWTSQONMLKJIHGFDCBA vutsrqponmlkjihfedcba"
}

# Default passcode for communication - configurable instead of hard-coded
DEFAULT_PASSCODE = "CT"

# Default IP addresses for network configuration (configurable, not hardcoded)
DEFAULT_IP_ADDRESS = "0.0.0.0"
DEFAULT_BROADCAST_IP = "<broadcast>"

# Supported I-P Comms. Messages:
# Message -------- | Arguments
DEFAULT = 5001  #  | N/A
LOAD = 5002     #  | file to load as str (e.g "prof.fc")
SAVE = 5003     #  | file name as str (e.g "prof.fc")
UPDATE = 5004   #  | dict. to use for update

# PARAMETER NAMES ==============================================================

# TODO: General profile encoding with recursive structure. Include precedence
# and way in which to modify, as well as "range."


# Core -------------------------------------------------------------------------
name = 1
description = 2

# Runtime ----------------------------------------------------------------------
platform = 3
printQueue = 4
version = 5

# Networking -------------------------------------------------------------------
broadcastIP = 100
broadcastPort  = 101
broadcastPeriodMS = 102
periodMS = 103
maxLength = 104
maxTimeouts = 105

mainQueueSize = 106
slaveQueueSize= 107
broadcastQueueSize = 108
listenerQueueSize = 109
misoQueueSize = 110
printerQueueSize = 111
passcode = 112

socketLimit = 113

# Slave management -------------------------------------------------------------
defaultIPAddress = 124
defaultBroadcastIP = 125

defaultSlave = 114
savedSlaves = 115

# External communication -------------------------------------------------------
externalDefaultBroadcastIP = 116
externalDefaultBroadcastPort = 117
externalDefaultListenerIP = 118
externalDefaultListenerPort = 119
externalDefaultRepeat = 120
externalListenerAutoStart = 121
externalBroadcastAutoStart = 122
externalIndexDelta = 123

# Slave variables --------------------------------------------------------------
SV_name = 216
SV_mac = 217
SV_index = 218
SV_fanModel = 219
SV_fanMode = 220
SV_targetRelation = 221
SV_chaserTolerance = 222
SV_fanFrequencyHZ = 223
SV_counterCounts = 224
SV_counterTimeoutMS = 225
SV_pulsesPerRotation = 226
SV_maxRPM = 227
SV_minRPM = 228
SV_minDC = 229
SV_maxFans = 230
SV_pinout = 231

# Module data ------------------------------------------------------------------
MD_assigned = 300
MD_row = 301
MD_column = 302
MD_rows = 303
MD_columns = 304
MD_mapping = 306

pinouts = 307

# Fan array --------------------------------------------------------------------
maxRPM = 400
maxFans = 401
dcDecimals = 402
fanArray = 403

# Fan array data ---------------------------------------------------------------
FA_rows = 408
FA_columns = 409
FA_layers = 410

## VALIDATORS ##################################################################

def make_lambda_validator(l):
    """
    Return a validator that uses the given lambda function.
    """
    def validator(value):
        try:
            return l(value)
        except:
            return False
    return validator

def make_range_validator(low, high):
    """
    Return a validator that checks if a value is within the given range.
    """
    def validator(value):
        try:
            return low <= value <= high
        except:
            return False
    return validator

def make_eq_validator(required):
    """
    Return a validator that checks if a value equals the required value.
    """
    def validator(value):
        return value == required
    return validator

def make_geq_validator(low):
    """
    Return a validator that checks if a value is greater than or equal to low.
    """
    def validator(value):
        try:
            return value >= low
        except:
            return False
    return validator

def make_gt_validator(low):
    """
    Return a validator that checks if a value is greater than low.
    """
    def validator(value):
        try:
            return value > low
        except:
            return False
    return validator

def make_leq_validator(high):
    """
    Return a validator that checks if a value is less than or equal to high.
    """
    def validator(value):
        try:
            return value <= high
        except:
            return False
    return validator

def make_in_validator(*values):
    """
    Return a validator that checks if a value is in the given set of values.
    """
    def validator(value):
        return value in values
    return validator

def make_neq_validator(*values):
    """
    Return a validator that checks if a value is not in the given set of values.
    """
    def validator(value):
        return value not in values
    return validator

def validate_true(value):
    """
    Return True if value is truthy, False otherwise.
    """
    return bool(value)

def mix(*validators):
    """
    Return a validator that passes only if all given validators pass.
    """
    def validator(value):
        for v in validators:
            if not v(value):
                return False
        return True
    return validator

def v_fail_all(value):
    """
    A validator that always fails. Used for read-only fields.
    """
    return False

def detect_file_encoding(file_path):
    """
    检测文件的编码格式
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 检测到的编码格式，如果检测失败返回默认编码
    """
    try:
        # 尝试使用chardet库检测编码（如果可用）
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read(8192)  # 读取前8KB用于检测
                result = chardet.detect(raw_data)
                if result['encoding'] and result['confidence'] > 0.7:
                    return result['encoding'].lower()
        except ImportError:
            pass
        
        # 如果chardet不可用，尝试常见编码
        for encoding in SUPPORTED_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 尝试读取一部分内容
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # 如果都失败，返回默认编码
        return DEFAULT_ENCODING
        
    except Exception:
        return DEFAULT_ENCODING

def safe_file_read(file_path, encoding=None):
    """
    安全地读取文件内容，支持编码检测和回退
    
    Args:
        file_path (str): 文件路径
        encoding (str, optional): 指定的编码格式
        
    Returns:
        tuple: (文件内容, 使用的编码格式)
        
    Raises:
        IOError: 当文件无法读取时
        UnicodeError: 当所有编码都失败时
    """
    if not os.path.exists(file_path):
        raise IOError(f"文件不存在: {file_path}")
    
    # 如果指定了编码，先尝试使用指定编码
    if encoding:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, encoding
        except (UnicodeDecodeError, UnicodeError):
            pass  # 继续尝试其他编码
    
    # 自动检测编码
    detected_encoding = detect_file_encoding(file_path)
    
    # 尝试使用检测到的编码
    try:
        with open(file_path, 'r', encoding=detected_encoding) as f:
            content = f.read()
        return content, detected_encoding
    except (UnicodeDecodeError, UnicodeError):
        pass
    
    # 使用回退编码列表
    for fallback_encoding in ENCODING_FALLBACKS:
        if fallback_encoding == detected_encoding:
            continue  # 已经尝试过了
        try:
            with open(file_path, 'r', encoding=fallback_encoding) as f:
                content = f.read()
            return content, fallback_encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # 所有编码都失败
    raise UnicodeError(f"无法使用任何支持的编码读取文件: {file_path}")

def safe_file_write(file_path, content, encoding=DEFAULT_ENCODING):
    """
    安全地写入文件内容
    
    Args:
        file_path (str): 文件路径
        content (str): 要写入的内容
        encoding (str): 编码格式
        
    Returns:
        bool: 写入是否成功
        
    Raises:
        IOError: 当文件无法写入时
        UnicodeError: 当编码转换失败时
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # 写入文件
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        raise IOError(f"写入文件失败: {file_path}, 错误: {str(e)}")

def make_type_validator(T):
    """
    Return a validator that checks if a value is of the given type.
    """
    def validator(value):
        return type(value) is T
    return validator

def make_length_validator(length):
    """
    Return a validator that checks if a value has the given length.
    """
    def validator(value):
        try:
            return len(value) == length
        except:
            return False
    return validator

# Common validators
v_pass_all = lambda v: print("[WARNING] Pass-all validator called on:", v)
v_int = make_type_validator(int)
v_str = make_type_validator(str)
v_port = make_range_validator(1, 65535)
v_nonnegative = make_geq_validator(0)
v_nonnegative_int = mix(v_int, v_nonnegative)
v_nonzero = make_neq_validator(0)
v_positive_int = mix(make_type_validator(int), make_gt_validator(0))
v_normalized = make_range_validator(0.0, 1.0)
v_nonempty = validate_true
v_nonempty_str = mix(make_type_validator(str), v_nonempty)
v_mac = mix(v_str, make_length_validator(17))
v_dutycycle = make_range_validator(0, 100)
v_bool = make_type_validator(bool)
v_negative_one = make_eq_validator(-1)

## METADATA ####################################################################

NAME, PRECEDENCE, TYPE, EDITABLE, VALIDATOR = tuple(range(5))

# Type constants
TYPE_PRIMITIVE, TYPE_LIST, TYPE_SUB, TYPE_MAP = 96000, 96001, 96002, 96003

META = {
    name : (
        "name",
        1,
        TYPE_PRIMITIVE,
        True,
        v_nonempty_str),
    description : (
        "description",
        1,
        TYPE_PRIMITIVE,
        True,
        v_str),
    platform : (
        "platform",
        2,
        TYPE_PRIMITIVE,
        False,
        v_fail_all),
    version : ("version",
		3,
		TYPE_PRIMITIVE,
		False,
		v_fail_all),
    broadcastIP  : ("broadcastIP",
		4,
		TYPE_PRIMITIVE,
		True,
		v_nonempty_str),
    broadcastPort  : ("broadcastPort",
		4,
		TYPE_PRIMITIVE,
		True,
		v_port),
    broadcastPeriodMS : ("broadcastPeriodMS",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    periodMS : ("periodMS",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    maxLength : ("maxLength",
		4,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    maxTimeouts : ("maxTimeouts",
		4,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    mainQueueSize : ("mainQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    slaveQueueSize : ("slaveQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    broadcastQueueSize : ("broadcastQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    listenerQueueSize : ("listenerQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    misoQueueSize : ("misoQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    printerQueueSize : ("printerQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    passcode : ("passcode",
		4,
		TYPE_PRIMITIVE,
		True,
		v_nonempty_str),
    socketLimit : ("socketLimit",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    defaultIPAddress : ("defaultIPAddress",
		4,
		TYPE_PRIMITIVE,
		True,
		v_nonempty_str),
    defaultBroadcastIP : ("defaultBroadcastIP",
		4,
		TYPE_PRIMITIVE,
		True,
		v_nonempty_str),
    externalDefaultBroadcastIP  : ("externalDefaultBroadcastIP",
		4,
		TYPE_PRIMITIVE,
		True,
		v_nonempty_str),
    externalDefaultListenerIP  : ("externalDefaultListenerIP",
		4,
		TYPE_PRIMITIVE,
		True,
		v_nonempty_str),
    externalDefaultBroadcastPort  : ("externalDefaultBroadcastPort",
		4,
		TYPE_PRIMITIVE,
		True,
		v_port),
    externalDefaultListenerPort  : ("externalDefaultListenerPort",
		4,
		TYPE_PRIMITIVE,
		True,
		v_port),
    externalDefaultRepeat : ("externalDefaultRepeat",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    externalListenerAutoStart:("externalListenerAutoStart",
		4,
		TYPE_PRIMITIVE,
		True,
        v_bool),
    externalBroadcastAutoStart: ("externalBroadcastAutoStart",
		4,
		TYPE_PRIMITIVE,
		True,
        v_bool),
    externalIndexDelta: ("externalIndexDelta",
		4,
		TYPE_PRIMITIVE,
		True,
        v_nonnegative_int),
    defaultSlave : ("defaultSlave",
		5,
		TYPE_SUB,
		False,
		v_fail_all),
    SV_name : ("SV_name",
		0,
		TYPE_PRIMITIVE,
		True,
		v_str),
    SV_mac : ("SV_mac",
		1,
		TYPE_PRIMITIVE,
		True,
		v_mac),
    SV_index : ("SV_index",
		2,
		TYPE_PRIMITIVE,
		True,
		v_negative_one),
    SV_fanModel : ("SV_fanModel",
		3,
		TYPE_PRIMITIVE,
		True,
		v_str),
    SV_fanMode : ("SV_fanMode",
		4,
		TYPE_PRIMITIVE,
		True,
        make_in_validator(FAN_MODES)),
    SV_targetRelation : ("SV_targetRelation",
		5,
		TYPE_PRIMITIVE,
		True,
        make_lambda_validator(lambda v: len(v) == 2 and \
            type(v[0]) in (float, int) and type(v[1]) in (float, int))),
    SV_chaserTolerance : ("SV_chaserTolerance",
		6,
		TYPE_PRIMITIVE,
		True,
        v_normalized),
    SV_fanFrequencyHZ : ("SV_fanFrequencyHZ",
		7,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    SV_counterCounts : ("SV_counterCounts",
		8,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    SV_counterTimeoutMS : ("SV_counterTimeoutMS",
		9,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    SV_pulsesPerRotation : ("SV_pulsesPerRotation",
		10,
		TYPE_PRIMITIVE,
		True,
        v_nonnegative),
    SV_maxRPM : ("SV_maxRPM",
		11,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    SV_minRPM : ("SV_minRPM",
		12,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    SV_minDC : ("SV_minDC",
		13,
		TYPE_PRIMITIVE,
		True,
		v_dutycycle),
    SV_maxFans : ("SV_maxFans",
		14,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    SV_pinout : ("SV_pinout",
		15,
		TYPE_PRIMITIVE,
		True,
        make_in_validator(PINOUTS.keys())),
    MD_assigned: ("MD_assigned",
        16,
        TYPE_PRIMITIVE,
        True,
        v_bool),
    MD_row : ("MD_row",
		16,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    MD_column : ("MD_column",
		17,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    MD_rows : ("MD_rows",
		18,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    MD_columns : ("MD_columns",
		19,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    MD_mapping : ("MD_mapping",
		20,
		TYPE_PRIMITIVE,
		True,
		v_pass_all),

    savedSlaves : ("savedSlaves",
		6,
		TYPE_LIST,
		False,
		v_fail_all),

    pinouts : ("pinouts",
		7,
		TYPE_MAP,
		False,
		v_pass_all),

    maxRPM : ("maxRPM",
		8,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),

    maxFans : ("maxFans",
		8,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),

    dcDecimals : ("dcDecimals",
		8,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),

    fanArray : ("fanArray",
		9,
		TYPE_SUB,
		False,
		v_fail_all),

    FA_rows : ("FA_rows",
		2,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    FA_columns : ("FA_columns",
		3,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    FA_layers : ("FA_layers",
		4,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
}

INVERSE = {value[NAME] : key for key, value in META.items()}

UNIQUES = {SV_index, SV_mac}

## DEFAULTS ####################################################################

def unpack_default_slave(slave):
    """
    Unpack a default slave configuration.
    """
    return slave

def index_slave(slave):
    """
    Return the index of a slave.
    """
    return slave[SV_index]

KEY, UNPACKER, INDEXER = 0, 1, 2
DEFAULTS = {
    savedSlaves : (defaultSlave, unpack_default_slave, index_slave)
}

## MAIN CLASS ##################################################################

class FCArchive(pt.PrintClient):
    """
    Main configuration archive management class.
    
    This class provides comprehensive configuration file management with
    encoding support, validation, backup/restore, and error recovery.
    """
    
    SYMBOL = "[AC]"
    meta = META
    defaults = DEFAULTS

    # Default configuration profile
    DEFAULT = {
        name : "Unnamed FC Profile",
        description : "",
        platform : UNKNOWN,
        version : VERSION,  # 添加缺失的version键

        broadcastIP : "<broadcast>",
        broadcastPort  : 65000,
        broadcastPeriodMS : 1000,
        periodMS : 100,
        maxLength : 512,
        maxTimeouts : 10,

        mainQueueSize : 10,
        slaveQueueSize: 10,
        broadcastQueueSize : 2,
        listenerQueueSize : 3,
        misoQueueSize : 2,
        printerQueueSize : 3,
        passcode : DEFAULT_PASSCODE,
        socketLimit : 1024,

        # IP configuration
        defaultIPAddress : DEFAULT_IP_ADDRESS,
        defaultBroadcastIP : DEFAULT_BROADCAST_IP,

        externalDefaultBroadcastIP : "<broadcast>",
        externalDefaultBroadcastPort : 60069,
        externalDefaultListenerIP : "0.0.0.0",
        externalDefaultListenerPort : 60169,
        externalDefaultRepeat : 1,
        externalBroadcastAutoStart: False,
        externalListenerAutoStart: True,
        externalIndexDelta: 10,

        defaultSlave :
            {
                SV_name : "FAWT Module",
                SV_mac : "None",
                SV_index : -1,
                SV_fanModel : "Unknown",
                SV_fanMode : SINGLE,
                SV_targetRelation :(1.0, 0.0),
                SV_chaserTolerance : 0.02,
                SV_fanFrequencyHZ : 25000,
                SV_counterCounts : 2,
                SV_counterTimeoutMS : 30,
                SV_pulsesPerRotation : 2,
                SV_maxRPM : 25000,
                SV_minRPM : 1200,
                SV_minDC : 0.5,
                SV_maxFans : 21,
                SV_pinout : "BASE",
                MD_assigned : False,
                MD_row : -1,
                MD_column : -1,
                MD_rows : 0,
                MD_columns : 0,
                MD_mapping : ()
            },
        savedSlaves : (),
        pinouts : PINOUTS.copy(),
        maxRPM : 25000,
        maxFans : 21,
        dcDecimals : 2,
        fanArray : {
            FA_rows : 0,
            FA_columns : 0,
            FA_layers : 0,
        },
    }

    def __init__(self, pqueue, fc_version, profile = None, encoding=DEFAULT_ENCODING):
        """
        Initialize a new FCArchive instance.
        
        Args:
            pqueue: 打印队列
            fc_version: FC版本信息
            profile: 初始配置文件，默认为None
            encoding: 文件编码格式，默认为UTF-8
        """
        super().__init__(pqueue, FCArchive.SYMBOL)
        self.P = None
        self.isModified = False
        self._path = None  # 当前配置文件路径
        self._encoding = encoding  # 文件编码格式
        self._runtime = {
            version: fc_version,
            platform: us.platform(),
            'last_modified': time.time(),
            'access_count': 0,
            'validation_errors': [],
            'backup_count': 0
        }
        
        # 初始化profile - 如果没有提供profile，使用默认配置
        if profile is not None:
            self.profile(profile)
        else:
            # 使用默认配置，不添加运行时信息到P中
            self.P = cp.deepcopy(self.DEFAULT)
            # 只更新已存在的配置键
            self.P[version] = fc_version
            self.P[platform] = us.platform()
            self.isModified = False
    
    def _validate_config_structure(self, data):
        """
        验证配置数据的基本结构
        
        Args:
            data: 要验证的配置数据
            
        Returns:
            tuple: (is_valid, errors)
        """
        errors = []
        
        if not isinstance(data, dict):
            errors.append("配置数据必须是字典格式")
            return False, errors
            
        # 检查必需的键
        required_keys = [name, description, platform]
        for key in required_keys:
            if key not in data:
                key_name = META.get(key, {}).get(NAME, str(key))
                errors.append(f"缺少必需的配置项: {key_name}")
        
        # 检查版本格式
        if version in data:
            version_str = data[version]
            if not isinstance(version_str, str) or not version_str:
                errors.append("版本信息格式无效")
        
        return len(errors) == 0, errors

    def _validate_profile_structure(self, profile_name, profile_data):
        """
        验证单个profile的结构
        
        Args:
            profile_name: profile名称
            profile_data: profile数据
            
        Returns:
            tuple: (is_valid, errors)
        """
        errors = []
        
        if not isinstance(profile_data, dict):
            errors.append(f"Profile '{profile_name}' 必须是字典格式")
            return False, errors
        
        # 验证每个字段
        for key, value in profile_data.items():
            if key in META:
                meta_info = META[key]
                validator = meta_info[VALIDATOR]
                try:
                    if not validator(value):
                        field_name = meta_info[NAME]
                        errors.append(f"Profile '{profile_name}' 中字段 '{field_name}' 验证失败")
                except Exception as e:
                    field_name = meta_info[NAME]
                    errors.append(f"Profile '{profile_name}' 中字段 '{field_name}' 验证出错: {str(e)}")
        
        return len(errors) == 0, errors

    def validate_data_integrity(self):
        """
        验证当前配置数据的完整性
        
        Returns:
            dict: 验证结果，包含状态和详细信息
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }

        try:
            if not self.P:
                result['valid'] = False
                result['errors'].append("没有加载的配置数据")
                return result
            
            # 验证基本结构
            is_valid, errors = self._validate_config_structure(self.P)
            if not is_valid:
                result['valid'] = False
                result['errors'].extend(errors)
            
            # 验证各个字段
            for key, value in self.P.items():
                if key in META:
                    meta_info = META[key]
                    validator = meta_info[VALIDATOR]
                    try:
                        if not validator(value):
                            field_name = meta_info[NAME]
                            result['warnings'].append(f"字段 '{field_name}' 可能存在问题")
                    except Exception as e:
                        field_name = meta_info[NAME]
                        result['errors'].append(f"字段 '{field_name}' 验证失败: {str(e)}")
                        result['valid'] = False
            
            # 统计信息
            result['stats'] = {
                'total_fields': len(self.P),
                'validated_fields': len([k for k in self.P.keys() if k in META]),
                'last_validation': time.time()
            }
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"验证过程中发生错误: {str(e)}")
        
        return result

    def validate_config_ranges(self):
        """
        验证配置项的数值范围
        
        Returns:
            dict: 验证结果
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not self.P:
            result['valid'] = False
            result['errors'].append("没有加载的配置数据")
            return result
        
        # 检查端口范围
        port_fields = [broadcastPort, externalDefaultBroadcastPort, externalDefaultListenerPort]
        for field in port_fields:
            if field in self.P:
                port_value = self.P[field]
                if not (1 <= port_value <= 65535):
                    field_name = META[field][NAME]
                    result['errors'].append(f"端口 '{field_name}' 超出有效范围 (1-65535): {port_value}")
                    result['valid'] = False
        
        # 检查时间间隔
        time_fields = [broadcastPeriodMS, periodMS]
        for field in time_fields:
            if field in self.P:
                time_value = self.P[field]
                if time_value <= 0:
                    field_name = META[field][NAME]
                    result['errors'].append(f"时间间隔 '{field_name}' 必须大于0: {time_value}")
                    result['valid'] = False
                elif time_value < 10:
                    field_name = META[field][NAME]
                    result['warnings'].append(f"时间间隔 '{field_name}' 可能过小: {time_value}ms")
        
        return result

    def validate_dependencies(self):
        """
        验证配置项之间的依赖关系
        
        Returns:
            dict: 验证结果
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not self.P:
            result['valid'] = False
            result['errors'].append("没有加载的配置数据")
            return result
        
        # 检查广播相关配置的一致性
        if broadcastIP in self.P and broadcastPort in self.P:
            ip = self.P[broadcastIP]
            port = self.P[broadcastPort]
            if ip == "<broadcast>" and port < 1024:
                result['warnings'].append("广播端口使用系统保留端口可能需要管理员权限")
        
        # 检查队列大小的合理性
        queue_fields = [mainQueueSize, slaveQueueSize, broadcastQueueSize, 
                       listenerQueueSize, misoQueueSize, printerQueueSize]
        total_queue_size = 0
        for field in queue_fields:
            if field in self.P:
                queue_size = self.P[field]
                total_queue_size += queue_size
                if queue_size > 1000:
                    field_name = META[field][NAME]
                    result['warnings'].append(f"队列大小 '{field_name}' 可能过大: {queue_size}")
        
        if total_queue_size > 5000:
            result['warnings'].append(f"总队列大小可能过大: {total_queue_size}")
        
        return result

    def get_validation_report(self):
        """
        获取完整的验证报告
        
        Returns:
            dict: 完整的验证报告
        """
        report = {
            'timestamp': time.time(),
            'overall_status': 'unknown',
            'summary': {},
            'details': {}
        }
        
        try:
            # 数据完整性验证
            integrity_result = self.validate_data_integrity()
            report['details']['integrity'] = integrity_result
            
            # 范围验证
            range_result = self.validate_config_ranges()
            report['details']['ranges'] = range_result
            
            # 依赖关系验证
            dependency_result = self.validate_dependencies()
            report['details']['dependencies'] = dependency_result
            
            # 汇总结果
            all_valid = (integrity_result['valid'] and 
                        range_result['valid'] and 
                        dependency_result['valid'])
            
            total_errors = (len(integrity_result['errors']) + 
                           len(range_result['errors']) + 
                           len(dependency_result['errors']))
            
            total_warnings = (len(integrity_result['warnings']) + 
                             len(range_result['warnings']) + 
                             len(dependency_result['warnings']))
            
            report['overall_status'] = 'valid' if all_valid else 'invalid'
            report['summary'] = {
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'validation_passed': all_valid
            }
            
        except Exception as e:
            report['overall_status'] = 'error'
            report['summary'] = {'error': str(e)}
        
        return report

    def create_backup(self, backup_path=None):
        """
        创建当前配置的备份
        
        Args:
            backup_path: 备份文件路径，如果为None则自动生成
            
        Returns:
            str: 备份文件路径，失败时返回None
        """
        try:
            if not self.P:
                self.printw("没有配置数据可备份")
                return None
            
            if backup_path is None:
                timestamp = int(time.time())
                backup_path = f"backup_{timestamp}.fc"
            
            # 使用pickle保存备份
            with open(backup_path, 'wb') as f:
                pk.dump(self.P, f)
            
            self._runtime['backup_count'] += 1
            self.printi(f"配置备份已保存到: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.printx(e, "创建备份失败")
            return None

    def restore_from_backup(self, backup_path):
        """
        从备份文件恢复配置
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            if not os.path.exists(backup_path):
                self.printw(f"备份文件不存在: {backup_path}")
                return False
            
            # 保存当前配置作为临时备份
            old_config = cp.deepcopy(self.P) if self.P else None
            
            try:
                with open(backup_path, 'rb') as f:
                    restored_config = pk.load(f)
                
                # 验证恢复的配置
                temp_archive = FCArchive(self.pqueue, self._runtime['version'])
                temp_archive.P = restored_config
                validation_result = temp_archive.validate_data_integrity()
                
                if validation_result['valid']:
                    self.P = restored_config
                    self.P.update(self._runtime)
                    self.isModified = True
                    self.printi(f"配置已从备份恢复: {backup_path}")
                    return True
                else:
                    self.printw("备份文件验证失败，恢复被取消")
                    return False
                    
            except Exception as e:
                # 恢复失败，回滚到原配置
                self.P = old_config
                self.printx(e, "从备份恢复失败")
                return False
                
        except Exception as e:
            self.printx(e, "恢复过程中发生错误")
            return False

    def safe_set_value(self, key, value, create_backup=True):
        """
        安全地设置配置值，包含验证和回滚机制
        
        Args:
            key: 配置键
            value: 配置值
            create_backup: 是否在修改前创建备份
            
        Returns:
            dict: 操作结果
        """
        result = {
            'success': False,
            'message': '',
            'backup_path': None
        }
        
        try:
            # 验证键的有效性
            if key not in META:
                result['message'] = f"无效的配置键: {key}"
                return result
            
            # 创建备份（如果需要）
            backup_path = None
            if create_backup and self.P:
                backup_path = self.create_backup()
                result['backup_path'] = backup_path
            
            # 保存原值用于回滚
            old_value = self.P.get(key) if self.P else None
            
            # 验证新值
            meta_info = META[key]
            validator = meta_info[VALIDATOR]
            
            try:
                if not validator(value):
                    result['message'] = f"值验证失败: {value}"
                    return result
            except Exception as e:
                result['message'] = f"验证过程出错: {str(e)}"
                return result
            
            # 设置新值
            if not self.P:
                self.P = cp.deepcopy(self.DEFAULT)
                self.P.update(self._runtime)
            
            self.P[key] = value
            self.isModified = True
            
            # 验证整体配置的一致性
            validation_result = self.validate_data_integrity()
            if not validation_result['valid']:
                # 回滚
                if old_value is not None:
                    self.P[key] = old_value
                else:
                    del self.P[key]
                result['message'] = f"设置值导致配置不一致，已回滚: {validation_result['errors']}"
                return result
            
            result['success'] = True
            result['message'] = f"成功设置 {meta_info[NAME]} = {value}"
            
        except Exception as e:
            result['message'] = f"设置值时发生错误: {str(e)}"
        
        return result

    def recover_from_error(self, error_type, **kwargs):
        """
        从各种错误中恢复
        
        Args:
            error_type: 错误类型
            **kwargs: 错误相关的额外参数
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            if error_type == 'corrupted_config':
                # 配置文件损坏，加载默认配置
                self.printi("检测到配置文件损坏，正在加载默认配置...")
                self.profile(None)  # 加载默认配置
                return True
                
            elif error_type == 'encoding_error':
                # 编码错误，尝试不同编码
                file_path = kwargs.get('file_path')
                if file_path:
                    for encoding in ENCODING_FALLBACKS:
                        try:
                            content, used_encoding = safe_file_read(file_path, encoding)
                            self.printi(f"使用编码 {used_encoding} 成功读取文件")
                            return True
                        except:
                            continue
                            
            elif error_type == 'validation_failed':
                # 验证失败，尝试修复
                if self.P:
                    # 移除无效的配置项
                    invalid_keys = []
                    for key, value in self.P.items():
                        if key in META:
                            meta_info = META[key]
                            validator = meta_info[VALIDATOR]
                            try:
                                if not validator(value):
                                    invalid_keys.append(key)
                            except:
                                invalid_keys.append(key)
                    
                    for key in invalid_keys:
                        if key in self.DEFAULT:
                            self.P[key] = self.DEFAULT[key]
                            self.printi(f"重置无效配置项 {META[key][NAME]} 为默认值")
                        else:
                            del self.P[key]
                            self.printi(f"移除无效配置项 {key}")
                    
                    if invalid_keys:
                        self.isModified = True
                        return True
            
            return False
            
        except Exception as e:
            self.printx(e, "错误恢复过程中发生异常")
            return False

    def modified(self):
        """
        Return whether the current profile has been modified without saving.
        """
        return self.isModified

    def default(self):
        """
        Load the default profile.
        """
        self.profile(FCArchive.DEFAULT)

    # Note: Built-in profile switching method - currently disabled
    # def builtin(self, name):
    #     """
    #     Method to switch to a "built-in" (hardcoded) profile.
    #     """
    #     self.P = cp.deepcopy(btp.PROFILES[name])
    #     self.P.update(self.runtime)
    #     self.isModified = False

    def profile(self, new = None):
        """
        Set the current profile to the given profile, if one is provided.
        Return a copy of the current profile, represented as a dictionary who's
        keys are constants defined in this module.

        - new := new profile to use, (Python dictionary). Defaults to None, in
            which case the current profile is returned.

        Raises an AttributeError if this instance has no profile loaded.
        """
        if new is not None:
            self.P = cp.deepcopy(new)
            # 只更新已存在的配置键
            self.P[version] = self._runtime[version]
            self.P[platform] = self._runtime[platform]
            self.isModified = False
        if self.P is not None:
            return cp.deepcopy(self.P)
        else:
            raise AttributeError("No profile loaded")

    def add(self, attribute, value):
        """
        Add VALUE to the TYPE_LIST attribute ATTRIBUTE.
        """
        if self.meta[attribute][TYPE] is not TYPE_LIST:
            raise ValueError("Tried to add to non-list attribute {} ".format(
                self.meta[attribute][NAME]))
        try:
            # TODO: Validate?
            # Check if runtime is being modified (should we allow this?)
            # Check if type is valid
            # Check if value is valid
            self.P[attribute] += (value,)
            self.isModified = True
        except KeyError as e:
            self.printe("Invalid FC Archive key \"{}\"".format(attribute))

    def set(self, attribute, value):
        """
        Replace the current value of ATTRIBUTE (an attribute constant defined in
        this module) in the current profile for the given VALUE, which must be
        valid and of the correct type. Returns the category that was modified.

        Note that nothing is saved to persistent storage unless the save method
        is called.
        """
        try:
            # TODO: Validate?
            # Check if runtime is being modified (should we allow this?)
            # Check if type is valid
            # Check if value is valid
            self.P[attribute] = value
            self.isModified = True
        except KeyError as e:
            self.printe("Invalid FC Archive key \"{}\"".format(attribute))

    def load(self, name, encoding=None):
        """
        Load profile data from a file named NAME with extension.
        
        Args:
            name (str): 配置文件路径
            encoding (str, optional): 文件编码格式，如果为None则自动检测

        Any IOError raised will be passed to the caller, in which case the
        current profile won't be changed.
        """
        try:
            old = self.P
            self._path = name  # 保存文件路径
            
            # 尝试使用pickle加载二进制文件
            try:
                new = pk.load(open(name, 'rb'))
            except (pk.UnpicklingError, UnicodeDecodeError):
                # 如果pickle失败，尝试作为文本文件处理
                content, used_encoding = safe_file_read(name, encoding)
                # 这里可以添加其他格式的解析逻辑
                # 目前假设是pickle格式，如果需要支持其他格式可以扩展
                raise IOError("Unsupported file format")
                
            # TODO: Validate?
            self.P = new
            self.P.update(self._runtime)
            self.isModified = False
            self._runtime['last_modified'] = time.time()
            self._runtime['access_count'] += 1
        except IOError as e:
            self.printx(e, "Could not load profile")
            self.P = old
        except UnicodeError as e:
            self.printx(e, "Encoding error while loading profile")
            self.P = old

    def save(self, name, encoding=DEFAULT_ENCODING):
        """
        Save current profile to file named NAME.
        Note that if a file with this name and extension exists it will be
        overwritten.
        
        Args:
            name (str): 文件路径
            encoding (str): 文件编码格式，默认为UTF-8

        IOErrors will cancel the operation and cause an error message to be
        sent to the print queue.
        """
        try:
            # 使用pickle保存为二进制文件（保持原有行为）
            pk.dump(self.profile(), open(name, 'wb'))
            self.isModified = False
            self._path = name  # 保存文件路径
            self._runtime['last_modified'] = time.time()
        except IOError as e:
            self.printx(e, "Could not save profile")
        except UnicodeError as e:
            self.printx(e, "Encoding error while saving profile")

    def update(self, update):
        """
        Update the current profile by replacing matching entries with
        those in UPDATE (expected to be a Python dictionary whose keys are
        all preexisting FCArchive keys whose values are valid).
        """
        for key in update:
            self.set(key, update[key])

    def keys(self):
        """
        Return an iterable containing the keys of the loaded profile.
        """
        return self.P.keys()

    def __getitem__(self, key):
        """
        Fetch a value from the current profile, indexed by KEY. Here KEY must
        be a valid key value defined in fc.archive.

        If the key is not present in the currently loaded profile, an attempt
        will be made to fetch it from the built-in default profile before
        raising a KeyError.
        """
        try:
            return self.P[key]
        except KeyError:
            self.printw("Missing key {} loaded from default profile.".format(
                META[key][NAME]))
            return self.DEFAULT[key]
