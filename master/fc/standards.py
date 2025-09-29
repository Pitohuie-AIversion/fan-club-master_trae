################################################################################
## Project: Fanclub Mark IV "Master" base window  ## File: standards.py       ##
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY ## ADVANCED SYSTEMS LABORATORY ##                     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __  __   __                  ##
##                  | | |  | |  | T_| | || |    |  ||_ | | _|                 ##
##                  | _ |  |T|  |  |  |  _|      ||   \\_//                   ##
##                  || || |_ _| |_|_| |_| _|    |__|  |___|                   ##
##                                                                            ##
##----------------------------------------------------------------------------##
## zhaoyang                   ## <mzymuzhaoyang@gmail.com>   ##              ##
## dashuai                    ## <dschen2018@gmail.com>      ##              ##
##                            ##                             ##              ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Repository of shared constant values to be used for communication across
 + processes and objects.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

""" INTER PROCESS COMMUNICATIONS STANDARD ++++++++++++++++++++++++++++++++++++++

                 ------ CONTROL PIPE ------------------------
            +----> [control vector (DC assignments) ] ----------->+
            ^    --------------------------------------------     |
            |                                                     |
            |    ------ COMMAND PIPE ------------------------     |
            | +--> [command vector (ADD, REBOOT, FIRMW...)] --->+ |
            ^ ^  --------------------------------------------   V V
        -----------                                         ------------
       |           |                                       |            |
       | FRONT-END |                                       |  BACK-END  |
       |           |                                       |            |
        -----------                                         ------------
         ^ ^ ^ ^                                               V V V V
         | | | |  ---- FEEDBACK PIPE ------------------------  | | | |
         | | | +<- [feedback vector F (DC's and RPM's)] <------+ | | |
         | | |    -------------------------------------------    | | |
         | | |                                                   | | |
         | | |    ---- SLAVE PIPE ---------------------------      | |
         | | +<--- [slave vector S (slave i's, statuses...)] <-----+ |
         | |      -------------------------------------------        |
         | |                                                         |
         | |      ---- NETWORK PIPE -------------------------        |
         | +<----- [network vector N (global IP's and ports)] <------+
         |        -------------------------------------------        |
         |                                                           |
         |        ==== PRINT QUEUE ==========================        |
         +<------- [print messages] <--------------------------------+
                  ===========================================

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

# Network diagnostics data standardization implemented below (lines 647-792)
# DC normalization and formats standardization implemented below (lines 75-262)

# TODO: Check performance w/ DC fan selections being Strings
# Timing for multiprocessing back-ends:
MP_STOP_TIMEOUT_S = 0.5

# Number of decimals to have for duty cyle. Indicates by which power of 10 to
# normalize
# Default value - can be overridden by profile configuration
DC_DECIMALS = 2
DC_NORMALIZER = 10.0**(DC_DECIMALS + 2) # .... Divide by this to normalize

def get_dc_normalizer(archive=None):
    """
    Get the DC normalizer value from archive configuration if available,
    otherwise use the default value.
    """
    if archive is not None:
        try:
            decimals = archive['dcDecimals']
            return 10.0**(decimals + 2)
        except (KeyError, TypeError):
            pass
    return DC_NORMALIZER


# DC DATA STANDARDIZATION ENHANCEMENTS ########################################
"""
Enhanced DC (Direct Current) data standardization with comprehensive validation,
error handling, and industry standard compliance.
"""

# DC data validation constants
DC_MIN_VOLTAGE = 0.0          # Minimum acceptable DC voltage
DC_MAX_VOLTAGE = 48.0         # Maximum acceptable DC voltage (industry standard)
DC_MIN_CURRENT = 0.0          # Minimum acceptable DC current
DC_MAX_CURRENT = 20.0         # Maximum acceptable DC current (amperes)
DC_MIN_POWER = 0.0            # Minimum acceptable DC power
DC_MAX_POWER = 1000.0         # Maximum acceptable DC power (watts)
DC_TOLERANCE = 0.001          # Tolerance for floating point comparisons

# DC status codes for standardized reporting
DC_STATUS_NORMAL = 80001      # DC values within normal range
DC_STATUS_WARNING = 80002     # DC values approaching limits
DC_STATUS_CRITICAL = 80003    # DC values exceeding safe limits
DC_STATUS_FAULT = 80004       # DC system fault detected

DC_STATUS_MESSAGES = {
    DC_STATUS_NORMAL: "Normal Operation",
    DC_STATUS_WARNING: "Warning - Approaching Limits",
    DC_STATUS_CRITICAL: "Critical - Exceeding Safe Limits", 
    DC_STATUS_FAULT: "System Fault Detected"
}

def validate_dc_input(value, min_val, max_val, param_name):
    """
    Validate DC input parameter according to industry standards.
    
    Args:
        value: The value to validate
        min_val (float): Minimum acceptable value
        max_val (float): Maximum acceptable value
        param_name (str): Parameter name for error messages
        
    Returns:
        float: Validated and converted value
        
    Raises:
        ValueError: If value is invalid
        TypeError: If value cannot be converted to float
    """
    try:
        # Convert to float if possible
        float_value = float(value)
        
        # Check for NaN or infinity
        if not (float_value == float_value):  # NaN check
            raise ValueError(f"{param_name} cannot be NaN")
        if float_value == float('inf') or float_value == float('-inf'):
            raise ValueError(f"{param_name} cannot be infinite")
            
        # Range validation
        if float_value < min_val - DC_TOLERANCE:
            raise ValueError(f"{param_name} ({float_value}) below minimum ({min_val})")
        if float_value > max_val + DC_TOLERANCE:
            raise ValueError(f"{param_name} ({float_value}) above maximum ({max_val})")
            
        return float_value
        
    except (TypeError, ValueError) as e:
        if "could not convert" in str(e).lower():
            raise TypeError(f"Cannot convert {param_name} to numeric value: {value}")
        raise

def standardize_dc_data(voltage, current, power=None, temperature=None):
    """
    Standardize DC data according to industry standards with comprehensive validation.
    
    Args:
        voltage (float): DC voltage in volts
        current (float): DC current in amperes  
        power (float, optional): DC power in watts (calculated if not provided)
        temperature (float, optional): Operating temperature in Celsius
        
    Returns:
        dict: Standardized DC data with status and diagnostics
        
    Raises:
        ValueError: If input parameters are invalid
        TypeError: If input parameters have wrong types
    """
    try:
        # Validate input parameters
        voltage = validate_dc_input(voltage, DC_MIN_VOLTAGE, DC_MAX_VOLTAGE, "voltage")
        current = validate_dc_input(current, DC_MIN_CURRENT, DC_MAX_CURRENT, "current")
        
        # Calculate power if not provided
        if power is None:
            calculated_power = voltage * current
        else:
            power = validate_dc_input(power, DC_MIN_POWER, DC_MAX_POWER, "power")
            calculated_power = power
            
            # Verify power calculation consistency (within 5% tolerance)
            expected_power = voltage * current
            if abs(calculated_power - expected_power) > (expected_power * 0.05):
                raise ValueError(f"Power inconsistency: provided {calculated_power}W, "
                               f"calculated {expected_power:.2f}W")
        
        # Validate temperature if provided
        if temperature is not None:
            temperature = validate_dc_input(temperature, -40.0, 85.0, "temperature")
            
        # Normalize values to 0-1 range based on maximum values
        normalized_voltage = voltage / DC_MAX_VOLTAGE
        normalized_current = current / DC_MAX_CURRENT
        normalized_power = calculated_power / DC_MAX_POWER
        
        # Determine status based on operating conditions
        status = DC_STATUS_NORMAL
        warnings = []
        
        # Check for warning conditions (>80% of maximum)
        if voltage > DC_MAX_VOLTAGE * 0.8:
            status = max(status, DC_STATUS_WARNING)
            warnings.append("High voltage")
        if current > DC_MAX_CURRENT * 0.8:
            status = max(status, DC_STATUS_WARNING)
            warnings.append("High current")
        if calculated_power > DC_MAX_POWER * 0.8:
            status = max(status, DC_STATUS_WARNING)
            warnings.append("High power")
            
        # Check for critical conditions (>95% of maximum)
        if voltage > DC_MAX_VOLTAGE * 0.95:
            status = DC_STATUS_CRITICAL
        if current > DC_MAX_CURRENT * 0.95:
            status = DC_STATUS_CRITICAL
        if calculated_power > DC_MAX_POWER * 0.95:
            status = DC_STATUS_CRITICAL
            
        # Check for fault conditions
        if voltage < DC_MIN_VOLTAGE + DC_TOLERANCE and current > DC_TOLERANCE:
            status = DC_STATUS_FAULT
            warnings.append("Voltage fault with current flow")
        if current < DC_MIN_CURRENT + DC_TOLERANCE and voltage > DC_TOLERANCE:
            # This might be normal for open circuit, so just note it
            warnings.append("Open circuit detected")
            
        # Calculate efficiency if temperature is available
        efficiency = None
        if temperature is not None:
            # Simple efficiency model based on temperature
            # Efficiency decreases with temperature above 25°C
            temp_factor = max(0.7, 1.0 - (max(0, temperature - 25) * 0.002))
            efficiency = min(1.0, temp_factor)
            
        # Create standardized data structure
        standardized_data = {
            'raw_values': {
                'voltage': round(voltage, DC_DECIMALS),
                'current': round(current, DC_DECIMALS),
                'power': round(calculated_power, DC_DECIMALS),
                'temperature': round(temperature, 1) if temperature is not None else None
            },
            'normalized_values': {
                'voltage': round(normalized_voltage, DC_DECIMALS),
                'current': round(normalized_current, DC_DECIMALS), 
                'power': round(normalized_power, DC_DECIMALS)
            },
            'status': status,
            'status_message': DC_STATUS_MESSAGES[status],
            'warnings': warnings,
            'efficiency': round(efficiency, 3) if efficiency is not None else None,
            'is_safe': status in [DC_STATUS_NORMAL, DC_STATUS_WARNING],
            'timestamp': None  # To be set by calling code if needed
        }
        
        return standardized_data
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"DC data standardization error: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error in DC data standardization: {e}")

def get_enhanced_dc_normalizer(dc_max, dc_min=0.0, target_range=(0.0, 1.0)):
    """
    Enhanced DC normalizer with configurable input and output ranges.
    
    Args:
        dc_max (float): Maximum input DC value
        dc_min (float): Minimum input DC value (default: 0.0)
        target_range (tuple): Target output range (default: (0.0, 1.0))
        
    Returns:
        function: Enhanced normalization function
        
    Raises:
        ValueError: If parameters are invalid
    """
    try:
        dc_max = float(dc_max)
        dc_min = float(dc_min)
        target_min, target_max = target_range
        
        if dc_max <= dc_min:
            raise ValueError("dc_max must be greater than dc_min")
        if target_max <= target_min:
            raise ValueError("target_max must be greater than target_min")
            
        input_range = dc_max - dc_min
        output_range = target_max - target_min
        
        def enhanced_normalize(dc_value):
            """
            Normalize DC value to target range with bounds checking.
            
            Args:
                dc_value: Value to normalize
                
            Returns:
                float: Normalized value within target range
            """
            try:
                value = float(dc_value)
                # Clamp to input range
                clamped = max(dc_min, min(dc_max, value))
                # Normalize to target range
                normalized = ((clamped - dc_min) / input_range) * output_range + target_min
                return normalized
            except (TypeError, ValueError):
                raise ValueError(f"Cannot normalize invalid DC value: {dc_value}")
                
        return enhanced_normalize
        
    except (TypeError, ValueError) as e:
        raise ValueError(f"Enhanced DC normalizer creation error: {e}")


# Target codes:
TGT_ALL = 4041
TGT_SELECTED = 4042

# NOTE: The purpose of these dictionaries is twofold --first, they allow for
# near constant-time lookup to check whether an integer is a valid code of a
# certain category; second, they allow translation of codes to strings for
# auxiliary printing.
TARGET_CODES = {
    TGT_ALL : "TGT_ALL",
    TGT_SELECTED : "TGR_SELECTED"
}

# Command vectors ##############################################################
# NOTE: Sent through the same channel as control vectors.
# Form:
#
#        D =  [CODE, TARGET_CODE, TARGET_0, TARGET_1,... ]
#              |     |            |---------------------/
#              |     |            |
#              |     |            |
#              |     |            Indices of selected slaves, if applicable
#              |     Whether to apply to all or to a subset of the slaves
#              Command code: ADD, DISCONNECT, REBOOT, etc. (below)
#
#                         either broadcast or targetted "heart beat"
#                         |
#        D =  [CMD_BMODE, BMODE]
#              |          |
#              |          New broadcast mode
#              Set new broadcast mode
#
#        D =  [CMD_FUPDATE_START, TGT_ALL VERSION_NAME, FILE_NAME, SIZE]
#              |                          |             |          |
#              |                          |             |          |
#              |                          |             |          File size (b)
#              |                          |             File name (String)
#              |                          Version name (String)
#              Start firmware update
#
#                       IP address to target
#                       |
#        D =  [CMD_BIP, IP]
#              |
#              |
#              Set new broadcast IP

# Command codes:
CMD_ADD = 3031
CMD_DISCONNECT = 3032
CMD_REBOOT = 3033
CMD_SHUTDOWN = 3035
CMD_FUPDATE_START = 3036 # .............................. Start firmware update
CMD_FUPDATE_STOP = 3037
CMD_STOP = 3038 # ............................................... Stop back-end
CMD_BMODE = 3039  # .............................................. Set broadcast
CMD_BIP = 3040

CMD_N = 3041 # .............................................. Get Network Vector
CMD_S = 3042 # .............................................. Get Slave Vector
CMD_CHASE = 3043 # .......................................... Start CHASE mode
CMD_PERF_STATS = 3044 # ..................................... Get Performance Stats
CMD_PERF_RESET = 3045 # ..................................... Reset Performance Stats
CMD_PERF_ENABLE = 3046 # .................................... Enable Performance Monitoring
CMD_PERF_DISABLE = 3047 # ................................... Disable Performance Monitoring

# Broadcast modes:
BMODE_BROADCAST = 8391
BMODE_TARGETTED = 8392

# INDICES:
CMD_I_CODE = 0
CMD_I_TGT_CODE = 1
CMD_I_TGT_OFFSET = 2

CMD_I_FU_VERSION = 2
CMD_I_FU_FILENAME = 3
CMD_I_FU_FILESIZE = 4

CMD_I_BM_BMODE = 1

CMD_I_BIP_IP = 1

COMMAND_CODES = {
    CMD_ADD : "CMD_ADD",
    CMD_DISCONNECT : "CMD_DISCONNECT",
    CMD_REBOOT : "CMD_REBOOT",
    CMD_SHUTDOWN : "CMD_SHUTDOWN",
    CMD_FUPDATE_START : "CMD_FUPDATE_START",
    CMD_FUPDATE_STOP : "CMD_FUPDATE_STOP",
    CMD_STOP : "CMD_STOP",
    CMD_BMODE : "CMD_BMODE",
    CMD_BIP : "CMD_BIP",
    CMD_N : "CMD_N",
    CMD_S : "CMD_S",
    CMD_CHASE : "CMD_CHASE",
    CMD_PERF_STATS : "CMD_PERF_STATS",
    CMD_PERF_RESET : "CMD_PERF_RESET",
    CMD_PERF_ENABLE : "CMD_PERF_ENABLE",
    CMD_PERF_DISABLE : "CMD_PERF_DISABLE"
}

# Control vectors ##############################################################
# NOTE: Sent through the same channel as command vectors
# NOTE: Here each duty cycle is a float between 0.0 and 1.0, inclusive.
# Form:
#                                                           1st fan selected
#                                                           |2nd fan selected
#                                                           ||
#                                       String of the form "01001..."
#                                       |
# [CTL_DC_SINGLE, TGT_SELECTED, DC, TARGET_0, SEL_0, TARGET_1, SEL_1...]
#  |              |             |   |-------------/ |----------------/
#  |              |             |   |               |
#  |              |             |   |               Data for second target...
#  |              |             |   Index of first target slave, then selection
#  |              |             Target duty cycle (int) (must be normalized)
#  |              Apply command to selected Slaves
#  Control code
#                                                  1st fan selected
#                                                  |2nd fan selected
#                                                  ||
#                              String of the form "01001..."
#                              |
# [CTL_DC_SINGLE, TGT_ALL, DC, SELECTION]
#  |              |        |   |
#  |              |        |   Selected fans
#  |              |        Target duty cycle, as integer (must be normalized)
#  |              Apply to all Slaves
#  Control code
#
# [CTL_DC_VECTOR, TGT_SELECTED, DC_0_0, DC_0_1, DC_0_MF,...DC_N-1_0,...DC_N-1_MF]
#  |                 |         |----------------------/ |----------------/
#  |                 |         |                        |
#  |                 |         |                        DC's for last slave
#  |                 |         Fans of slave 0
#  |                 Whether to apply to all or to a subset of the slaves
#  Control code
#  NOTE: TGT_SELECTED is ignored, as CTL_DC_VECTOR is meant to only use this
#  NOTE: Here all slaves are assumed to have maxFans fans. Inactive fans are
#  expected to be padded with zeros.

# Control codes:
CTL_DC_SINGLE = 5051
CTL_DC_VECTOR = 5052

# Control indices:
CTL_I_CODE = 0
CTL_I_TGT_CODE = 1

CTL_I_SINGLE_DC = 2
CTL_I_SINGLE_ALL_SELECTION = 3

CTL_I_SINGLE_TGT_OFFSET = 3
CTL_I_VECTOR_TGT_OFFSET = 1
CTL_I_VECTOR_DC_OFFSET = 2

CONTROL_CODES = {
    CTL_DC_SINGLE : "CTL_DC_SINGLE",
    CTL_DC_VECTOR : "CTL_DC_VECTOR"
}


# Aggregates:
MESSAGES = {"Add":CMD_ADD, "Disconnect":CMD_DISCONNECT, "Reboot":CMD_REBOOT,
    "Shutdown":CMD_SHUTDOWN}
TARGETS = {"All":TGT_ALL, "Selected":TGT_SELECTED}

CONTROLS = {"Ohno" : 1}#{"DC":CTL_DC}

# Network status vectors #######################################################
# Form:
#      N =    [CONN, IP, BIP, BPORT, LPORT]
#              |     |   |    |       |
#              |     |   |    |       Listener port (int)
#              |     |   |    Broadcast port (int)
#              |     |   Broadcast IP (String)
#              |     Communications IP (String)
#              Connection status (Bool -- connected or not)

# Indices:
NS_LEN = 5
NS_I_CONN, NS_I_IP, NS_I_BIP, NS_I_BPORT, NS_I_LPORT = range(NS_LEN)

# Network Status codes:
NS_CONNECTED = 20001
NS_CONNECTING = 20002
NS_DISCONNECTED = 20003
NS_DISCONNECTING = 20004

NETWORK_STATUSES = {
    NS_CONNECTED : "Connected",
    NS_CONNECTING : "Connecting",
    NS_DISCONNECTED : "Disconnected",
    NS_DISCONNECTING : "Disconnecting",
}

# Slave status codes:
SS_CONNECTED = 30001
SS_KNOWN = 30002
SS_DISCONNECTED = 30003
SS_AVAILABLE = 30004
SS_UPDATING = 30005

SLAVE_STATUSES = {
    SS_CONNECTED : 'Connected',
    SS_KNOWN : 'Known',
    SS_DISCONNECTED : 'Disconnected',
    SS_AVAILABLE : 'Available',
    SS_UPDATING : 'Bootloader'
}

SLAVE_STATUSES_SHORT = {
    SS_CONNECTED : 'CONND',
    SS_KNOWN : 'KNOWN',
    SS_DISCONNECTED : 'DISCN',
    SS_AVAILABLE : 'AVAIL',
    SS_UPDATING : 'BOOTN'
}


# Status foreground colors:
FOREGROUNDS = {
    SS_CONNECTED : '#0e4707',
    SS_KNOWN : '#44370b',
    SS_DISCONNECTED : '#560e0e',
    SS_AVAILABLE : '#666666',
    SS_UPDATING : '#192560'
}
FOREGROUNDS.update({
    NS_CONNECTED : FOREGROUNDS[SS_CONNECTED],
    NS_CONNECTING : FOREGROUNDS[SS_DISCONNECTED],
    NS_DISCONNECTED : FOREGROUNDS[SS_DISCONNECTED],
    NS_DISCONNECTING : FOREGROUNDS[SS_CONNECTED],
})

# Status background colors:
BACKGROUNDS = {
    SS_CONNECTED : '#d1ffcc',
    SS_KNOWN : '#fffaba',
    SS_DISCONNECTED : '#ffd3d3',
    SS_AVAILABLE : '#ededed',
    SS_UPDATING : '#a6c1fc'
}
BACKGROUNDS.update({
    NS_CONNECTED : BACKGROUNDS[SS_CONNECTED],
    NS_CONNECTING : BACKGROUNDS[SS_DISCONNECTED],
    NS_DISCONNECTED : BACKGROUNDS[SS_DISCONNECTED],
    NS_DISCONNECTING : BACKGROUNDS[SS_CONNECTED],
})

# Slave data vectors ###########################################################
# Form:
#
#            S = [INDEX_0, NAME_0, MAC_0, STATUS_0, FANS_0, VERSION_0...]
#                 |        |       |      |         |       |
#                 |        |       |      |         |       Slave 0's version
#                 |        |       |      |         Slave 0's active fans
#                 |        |       |      Slave 0's status
#                 |        |       Slave 0's MAC
#                 |        Slave 0's name
#                 Slave 0's index (should be 0)

# Slave data:
SD_LEN = 6

# Offsets of data per slave in the slave data vector:
SD_INDEX, SD_NAME, SD_MAC, SD_STATUS, SD_FANS, SD_VERSION = range(SD_LEN)

# Feedback vectors #############################################################
# Form:
#
#     F = [RPM_0_1, RPM_0_1, RPM_0_F0, RPM_1_1,... RPM_N-1_FN-1,  DC_0_1,...]
#          |-------------------------/ |------..   |              |-----...
#          |                           |           |     Same pattern, for DC's
#          |                           |           /
#          |                           |   RPM of fan FN-1 of slave N-1
#          |                           RPM's of slave 1
#          RPM's of slave 0
#
# NOTE: Controllers with mappings (i.e grid) need not care about new slaves, for
# they are always unmapped. To get the DC offset they need only get half of the
# feedback vector, and mapped (i.e saved) slaves are guaranteed to be the first
# by the communicator's index assignment.
# Controllers who need to always show all Slaves (i.e live table) may track the
# size of the feedback vector, the default slave values (applied to new slaves),
# and the slave vectors.
# NOTE: Values corresponding to non-connected slaves will be set to a negative
# code.
#
# TODO: Need means by which to handle disconnected slaves and diff. fan sizes
RIP = -666
PAD = -69
END = -354

# EXTERNAL CONTROL #############################################################
EX_BROADCAST, EX_LISTENER = 40001, 40002
EX_KEYS = (EX_BROADCAST, EX_LISTENER)
EX_ACTIVE, EX_INACTIVE = True, False
EX_NAME_BROADCAST, EX_NAME_LISTENER = "State Broadcast", "Command Listener"
EX_NAMES = {EX_BROADCAST: EX_NAME_BROADCAST, EX_LISTENER: EX_NAME_LISTENER}

EX_I_IN, EX_I_OUT = 40010, 40011
EX_INDICES = (EX_I_IN, EX_I_OUT)
EX_RIP = "[RIP]"

EX_CMD_SPLITTER = '|'
EX_LIST_SPLITTER = ','
EX_CMD_I_INDEX, EX_CMD_I_CODE = 0, 1
EX_CMD_F, EX_CMD_N, EX_CMD_S = 'F', 'N', 'S' # Get state vectors
EX_CMD_DC_VECTOR = 'D' # Process DC matrix
EX_CMD_UNIFORM = 'U' # Apply DC to al
EX_CMD_PROFILE = 'P' # Profile attribute
EX_CMD_EVALUATE = 'V' # Evaluate Python expression and get result
EX_CMD_RESET = 'R' # Reset input index
EX_CMD_CHASE = 'C' # Start CHASE mode with target RPM

EX_CMD_CODES = (EX_CMD_F, EX_CMD_N, EX_CMD_S, EX_CMD_DC_VECTOR, EX_CMD_UNIFORM,
    EX_CMD_PROFILE, EX_CMD_EVALUATE, EX_CMD_CHASE)

EX_REP_ERROR = 'E'

# NETWORK DIAGNOSTICS DATA STANDARDIZATION ####################################
"""
Network diagnostics data standardization for monitoring and troubleshooting
network communication performance and reliability.
"""

# Network diagnostics vector structure
# Form: ND = [MISO_INDEX, MOSI_INDEX, PACKET_LOSS_COUNT, LATENCY_MS, 
#             THROUGHPUT_KBPS, ERROR_COUNT, RETRY_COUNT, CONNECTION_QUALITY]

# Network diagnostics indices
ND_LEN = 8
ND_I_MISO_INDEX = 0      # Master In Slave Out index
ND_I_MOSI_INDEX = 1      # Master Out Slave In index  
ND_I_PACKET_LOSS = 2     # Packet loss count
ND_I_LATENCY = 3         # Network latency in milliseconds
ND_I_THROUGHPUT = 4      # Throughput in kilobits per second
ND_I_ERROR_COUNT = 5     # Communication error count
ND_I_RETRY_COUNT = 6     # Retry attempt count
ND_I_CONN_QUALITY = 7    # Connection quality percentage (0-100)

# Network diagnostics status codes
ND_STATUS_EXCELLENT = 90001  # Connection quality >= 90%
ND_STATUS_GOOD = 90002       # Connection quality >= 70%
ND_STATUS_FAIR = 90003       # Connection quality >= 50%
ND_STATUS_POOR = 90004       # Connection quality < 50%
ND_STATUS_CRITICAL = 90005   # Connection quality < 20%

NETWORK_DIAGNOSTICS_STATUS = {
    ND_STATUS_EXCELLENT: "Excellent",
    ND_STATUS_GOOD: "Good", 
    ND_STATUS_FAIR: "Fair",
    ND_STATUS_POOR: "Poor",
    ND_STATUS_CRITICAL: "Critical"
}

# Network diagnostics thresholds
ND_LATENCY_THRESHOLD_MS = 100      # Maximum acceptable latency
ND_PACKET_LOSS_THRESHOLD = 5       # Maximum acceptable packet loss percentage
ND_ERROR_RATE_THRESHOLD = 0.01     # Maximum acceptable error rate (1%)

def standardize_network_diagnostics(miso_index, mosi_index, packet_loss_count, 
                                   latency_ms, throughput_kbps, error_count, 
                                   retry_count, total_packets=1000):
    """
    Standardize network diagnostics data according to industry standards.
    
    Args:
        miso_index (int): Master In Slave Out index
        mosi_index (int): Master Out Slave In index
        packet_loss_count (int): Number of lost packets
        latency_ms (float): Network latency in milliseconds
        throughput_kbps (float): Throughput in kilobits per second
        error_count (int): Number of communication errors
        retry_count (int): Number of retry attempts
        total_packets (int): Total packets sent for loss calculation
        
    Returns:
        dict: Standardized network diagnostics data
        
    Raises:
        ValueError: If input parameters are invalid
        TypeError: If input parameters have wrong types
    """
    try:
        # Input validation
        if not isinstance(miso_index, int) or miso_index < 0:
            raise ValueError("MISO index must be a non-negative integer")
        if not isinstance(mosi_index, int) or mosi_index < 0:
            raise ValueError("MOSI index must be a non-negative integer")
        if not isinstance(packet_loss_count, int) or packet_loss_count < 0:
            raise ValueError("Packet loss count must be a non-negative integer")
        if not isinstance(latency_ms, (int, float)) or latency_ms < 0:
            raise ValueError("Latency must be a non-negative number")
        if not isinstance(throughput_kbps, (int, float)) or throughput_kbps < 0:
            raise ValueError("Throughput must be a non-negative number")
        if not isinstance(error_count, int) or error_count < 0:
            raise ValueError("Error count must be a non-negative integer")
        if not isinstance(retry_count, int) or retry_count < 0:
            raise ValueError("Retry count must be a non-negative integer")
        if not isinstance(total_packets, int) or total_packets <= 0:
            raise ValueError("Total packets must be a positive integer")
            
        # Calculate packet loss percentage
        packet_loss_percentage = (packet_loss_count / total_packets) * 100
        
        # Calculate error rate
        error_rate = error_count / max(total_packets, 1)
        
        # Calculate connection quality based on multiple factors
        quality_score = 100.0
        
        # Deduct points for packet loss
        if packet_loss_percentage > 0:
            quality_score -= min(packet_loss_percentage * 10, 50)
            
        # Deduct points for high latency
        if latency_ms > ND_LATENCY_THRESHOLD_MS:
            latency_penalty = min((latency_ms - ND_LATENCY_THRESHOLD_MS) / 10, 30)
            quality_score -= latency_penalty
            
        # Deduct points for errors
        if error_rate > 0:
            error_penalty = min(error_rate * 1000, 20)
            quality_score -= error_penalty
            
        # Ensure quality score is within bounds
        connection_quality = max(0, min(100, quality_score))
        
        # Determine status based on connection quality
        if connection_quality >= 90:
            status = ND_STATUS_EXCELLENT
        elif connection_quality >= 70:
            status = ND_STATUS_GOOD
        elif connection_quality >= 50:
            status = ND_STATUS_FAIR
        elif connection_quality >= 20:
            status = ND_STATUS_POOR
        else:
            status = ND_STATUS_CRITICAL
            
        # Create standardized diagnostics vector
        diagnostics_vector = [
            miso_index,
            mosi_index,
            packet_loss_count,
            round(latency_ms, 2),
            round(throughput_kbps, 2),
            error_count,
            retry_count,
            round(connection_quality, 1)
        ]
        
        return {
            'vector': diagnostics_vector,
            'status': status,
            'status_text': NETWORK_DIAGNOSTICS_STATUS[status],
            'packet_loss_percentage': round(packet_loss_percentage, 2),
            'error_rate': round(error_rate, 4),
            'is_healthy': (packet_loss_percentage <= ND_PACKET_LOSS_THRESHOLD and 
                          latency_ms <= ND_LATENCY_THRESHOLD_MS and 
                          error_rate <= ND_ERROR_RATE_THRESHOLD)
        }
        
    except (TypeError, ValueError) as e:
        raise ValueError(f"Network diagnostics standardization error: {e}")
    except Exception as e:
         raise RuntimeError(f"Unexpected error in network diagnostics standardization: {e}")

# SLAVE DISCONNECTION EXCEPTION HANDLING ######################################
"""
Comprehensive exception handling for slave disconnection scenarios with
data cleanup, state management, and recovery procedures.
"""

# Disconnection status codes
DISC_STATUS_NORMAL = 70001       # Normal disconnection
DISC_STATUS_TIMEOUT = 70002      # Disconnection due to timeout
DISC_STATUS_ERROR = 70003        # Disconnection due to error
DISC_STATUS_FORCED = 70004       # Forced disconnection
DISC_STATUS_NETWORK = 70005      # Network-related disconnection

DISCONNECTION_STATUS = {
    DISC_STATUS_NORMAL: "Normal Disconnection",
    DISC_STATUS_TIMEOUT: "Timeout Disconnection", 
    DISC_STATUS_ERROR: "Error-based Disconnection",
    DISC_STATUS_FORCED: "Forced Disconnection",
    DISC_STATUS_NETWORK: "Network Disconnection"
}

# Disconnection cleanup priorities
CLEANUP_PRIORITY_CRITICAL = 1   # Critical data that must be preserved
CLEANUP_PRIORITY_HIGH = 2       # Important data that should be preserved
CLEANUP_PRIORITY_MEDIUM = 3     # Standard data cleanup
CLEANUP_PRIORITY_LOW = 4        # Optional cleanup

class SlaveDisconnectionHandler:
    """
    Handles slave disconnection scenarios with comprehensive cleanup and state management.
    """
    
    def __init__(self):
        self.cleanup_registry = {}
        self.state_backup = {}
        self.recovery_callbacks = []
        
    def register_cleanup_handler(self, handler_id, cleanup_func, priority=CLEANUP_PRIORITY_MEDIUM):
        """
        Register a cleanup handler for disconnection scenarios.
        
        Args:
            handler_id (str): Unique identifier for the handler
            cleanup_func (callable): Function to call during cleanup
            priority (int): Cleanup priority (lower numbers = higher priority)
            
        Raises:
            ValueError: If handler_id already exists or parameters are invalid
        """
        if not isinstance(handler_id, str) or not handler_id.strip():
            raise ValueError("Handler ID must be a non-empty string")
        if not callable(cleanup_func):
            raise ValueError("Cleanup function must be callable")
        if handler_id in self.cleanup_registry:
            raise ValueError(f"Handler ID '{handler_id}' already registered")
            
        self.cleanup_registry[handler_id] = {
            'function': cleanup_func,
            'priority': priority,
            'registered_at': None  # To be set by calling code
        }
        
    def backup_slave_state(self, slave_id, state_data):
        """
        Backup slave state data before disconnection.
        
        Args:
            slave_id (str): Unique slave identifier
            state_data (dict): State data to backup
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(slave_id, str) or not slave_id.strip():
            raise ValueError("Slave ID must be a non-empty string")
        if not isinstance(state_data, dict):
            raise ValueError("State data must be a dictionary")
            
        self.state_backup[slave_id] = {
            'data': state_data.copy(),
            'backup_time': None,  # To be set by calling code
            'status': 'backed_up'
        }
        
    def handle_disconnection(self, slave_id, disconnection_type=DISC_STATUS_NORMAL, 
                           error_details=None, preserve_state=True):
        """
        Handle slave disconnection with comprehensive cleanup and state management.
        
        Args:
            slave_id (str): Unique slave identifier
            disconnection_type (int): Type of disconnection
            error_details (str, optional): Error details if applicable
            preserve_state (bool): Whether to preserve state for recovery
            
        Returns:
            dict: Disconnection handling results
            
        Raises:
            ValueError: If parameters are invalid
        """
        try:
            if not isinstance(slave_id, str) or not slave_id.strip():
                raise ValueError("Slave ID must be a non-empty string")
            if disconnection_type not in DISCONNECTION_STATUS:
                raise ValueError(f"Invalid disconnection type: {disconnection_type}")
                
            results = {
                'slave_id': slave_id,
                'disconnection_type': disconnection_type,
                'status_message': DISCONNECTION_STATUS[disconnection_type],
                'error_details': error_details,
                'cleanup_results': {},
                'state_preserved': False,
                'recovery_possible': False
            }
            
            # Preserve state if requested and not already backed up
            if preserve_state and slave_id not in self.state_backup:
                try:
                    # Create minimal state backup
                    minimal_state = {
                        'slave_id': slave_id,
                        'disconnection_type': disconnection_type,
                        'last_known_status': 'disconnected'
                    }
                    self.backup_slave_state(slave_id, minimal_state)
                    results['state_preserved'] = True
                except Exception as e:
                    results['cleanup_results']['state_backup_error'] = str(e)
                    
            # Execute cleanup handlers in priority order
            sorted_handlers = sorted(
                self.cleanup_registry.items(),
                key=lambda x: x[1]['priority']
            )
            
            for handler_id, handler_info in sorted_handlers:
                try:
                    cleanup_result = handler_info['function'](slave_id, disconnection_type)
                    results['cleanup_results'][handler_id] = {
                        'status': 'success',
                        'result': cleanup_result
                    }
                except Exception as e:
                    results['cleanup_results'][handler_id] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    
            # Determine if recovery is possible
            critical_failures = [
                result for result in results['cleanup_results'].values()
                if result['status'] == 'error'
            ]
            
            results['recovery_possible'] = (
                len(critical_failures) == 0 and 
                results['state_preserved'] and
                disconnection_type in [DISC_STATUS_NORMAL, DISC_STATUS_TIMEOUT]
            )
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"Disconnection handling error for slave {slave_id}: {e}")
            
    def attempt_recovery(self, slave_id):
        """
        Attempt to recover a disconnected slave using backed up state.
        
        Args:
            slave_id (str): Unique slave identifier
            
        Returns:
            dict: Recovery attempt results
            
        Raises:
            ValueError: If slave_id is invalid or no backup exists
        """
        try:
            if not isinstance(slave_id, str) or not slave_id.strip():
                raise ValueError("Slave ID must be a non-empty string")
            if slave_id not in self.state_backup:
                raise ValueError(f"No state backup found for slave {slave_id}")
                
            backup_info = self.state_backup[slave_id]
            
            recovery_results = {
                'slave_id': slave_id,
                'recovery_attempted': True,
                'backup_data': backup_info['data'],
                'recovery_success': False,
                'callback_results': {}
            }
            
            # Execute recovery callbacks
            for i, callback in enumerate(self.recovery_callbacks):
                try:
                    callback_result = callback(slave_id, backup_info['data'])
                    recovery_results['callback_results'][f'callback_{i}'] = {
                        'status': 'success',
                        'result': callback_result
                    }
                except Exception as e:
                    recovery_results['callback_results'][f'callback_{i}'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    
            # Determine overall recovery success
            failed_callbacks = [
                result for result in recovery_results['callback_results'].values()
                if result['status'] == 'error'
            ]
            
            recovery_results['recovery_success'] = len(failed_callbacks) == 0
            
            # Clean up backup if recovery successful
            if recovery_results['recovery_success']:
                del self.state_backup[slave_id]
                
            return recovery_results
            
        except Exception as e:
            raise RuntimeError(f"Recovery attempt error for slave {slave_id}: {e}")
            
    def cleanup_expired_backups(self, max_age_seconds=3600):
        """
        Clean up expired state backups to prevent memory leaks.
        
        Args:
            max_age_seconds (int): Maximum age of backups in seconds
            
        Returns:
            int: Number of backups cleaned up
        """
        # This would need actual timestamp comparison in real implementation
        # For now, just return 0 as placeholder
        return 0

# Global disconnection handler instance
_global_disconnection_handler = SlaveDisconnectionHandler()

def get_disconnection_handler():
    """
    Get the global disconnection handler instance.
    
    Returns:
        SlaveDisconnectionHandler: Global handler instance
    """
    return _global_disconnection_handler

def standardize_disconnection_event(slave_id, disconnection_type, error_details=None, 
                                   additional_data=None):
    """
    Standardize disconnection event data for consistent reporting and logging.
    
    Args:
        slave_id (str): Unique slave identifier
        disconnection_type (int): Type of disconnection
        error_details (str, optional): Error details if applicable
        additional_data (dict, optional): Additional event data
        
    Returns:
        dict: Standardized disconnection event data
        
    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not isinstance(slave_id, str) or not slave_id.strip():
            raise ValueError("Slave ID must be a non-empty string")
        if disconnection_type not in DISCONNECTION_STATUS:
            raise ValueError(f"Invalid disconnection type: {disconnection_type}")
            
        event_data = {
            'event_type': 'slave_disconnection',
            'slave_id': slave_id,
            'disconnection_type': disconnection_type,
            'status_message': DISCONNECTION_STATUS[disconnection_type],
            'error_details': error_details,
            'severity': _get_disconnection_severity(disconnection_type),
            'requires_attention': disconnection_type in [DISC_STATUS_ERROR, DISC_STATUS_FORCED],
            'timestamp': None,  # To be set by calling code
            'additional_data': additional_data or {}
        }
        
        return event_data
        
    except Exception as e:
        raise ValueError(f"Disconnection event standardization error: {e}")

def _get_disconnection_severity(disconnection_type):
    """
    Get severity level for disconnection type.
    
    Args:
        disconnection_type (int): Type of disconnection
        
    Returns:
        str: Severity level
    """
    severity_map = {
        DISC_STATUS_NORMAL: 'info',
        DISC_STATUS_TIMEOUT: 'warning',
        DISC_STATUS_ERROR: 'error',
        DISC_STATUS_FORCED: 'warning',
        DISC_STATUS_NETWORK: 'warning'
    }
    return severity_map.get(disconnection_type, 'unknown')

# DATA VALIDATION AND FORMAT CHECKING ########################################
"""
Comprehensive data validation and format checking functions to ensure all
standardized data complies with industry standards and system requirements.
"""

import re
from typing import Any, Dict, List, Union, Optional

# Validation result codes
VALIDATION_SUCCESS = 60001
VALIDATION_WARNING = 60002
VALIDATION_ERROR = 60003
VALIDATION_CRITICAL = 60004

VALIDATION_STATUS = {
    VALIDATION_SUCCESS: "Validation Successful",
    VALIDATION_WARNING: "Validation Warning",
    VALIDATION_ERROR: "Validation Error", 
    VALIDATION_CRITICAL: "Critical Validation Failure"
}

# Industry standard data formats
IEEE_754_FLOAT_PATTERN = r'^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$'
SLAVE_ID_PATTERN = r'^[A-Za-z0-9_-]{1,32}$'
TIMESTAMP_PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$'

class DataValidator:
    """
    Comprehensive data validator for standardized system data.
    """
    
    def __init__(self):
        self.validation_rules = {}
        self.format_checkers = {}
        self._register_default_rules()
        
    def _register_default_rules(self):
        """Register default validation rules for common data types."""
        
        # Network diagnostics validation rules
        self.validation_rules['network_diagnostics'] = {
            'required_fields': ['vector', 'status', 'status_text'],
            'vector_length': ND_LEN,
            'status_codes': list(NETWORK_DIAGNOSTICS_STATUS.keys()),
            'numeric_fields': ['vector'],
            'range_checks': {
                'latency': (0, 10000),  # 0-10 seconds
                'throughput': (0, 1000000),  # 0-1Gbps
                'connection_quality': (0, 100)
            }
        }
        
        # DC data validation rules
        self.validation_rules['dc_data'] = {
            'required_fields': ['raw_values', 'normalized_values', 'status'],
            'status_codes': list(DC_STATUS_MESSAGES.keys()),
            'numeric_fields': ['raw_values', 'normalized_values'],
            'range_checks': {
                'voltage': (DC_MIN_VOLTAGE, DC_MAX_VOLTAGE),
                'current': (DC_MIN_CURRENT, DC_MAX_CURRENT),
                'power': (DC_MIN_POWER, DC_MAX_POWER)
            }
        }
        
        # Disconnection event validation rules
        self.validation_rules['disconnection_event'] = {
            'required_fields': ['event_type', 'slave_id', 'disconnection_type'],
            'status_codes': list(DISCONNECTION_STATUS.keys()),
            'string_fields': ['slave_id', 'status_message'],
            'enum_fields': {
                'severity': ['info', 'warning', 'error', 'critical'],
                'event_type': ['slave_disconnection']
            }
        }
        
    def validate_data_structure(self, data, data_type):
        """
        Validate data structure against defined rules.
        
        Args:
            data: Data to validate
            data_type (str): Type of data being validated
            
        Returns:
            dict: Validation results
        """
        try:
            if data_type not in self.validation_rules:
                return {
                    'status': VALIDATION_ERROR,
                    'message': f"Unknown data type: {data_type}",
                    'errors': [f"No validation rules for data type '{data_type}'"]
                }
                
            rules = self.validation_rules[data_type]
            errors = []
            warnings = []
            
            # Check required fields
            if 'required_fields' in rules:
                for field in rules['required_fields']:
                    if field not in data:
                        errors.append(f"Missing required field: {field}")
                    elif data[field] is None:
                        errors.append(f"Required field '{field}' cannot be None")
                        
            # Check vector length for network diagnostics
            if data_type == 'network_diagnostics' and 'vector' in data:
                if len(data['vector']) != rules['vector_length']:
                    errors.append(f"Vector length {len(data['vector'])} != expected {rules['vector_length']}")
                    
            # Check status codes
            if 'status_codes' in rules and 'status' in data:
                if data['status'] not in rules['status_codes']:
                    errors.append(f"Invalid status code: {data['status']}")
                    
            # Check numeric fields
            if 'numeric_fields' in rules:
                for field in rules['numeric_fields']:
                    if field in data:
                        result = self._validate_numeric_data(data[field], field)
                        if result['errors']:
                            errors.extend(result['errors'])
                        if result['warnings']:
                            warnings.extend(result['warnings'])
                            
            # Check range constraints
            if 'range_checks' in rules:
                for field, (min_val, max_val) in rules['range_checks'].items():
                    if field in data:
                        value = self._extract_numeric_value(data, field)
                        if value is not None:
                            if value < min_val or value > max_val:
                                errors.append(f"{field} value {value} outside range [{min_val}, {max_val}]")
                                
            # Check enum fields
            if 'enum_fields' in rules:
                for field, valid_values in rules['enum_fields'].items():
                    if field in data and data[field] not in valid_values:
                        errors.append(f"Invalid {field} value: {data[field]}")
                        
            # Determine overall status
            if errors:
                status = VALIDATION_CRITICAL if len(errors) > 3 else VALIDATION_ERROR
            elif warnings:
                status = VALIDATION_WARNING
            else:
                status = VALIDATION_SUCCESS
                
            return {
                'status': status,
                'message': VALIDATION_STATUS[status],
                'errors': errors,
                'warnings': warnings,
                'data_type': data_type
            }
            
        except Exception as e:
            return {
                'status': VALIDATION_CRITICAL,
                'message': f"Validation exception: {e}",
                'errors': [str(e)],
                'warnings': []
            }
            
    def _validate_numeric_data(self, data, field_name):
        """Validate numeric data for NaN, infinity, and type correctness."""
        errors = []
        warnings = []
        
        try:
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        if not (value == value):  # NaN check
                            errors.append(f"{field_name}.{key} is NaN")
                        elif value == float('inf') or value == float('-inf'):
                            errors.append(f"{field_name}.{key} is infinite")
            elif isinstance(data, list):
                for i, value in enumerate(data):
                    if isinstance(value, (int, float)):
                        if not (value == value):  # NaN check
                            errors.append(f"{field_name}[{i}] is NaN")
                        elif value == float('inf') or value == float('-inf'):
                            errors.append(f"{field_name}[{i}] is infinite")
            elif isinstance(data, (int, float)):
                if not (data == data):  # NaN check
                    errors.append(f"{field_name} is NaN")
                elif data == float('inf') or data == float('-inf'):
                    errors.append(f"{field_name} is infinite")
                    
        except Exception as e:
            errors.append(f"Error validating numeric data in {field_name}: {e}")
            
        return {'errors': errors, 'warnings': warnings}
        
    def _extract_numeric_value(self, data, field_path):
        """Extract numeric value from nested data structure."""
        try:
            if '.' in field_path:
                parts = field_path.split('.')
                value = data
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        return None
                return value if isinstance(value, (int, float)) else None
            else:
                return data.get(field_path) if isinstance(data, dict) else None
        except:
            return None

def validate_ieee_754_float(value):
    """
    Validate IEEE 754 floating point format compliance.
    
    Args:
        value: Value to validate
        
    Returns:
        dict: Validation result
    """
    try:
        if isinstance(value, str):
            if not re.match(IEEE_754_FLOAT_PATTERN, value):
                return {
                    'valid': False,
                    'error': f"String '{value}' does not match IEEE 754 float pattern"
                }
            try:
                float_val = float(value)
            except ValueError as e:
                return {
                    'valid': False,
                    'error': f"Cannot convert '{value}' to float: {e}"
                }
        elif isinstance(value, (int, float)):
            float_val = float(value)
        else:
            return {
                'valid': False,
                'error': f"Invalid type for float validation: {type(value)}"
            }
            
        # Check for special values
        if not (float_val == float_val):  # NaN
            return {
                'valid': False,
                'error': "Value is NaN (Not a Number)"
            }
        elif float_val == float('inf'):
            return {
                'valid': False,
                'error': "Value is positive infinity"
            }
        elif float_val == float('-inf'):
            return {
                'valid': False,
                'error': "Value is negative infinity"
            }
            
        return {
            'valid': True,
            'value': float_val,
            'error': None
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f"Unexpected error in float validation: {e}"
        }

def validate_slave_id_format(slave_id):
    """
    Validate slave ID format according to system standards.
    
    Args:
        slave_id (str): Slave ID to validate
        
    Returns:
        dict: Validation result
    """
    try:
        if not isinstance(slave_id, str):
            return {
                'valid': False,
                'error': f"Slave ID must be string, got {type(slave_id)}"
            }
            
        if not slave_id.strip():
            return {
                'valid': False,
                'error': "Slave ID cannot be empty or whitespace"
            }
            
        if not re.match(SLAVE_ID_PATTERN, slave_id):
            return {
                'valid': False,
                'error': f"Slave ID '{slave_id}' does not match required pattern"
            }
            
        return {
            'valid': True,
            'normalized_id': slave_id.strip(),
            'error': None
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f"Unexpected error in slave ID validation: {e}"
        }

def validate_timestamp_format(timestamp):
    """
    Validate timestamp format (ISO 8601 compliance).
    
    Args:
        timestamp (str): Timestamp to validate
        
    Returns:
        dict: Validation result
    """
    try:
        if not isinstance(timestamp, str):
            return {
                'valid': False,
                'error': f"Timestamp must be string, got {type(timestamp)}"
            }
            
        if not re.match(TIMESTAMP_PATTERN, timestamp):
            return {
                'valid': False,
                'error': f"Timestamp '{timestamp}' does not match ISO 8601 format"
            }
            
        return {
            'valid': True,
            'normalized_timestamp': timestamp,
            'error': None
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f"Unexpected error in timestamp validation: {e}"
        }

def validate_data_integrity(data_dict):
    """
    Perform comprehensive data integrity validation.
    
    Args:
        data_dict (dict): Data dictionary to validate
        
    Returns:
        dict: Comprehensive validation results
    """
    try:
        results = {
            'overall_status': VALIDATION_SUCCESS,
            'validation_summary': {
                'total_fields': 0,
                'valid_fields': 0,
                'warning_fields': 0,
                'error_fields': 0
            },
            'field_results': {},
            'recommendations': []
        }
        
        validator = DataValidator()
        
        for field_name, field_data in data_dict.items():
            field_result = {
                'status': VALIDATION_SUCCESS,
                'errors': [],
                'warnings': []
            }
            
            # Type-specific validation
            if isinstance(field_data, dict):
                # Try to determine data type and validate accordingly
                if 'vector' in field_data and 'status' in field_data:
                    validation_result = validator.validate_data_structure(field_data, 'network_diagnostics')
                elif 'raw_values' in field_data and 'normalized_values' in field_data:
                    validation_result = validator.validate_data_structure(field_data, 'dc_data')
                elif 'event_type' in field_data and field_data.get('event_type') == 'slave_disconnection':
                    validation_result = validator.validate_data_structure(field_data, 'disconnection_event')
                else:
                    validation_result = {'status': VALIDATION_SUCCESS, 'errors': [], 'warnings': []}
                    
                field_result['status'] = validation_result['status']
                field_result['errors'] = validation_result.get('errors', [])
                field_result['warnings'] = validation_result.get('warnings', [])
                
            results['field_results'][field_name] = field_result
            results['validation_summary']['total_fields'] += 1
            
            if field_result['status'] == VALIDATION_SUCCESS:
                results['validation_summary']['valid_fields'] += 1
            elif field_result['status'] == VALIDATION_WARNING:
                results['validation_summary']['warning_fields'] += 1
            else:
                results['validation_summary']['error_fields'] += 1
                
        # Determine overall status
        if results['validation_summary']['error_fields'] > 0:
            results['overall_status'] = VALIDATION_ERROR
        elif results['validation_summary']['warning_fields'] > 0:
            results['overall_status'] = VALIDATION_WARNING
            
        # Generate recommendations
        if results['validation_summary']['error_fields'] > 0:
            results['recommendations'].append("Address validation errors before proceeding")
        if results['validation_summary']['warning_fields'] > 0:
            results['recommendations'].append("Review validation warnings for potential issues")
            
        return results
        
    except Exception as e:
        return {
            'overall_status': VALIDATION_CRITICAL,
            'error': f"Data integrity validation failed: {e}",
            'validation_summary': {'total_fields': 0, 'valid_fields': 0, 'warning_fields': 0, 'error_fields': 0},
            'field_results': {},
            'recommendations': ["Fix validation system error before proceeding"]
        }

# Global validator instance
_global_validator = DataValidator()

def get_data_validator():
    """
    Get the global data validator instance.
    
    Returns:
        DataValidator: Global validator instance
    """
    return _global_validator

# EXTENSIBLE STANDARDIZATION FRAMEWORK #######################################
"""
Extensible framework for standardizing various data types with plugin support
and dynamic registration capabilities for future data type extensions.
"""

from abc import ABC, abstractmethod
from typing import Type, Callable, Any
import inspect

class StandardizationPlugin(ABC):
    """
    Abstract base class for standardization plugins.
    All standardization plugins must inherit from this class.
    """
    
    @property
    @abstractmethod
    def data_type(self) -> str:
        """Return the data type this plugin handles."""
        pass
        
    @property
    @abstractmethod
    def version(self) -> str:
        """Return the plugin version."""
        pass
        
    @abstractmethod
    def standardize(self, data: Any) -> dict:
        """
        Standardize the input data.
        
        Args:
            data: Raw data to standardize
            
        Returns:
            dict: Standardized data with metadata
        """
        pass
        
    @abstractmethod
    def validate(self, data: Any) -> dict:
        """
        Validate the input data.
        
        Args:
            data: Data to validate
            
        Returns:
            dict: Validation results
        """
        pass
        
    def get_metadata(self) -> dict:
        """
        Get plugin metadata.
        
        Returns:
            dict: Plugin metadata
        """
        return {
            'data_type': self.data_type,
            'version': self.version,
            'class_name': self.__class__.__name__,
            'module': self.__class__.__module__
        }

class NetworkDiagnosticsPlugin(StandardizationPlugin):
    """Plugin for network diagnostics data standardization."""
    
    @property
    def data_type(self) -> str:
        return "network_diagnostics"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    def standardize(self, data: Any) -> dict:
        """Standardize network diagnostics data."""
        if isinstance(data, list) and len(data) >= 7:
            # Handle vector format
            return standardize_network_diagnostics(
                data[0], data[1], data[2], data[3], data[4], data[5], data[6]
            )
        elif isinstance(data, dict):
            # Handle dictionary format
            return standardize_network_diagnostics(
                data.get('miso_index', 0),
                data.get('mosi_index', 0), 
                data.get('packet_loss_count', 0),
                data.get('latency_ms', 0.0),
                data.get('throughput_kbps', 0.0),
                data.get('error_count', 0),
                data.get('retry_count', 0)
            )
        else:
            raise ValueError("Invalid data format for network diagnostics")
        
    def validate(self, data: Any) -> dict:
        """Validate network diagnostics data."""
        validator = get_data_validator()
        return validator.validate_data_structure(data, self.data_type)

class DCDataPlugin(StandardizationPlugin):
    """Plugin for DC data standardization."""
    
    @property
    def data_type(self) -> str:
        return "dc_data"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    def standardize(self, data: Any) -> dict:
        """Standardize DC data."""
        if isinstance(data, dict):
            return standardize_dc_data(
                data.get('voltage'),
                data.get('current'),
                data.get('power'),
                data.get('temperature')
            )
        else:
            raise ValueError("Invalid data format for DC data")
        
    def validate(self, data: Any) -> dict:
        """Validate DC data."""
        validator = get_data_validator()
        return validator.validate_data_structure(data, self.data_type)

class DisconnectionEventPlugin(StandardizationPlugin):
    """Plugin for disconnection event standardization."""
    
    @property
    def data_type(self) -> str:
        return "disconnection_event"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    def standardize(self, data: Any) -> dict:
        """Standardize disconnection event data."""
        if isinstance(data, dict):
            return standardize_disconnection_event(
                data.get('slave_id'),
                data.get('disconnection_type'),
                data.get('error_details'),
                data.get('additional_data')
            )
        else:
            raise ValueError("Invalid data format for disconnection event")
        
    def validate(self, data: Any) -> dict:
        """Validate disconnection event data."""
        validator = get_data_validator()
        return validator.validate_data_structure(data, self.data_type)

class StandardizationFramework:
    """
    Extensible framework for data standardization with plugin support.
    """
    
    def __init__(self):
        self.plugins = {}
        self.transformers = {}
        self.validators = {}
        self._register_default_plugins()
        
    def _register_default_plugins(self):
        """Register default standardization plugins."""
        default_plugins = [
            NetworkDiagnosticsPlugin(),
            DCDataPlugin(),
            DisconnectionEventPlugin()
        ]
        
        for plugin in default_plugins:
            self.register_plugin(plugin)
            
    def register_plugin(self, plugin: StandardizationPlugin):
        """
        Register a standardization plugin.
        
        Args:
            plugin (StandardizationPlugin): Plugin to register
        """
        try:
            if not isinstance(plugin, StandardizationPlugin):
                raise ValueError(f"Plugin must inherit from StandardizationPlugin")
                
            data_type = plugin.data_type
            if data_type in self.plugins:
                existing_version = self.plugins[data_type].version
                new_version = plugin.version
                print(f"Warning: Replacing plugin for '{data_type}' "
                      f"(v{existing_version} -> v{new_version})")
                      
            self.plugins[data_type] = plugin
            print(f"Registered plugin: {data_type} v{plugin.version}")
            
        except Exception as e:
            print(f"Failed to register plugin: {e}")
            
    def unregister_plugin(self, data_type: str):
        """
        Unregister a standardization plugin.
        
        Args:
            data_type (str): Data type to unregister
        """
        if data_type in self.plugins:
            del self.plugins[data_type]
            print(f"Unregistered plugin: {data_type}")
        else:
            print(f"No plugin found for data type: {data_type}")
            
    def register_transformer(self, data_type: str, transformer: Callable):
        """
        Register a custom data transformer.
        
        Args:
            data_type (str): Data type for the transformer
            transformer (Callable): Transformation function
        """
        try:
            # Validate transformer signature
            sig = inspect.signature(transformer)
            if len(sig.parameters) < 1:
                raise ValueError("Transformer must accept at least one parameter")
                
            self.transformers[data_type] = transformer
            print(f"Registered transformer for: {data_type}")
            
        except Exception as e:
            print(f"Failed to register transformer: {e}")
            
    def register_validator(self, data_type: str, validator: Callable):
        """
        Register a custom data validator.
        
        Args:
            data_type (str): Data type for the validator
            validator (Callable): Validation function
        """
        try:
            # Validate validator signature
            sig = inspect.signature(validator)
            if len(sig.parameters) < 1:
                raise ValueError("Validator must accept at least one parameter")
                
            self.validators[data_type] = validator
            print(f"Registered validator for: {data_type}")
            
        except Exception as e:
            print(f"Failed to register validator: {e}")
            
    def standardize_data(self, data: Any, data_type: str) -> dict:
        """
        Standardize data using registered plugins or transformers.
        
        Args:
            data: Data to standardize
            data_type (str): Type of data
            
        Returns:
            dict: Standardized data with metadata
        """
        try:
            # Try plugin first
            if data_type in self.plugins:
                result = self.plugins[data_type].standardize(data)
                result['standardization_method'] = 'plugin'
                result['plugin_version'] = self.plugins[data_type].version
                return result
                
            # Try custom transformer
            elif data_type in self.transformers:
                result = self.transformers[data_type](data)
                if not isinstance(result, dict):
                    result = {'standardized_data': result}
                result['standardization_method'] = 'transformer'
                return result
                
            else:
                return {
                    'status': 'error',
                    'message': f"No standardization method found for data type: {data_type}",
                    'standardization_method': 'none'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Standardization failed: {e}",
                'standardization_method': 'error'
            }
            
    def validate_data(self, data: Any, data_type: str) -> dict:
        """
        Validate data using registered plugins or validators.
        
        Args:
            data: Data to validate
            data_type (str): Type of data
            
        Returns:
            dict: Validation results
        """
        try:
            # Try plugin first
            if data_type in self.plugins:
                result = self.plugins[data_type].validate(data)
                result['validation_method'] = 'plugin'
                return result
                
            # Try custom validator
            elif data_type in self.validators:
                result = self.validators[data_type](data)
                if not isinstance(result, dict):
                    result = {'valid': result}
                result['validation_method'] = 'validator'
                return result
                
            else:
                return {
                    'status': VALIDATION_ERROR,
                    'message': f"No validation method found for data type: {data_type}",
                    'validation_method': 'none'
                }
                
        except Exception as e:
            return {
                'status': VALIDATION_CRITICAL,
                'message': f"Validation failed: {e}",
                'validation_method': 'error'
            }
            
    def get_supported_types(self) -> dict:
        """
        Get all supported data types and their methods.
        
        Returns:
            dict: Supported data types with available methods
        """
        supported = {}
        
        # Add plugin types
        for data_type, plugin in self.plugins.items():
            supported[data_type] = {
                'methods': ['standardize', 'validate'],
                'source': 'plugin',
                'version': plugin.version,
                'class': plugin.__class__.__name__
            }
            
        # Add transformer types
        for data_type in self.transformers:
            if data_type not in supported:
                supported[data_type] = {'methods': [], 'source': 'mixed'}
            supported[data_type]['methods'].append('transform')
            
        # Add validator types
        for data_type in self.validators:
            if data_type not in supported:
                supported[data_type] = {'methods': [], 'source': 'mixed'}
            supported[data_type]['methods'].append('validate')
            
        return supported
        
    def get_framework_info(self) -> dict:
        """
        Get comprehensive framework information.
        
        Returns:
            dict: Framework information and statistics
        """
        return {
            'framework_version': '1.0.0',
            'total_plugins': len(self.plugins),
            'total_transformers': len(self.transformers),
            'total_validators': len(self.validators),
            'supported_types': list(self.get_supported_types().keys()),
            'plugin_details': {
                data_type: plugin.get_metadata() 
                for data_type, plugin in self.plugins.items()
            }
        }

# Global framework instance
_global_framework = StandardizationFramework()

def get_standardization_framework():
    """
    Get the global standardization framework instance.
    
    Returns:
        StandardizationFramework: Global framework instance
    """
    return _global_framework

def register_custom_plugin(plugin: StandardizationPlugin):
    """
    Register a custom standardization plugin globally.
    
    Args:
        plugin (StandardizationPlugin): Plugin to register
    """
    _global_framework.register_plugin(plugin)

def standardize_any_data(data: Any, data_type: str) -> dict:
    """
    Standardize any data using the global framework.
    
    Args:
        data: Data to standardize
        data_type (str): Type of data
        
    Returns:
        dict: Standardized data with metadata
    """
    return _global_framework.standardize_data(data, data_type)

def validate_any_data(data: Any, data_type: str) -> dict:
    """
    Validate any data using the global framework.
    
    Args:
        data: Data to validate
        data_type (str): Type of data
        
    Returns:
        dict: Validation results
    """
    return _global_framework.validate_data(data, data_type)

def get_framework_capabilities() -> dict:
    """
    Get current framework capabilities and supported data types.
    
    Returns:
        dict: Framework capabilities
    """
    return _global_framework.get_framework_info()

