################################################################################
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY                                                        ##
## ADVANCED SYSTEMS LABORATORY                                                ##
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
## AUTHORS: zhaoyang (mzymuzhaoyang@gmail.com)                               ##
##          dashuai (dschen2018@gmail.com)                                   ##
##----------------------------------------------------------------------------##
################################################################################

## ABOUT #######################################################################
"""
Custom exception classes and error handling utilities for FCCommunicator.

This module provides specific exception types and error handling utilities
to improve error diagnosis and system reliability.
"""
################################################################################

import logging
import traceback
import socket
from typing import Optional, Any


class FCCommunicatorError(Exception):
    """Base exception class for FCCommunicator errors."""
    pass


class NetworkError(FCCommunicatorError):
    """Raised when network communication fails."""
    def __init__(self, message: str, slave_info: Optional[dict] = None):
        super().__init__(message)
        self.slave_info = slave_info


class SlaveConnectionError(NetworkError):
    """Raised when slave connection fails or times out."""
    def __init__(self, message: str, slave_mac: Optional[str] = None, 
                 slave_ip: Optional[str] = None):
        super().__init__(message, {'mac': slave_mac, 'ip': slave_ip})
        self.slave_mac = slave_mac
        self.slave_ip = slave_ip


class MessageParsingError(FCCommunicatorError):
    """Raised when message parsing fails."""
    def __init__(self, message: str, raw_message: Optional[str] = None):
        super().__init__(message)
        self.raw_message = raw_message


class ConfigurationError(FCCommunicatorError):
    """Raised when configuration is invalid."""
    pass


class ThreadError(FCCommunicatorError):
    """Raised when thread operations fail."""
    def __init__(self, message: str, thread_name: Optional[str] = None):
        super().__init__(message)
        self.thread_name = thread_name


class ErrorHandler:
    """Centralized error handling and logging utility."""
    
    def __init__(self, logger_name: str = 'FCCommunicator'):
        self.logger = logging.getLogger(logger_name)
        
    def handle_network_error(self, error: Exception, context: str = "", 
                           slave_info: Optional[dict] = None) -> NetworkError:
        """Handle network-related errors with proper logging."""
        if isinstance(error, socket.timeout):
            msg = f"Network timeout in {context}"
            exc = SlaveConnectionError(msg, 
                                     slave_info.get('mac') if slave_info else None,
                                     slave_info.get('ip') if slave_info else None)
        elif isinstance(error, socket.error):
            msg = f"Socket error in {context}: {error}"
            exc = NetworkError(msg, slave_info)
        else:
            msg = f"Network error in {context}: {error}"
            exc = NetworkError(msg, slave_info)
            
        self.logger.error(msg, exc_info=True)
        return exc
    
    def handle_parsing_error(self, error: Exception, raw_message: str = "", 
                           context: str = "") -> MessageParsingError:
        """Handle message parsing errors."""
        msg = f"Message parsing failed in {context}: {error}"
        exc = MessageParsingError(msg, raw_message)
        self.logger.warning(msg)
        return exc
    
    def handle_thread_error(self, error: Exception, thread_name: str = "", 
                          context: str = "") -> ThreadError:
        """Handle thread-related errors."""
        msg = f"Thread error in {context} (thread: {thread_name}): {error}"
        exc = ThreadError(msg, thread_name)
        self.logger.error(msg, exc_info=True)
        return exc
    
    def log_exception(self, error: Exception, context: str = "", 
                     level: str = "error") -> None:
        """Log exception with context information."""
        msg = f"Exception in {context}: {error}"
        
        if level == "error":
            self.logger.error(msg, exc_info=True)
        elif level == "warning":
            self.logger.warning(msg)
        elif level == "info":
            self.logger.info(msg)
        else:
            self.logger.debug(msg)
    
    def safe_execute(self, func, *args, default_return=None, 
                    context: str = "", **kwargs):
        """Safely execute a function with error handling."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.log_exception(e, context)
            return default_return


def create_error_handler(logger_name: str = 'FCCommunicator') -> ErrorHandler:
    """Factory function to create error handler instances."""
    return ErrorHandler(logger_name)


def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging configuration for error handling."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('fc_communicator.log')
        ]
    )