#!/usr/bin/env python3
################################################################################
## Project: Fanclub Mark IV "Standards" unit tests                           ##
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
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
## Data Standardization Unit Tests                                           ##
################################################################################

"""
ABOUT +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Unit tests for the data standardization functionality implemented in standards.py.
Tests cover network diagnostics, DC data standardization, disconnection handling,
data validation, and the extensible framework.
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""

import unittest
import sys
import os
import math
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to the path to import fc modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fc.standards as standards

class TestNetworkDiagnosticsStandardization(unittest.TestCase):
    """Test network diagnostics data standardization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Valid test parameters
        self.valid_miso_index = 100
        self.valid_mosi_index = 850000
        self.valid_packet_loss_count = 5
        self.valid_latency_ms = 50.0
        self.valid_throughput_kbps = 1000.0
        self.valid_error_count = 2
        self.valid_retry_count = 1
        
    def test_standardize_network_diagnostics_valid_data(self):
        """Test standardization with valid network diagnostics data."""
        result = standards.standardize_network_diagnostics(
            self.valid_miso_index, self.valid_mosi_index, self.valid_packet_loss_count,
            self.valid_latency_ms, self.valid_throughput_kbps, self.valid_error_count,
            self.valid_retry_count
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('vector', result)
        self.assertIn('status', result)
        self.assertIn('status_text', result)
        self.assertIn('packet_loss_percentage', result)
        self.assertIn('error_rate', result)
        self.assertIn('is_healthy', result)
        
        # Verify data types
        self.assertIsInstance(result['vector'], list)
        self.assertIsInstance(result['status'], int)
        self.assertIsInstance(result['status_text'], str)
        self.assertIsInstance(result['packet_loss_percentage'], (int, float))
        self.assertIsInstance(result['error_rate'], (int, float))
        self.assertIsInstance(result['is_healthy'], bool)
        
        # Verify vector length
        self.assertEqual(len(result['vector']), 8)
        
    def test_standardize_network_diagnostics_invalid_miso_index(self):
        """Test standardization with invalid MISO index."""
        with self.assertRaises(ValueError):
            standards.standardize_network_diagnostics(
                -1, self.valid_mosi_index, self.valid_packet_loss_count,
                self.valid_latency_ms, self.valid_throughput_kbps, self.valid_error_count,
                self.valid_retry_count
            )
        
    def test_standardize_network_diagnostics_invalid_latency(self):
        """Test standardization with invalid latency."""
        with self.assertRaises(ValueError):
            standards.standardize_network_diagnostics(
                self.valid_miso_index, self.valid_mosi_index, self.valid_packet_loss_count,
                -10.0, self.valid_throughput_kbps, self.valid_error_count,
                self.valid_retry_count
            )
        
    def test_standardize_network_diagnostics_high_latency(self):
        """Test standardization with high latency."""
        result = standards.standardize_network_diagnostics(
            self.valid_miso_index, self.valid_mosi_index, self.valid_packet_loss_count,
            200.0, self.valid_throughput_kbps, self.valid_error_count,
            self.valid_retry_count
        )
        
        # Verify return result contains necessary fields
        self.assertIn('vector', result)
        self.assertIn('status', result)
        self.assertIn('is_healthy', result)
        
        # High latency should result in unhealthy status
        self.assertFalse(result['is_healthy'])

class TestDCDataStandardization(unittest.TestCase):
    """Test DC data standardization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.voltage = 12.5
        self.current = 2.3
        self.power = 28.75
        self.temperature = 25.0
        
    def test_standardize_dc_data_valid(self):
        """Test DC data standardization with valid data."""
        result = standards.standardize_dc_data(
            self.voltage, self.current, self.power, self.temperature
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('raw_values', result)
        self.assertIn('normalized_values', result)
        self.assertIn('status', result)
        self.assertIn('status_message', result)
        self.assertIn('warnings', result)
        self.assertIn('is_safe', result)
        
        # Check that normalized values are present
        normalized = result['normalized_values']
        self.assertIn('voltage', normalized)
        self.assertIn('current', normalized)
        self.assertIn('power', normalized)
        
    def test_standardize_dc_data_invalid_values(self):
        """Test DC data standardization with invalid values."""
        with self.assertRaises(ValueError):
            standards.standardize_dc_data(
                -5.0,  # Invalid negative voltage
                15.0,  # Exceeds max current
                200.0  # Exceeds max power
            )
        
    def test_standardize_dc_data_invalid_voltage(self):
        """测试无效电压值"""
        with self.assertRaises(ValueError):
            standards.standardize_dc_data(-5.0, self.current)  # 负电压
        
    def test_standardize_dc_data_missing_current(self):
        """Test DC data standardization with missing required current parameter."""
        with self.assertRaises(TypeError):
            standards.standardize_dc_data(self.voltage)  # Missing current parameter
        
    def test_standardize_dc_data_none_input(self):
        """Test DC data standardization with None input."""
        with self.assertRaises((TypeError, ValueError)):
            standards.standardize_dc_data(None, None)

class TestDisconnectionEventHandling(unittest.TestCase):
    """Test disconnection event handling functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_event = {
            'event_type': 'slave_disconnection',
            'slave_id': 'slave_001',
            'disconnection_type': 'timeout'
        }
        
    def test_standardize_disconnection_event_valid(self):
        """Test disconnection event standardization with valid data."""
        result = standards.standardize_disconnection_event(
            'slave_001', 
            standards.DISC_STATUS_TIMEOUT, 
            'Connection timeout occurred'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('event_type', result)
        self.assertIn('slave_id', result)
        self.assertIn('disconnection_type', result)
        self.assertIn('status_message', result)
        self.assertIn('severity', result)
        self.assertEqual(result['slave_id'], 'slave_001')
        self.assertEqual(result['disconnection_type'], standards.DISC_STATUS_TIMEOUT)
        
    def test_disconnection_handler_registration(self):
        """Test disconnection handler registration."""
        handler = standards.get_disconnection_handler()
        
        # Test registering a cleanup handler
        def dummy_cleanup(slave_id, disconnection_type):
            return f"Cleaned up {slave_id} for type {disconnection_type}"
            
        handler.register_cleanup_handler('test_cleanup', dummy_cleanup, standards.CLEANUP_PRIORITY_HIGH)
        
        # Verify handler was registered in cleanup_registry
        self.assertIn('test_cleanup', handler.cleanup_registry)
        self.assertEqual(handler.cleanup_registry['test_cleanup']['priority'], standards.CLEANUP_PRIORITY_HIGH)
        
    def test_disconnection_handler_process_event(self):
        """Test disconnection handler event processing."""
        handler = standards.get_disconnection_handler()
        
        # Process a disconnection event with correct parameters
        result = handler.handle_disconnection(
            'slave_001', 
            standards.DISC_STATUS_TIMEOUT, 
            'Connection timeout occurred'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('slave_id', result)
        self.assertIn('disconnection_type', result)
        self.assertIn('status_message', result)
        self.assertIn('cleanup_results', result)
        self.assertIn('state_preserved', result)
        self.assertIn('recovery_possible', result)
        self.assertEqual(result['slave_id'], 'slave_001')
        self.assertEqual(result['disconnection_type'], standards.DISC_STATUS_TIMEOUT)

class TestDataValidation(unittest.TestCase):
    """Test data validation and format checking functionality."""
    
    def test_validate_ieee_754_float_valid(self):
        """Test IEEE 754 float validation with valid values."""
        test_cases = [
            3.14159,
            -2.71828,
            "123.456",
            "1.23e-4",
            0.0
        ]
        
        for value in test_cases:
            with self.subTest(value=value):
                result = standards.validate_ieee_754_float(value)
                self.assertTrue(result['valid'], f"Failed for value: {value}")
                
    def test_validate_ieee_754_float_invalid(self):
        """Test IEEE 754 float validation with invalid values."""
        test_cases = [
            float('nan'),
            float('inf'),
            float('-inf'),
            "not_a_number",
            None,
            []
        ]
        
        for value in test_cases:
            with self.subTest(value=value):
                result = standards.validate_ieee_754_float(value)
                self.assertFalse(result['valid'], f"Should have failed for value: {value}")
                
    def test_validate_slave_id_format_valid(self):
        """Test slave ID format validation with valid IDs."""
        test_cases = [
            "slave_001",
            "SLAVE-123",
            "s1",
            "test_slave_id_123"
        ]
        
        for slave_id in test_cases:
            with self.subTest(slave_id=slave_id):
                result = standards.validate_slave_id_format(slave_id)
                self.assertTrue(result['valid'], f"Failed for slave_id: {slave_id}")
                
    def test_validate_slave_id_format_invalid(self):
        """Test slave ID format validation with invalid IDs."""
        test_cases = [
            "",
            "   ",
            "slave@001",  # Invalid character
            "a" * 50,     # Too long
            123,          # Not a string
            None
        ]
        
        for slave_id in test_cases:
            with self.subTest(slave_id=slave_id):
                result = standards.validate_slave_id_format(slave_id)
                self.assertFalse(result['valid'], f"Should have failed for slave_id: {slave_id}")
                
    def test_validate_timestamp_format_valid(self):
        """Test timestamp format validation with valid timestamps."""
        test_cases = [
            "2024-01-15T10:30:45",
            "2024-01-15T10:30:45.123",
            "2024-01-15T10:30:45Z",
            "2024-01-15T10:30:45.123Z"
        ]
        
        for timestamp in test_cases:
            with self.subTest(timestamp=timestamp):
                result = standards.validate_timestamp_format(timestamp)
                self.assertTrue(result['valid'], f"Failed for timestamp: {timestamp}")
                
    def test_validate_timestamp_format_invalid(self):
        """Test timestamp format validation with invalid timestamps."""
        test_cases = [
            "2024-01-15 10:30:45",  # Missing T
            "2024/01/15T10:30:45",  # Wrong date separator
            "24-01-15T10:30:45",    # Wrong year format
            "invalid_timestamp",
            123,
            None
        ]
        
        for timestamp in test_cases:
            with self.subTest(timestamp=timestamp):
                result = standards.validate_timestamp_format(timestamp)
                self.assertFalse(result['valid'], f"Should have failed for timestamp: {timestamp}")

class TestDataValidator(unittest.TestCase):
    """Test the DataValidator class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = standards.get_data_validator()
        
    def test_validate_network_diagnostics_structure(self):
        """Test network diagnostics data structure validation."""
        valid_data = {
            'vector': [100.0, 850000.0, 95.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'status': standards.ND_STATUS_GOOD,
            'status_text': 'Good',
            'packet_loss_percentage': 5.0,
            'error_rate': 0.02,
            'is_healthy': True
        }
        
        result = self.validator.validate_data_structure(valid_data, 'network_diagnostics')
        
        self.assertEqual(result['status'], standards.VALIDATION_SUCCESS)
        self.assertEqual(len(result['errors']), 0)
        
    def test_validate_dc_data_structure(self):
        """Test DC data structure validation."""
        valid_data = {
            'raw_values': {'voltage': 12.0, 'current': 2.0, 'power': 24.0},
            'normalized_values': {'voltage': 0.8, 'current': 0.4, 'power': 0.6},
            'status': standards.DC_STATUS_NORMAL
        }
        
        result = self.validator.validate_data_structure(valid_data, 'dc_data')
        
        self.assertEqual(result['status'], standards.VALIDATION_SUCCESS)
        self.assertEqual(len(result['errors']), 0)
        
    def test_validate_data_integrity(self):
        """Test comprehensive data integrity validation."""
        test_data = {
            'network_data': {
                'vector': [100.0, 850000.0, 95.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'status': standards.ND_STATUS_GOOD,
                'status_text': 'Good'
            },
            'dc_data': {
                'raw_values': {'voltage': 12.0, 'current': 2.0, 'power': 24.0},
                'normalized_values': {'voltage': 0.8, 'current': 0.4, 'power': 0.6},
                'status': standards.DC_STATUS_NORMAL
            }
        }
        
        result = standards.validate_data_integrity(test_data)
        
        self.assertEqual(result['overall_status'], standards.VALIDATION_SUCCESS)
        self.assertGreater(result['validation_summary']['total_fields'], 0)

class TestStandardizationFramework(unittest.TestCase):
    """Test the extensible standardization framework."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.framework = standards.get_standardization_framework()
        
    def test_framework_initialization(self):
        """Test framework initialization with default plugins."""
        info = self.framework.get_framework_info()
        
        self.assertGreater(info['total_plugins'], 0)
        self.assertIn('network_diagnostics', info['supported_types'])
        self.assertIn('dc_data', info['supported_types'])
        self.assertIn('disconnection_event', info['supported_types'])
        
    def test_custom_plugin_registration(self):
        """Test custom plugin registration."""
        
        class TestPlugin(standards.StandardizationPlugin):
            @property
            def data_type(self):
                return "test_data"
                
            @property
            def version(self):
                return "1.0.0"
                
            def standardize(self, data):
                return {'standardized': True, 'data': data}
                
            def validate(self, data):
                return {'valid': True}
                
        plugin = TestPlugin()
        self.framework.register_plugin(plugin)
        
        # Test that plugin was registered
        supported_types = self.framework.get_supported_types()
        self.assertIn('test_data', supported_types)
        
        # Test using the plugin
        result = self.framework.standardize_data({'test': 'data'}, 'test_data')
        self.assertTrue(result['standardized'])
        
    def test_custom_transformer_registration(self):
        """Test custom transformer registration."""
        
        def test_transformer(data):
            return {'transformed': True, 'original': data}
            
        self.framework.register_transformer('custom_type', test_transformer)
        
        # Test using the transformer
        result = self.framework.standardize_data({'test': 'data'}, 'custom_type')
        self.assertEqual(result['standardization_method'], 'transformer')
        
    def test_framework_standardize_data(self):
        """Test framework data standardization."""
        # Test with DC data (which works with the plugin interface)
        dc_data = {'voltage': 12.5, 'current': 2.3, 'power': 28.75}
        result = self.framework.standardize_data(dc_data, 'dc_data')
        
        self.assertEqual(result['standardization_method'], 'plugin')
        self.assertIn('raw_values', result)
        
    def test_framework_validate_data(self):
        """Test framework data validation."""
        valid_data = {
            'vector': [100.0, 850000.0, 95.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'status': standards.ND_STATUS_GOOD,
            'status_text': 'Good'
        }
        
        result = self.framework.validate_data(valid_data, 'network_diagnostics')
        
        self.assertEqual(result['validation_method'], 'plugin')
        self.assertEqual(result['status'], standards.VALIDATION_SUCCESS)

class TestGlobalFunctions(unittest.TestCase):
    """Test global convenience functions."""
    
    def test_standardize_any_data(self):
        """Test global standardize_any_data function."""
        data = {
            'miso_index': 1,
            'latency': 100.0,
            'bandwidth': 850000.0,
            'packet_loss_percentage': 5.0,
            'error_rate': 0.02,
            'jitter': 0.0,
            'signal_strength': 0.0
        }
        result = standards.standardize_any_data(data, 'network_diagnostics')
        
        self.assertIn('vector', result)
        self.assertIn('status', result)
        
    def test_validate_any_data(self):
        """Test global validate_any_data function."""
        valid_data = {
            'vector': [100.0, 850000.0, 95.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'status': standards.ND_STATUS_GOOD,
            'status_text': 'Good',
            'packet_loss_percentage': 5.0,
            'error_rate': 0.02,
            'is_healthy': True
        }
        
        result = standards.validate_any_data(valid_data, 'network_diagnostics')
        
        self.assertEqual(result['status'], standards.VALIDATION_SUCCESS)
        
    def test_get_framework_capabilities(self):
        """Test get_framework_capabilities function."""
        capabilities = standards.get_framework_capabilities()
        
        self.assertIn('framework_version', capabilities)
        self.assertIn('total_plugins', capabilities)
        self.assertIn('supported_types', capabilities)

if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestNetworkDiagnosticsStandardization,
        TestDCDataStandardization,
        TestDisconnectionEventHandling,
        TestDataValidation,
        TestDataValidator,
        TestStandardizationFramework,
        TestGlobalFunctions
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
            
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")