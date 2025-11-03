#!/usr/bin/env python3
"""
21x21 Fan Array Configuration Test Suite
========================================

This script tests the ARRAY_21X21 profile configuration to ensure all parameters
are valid and the system can properly handle the 441-fan array.

Author: Fan Club System
Date: 2025
"""

import sys
import os
import traceback
from typing import Dict, List, Any

# Add the fc module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fc'))

try:
    from fc.builtin import profiles
    from fc import archive as ac
    from fc.builtin.array_21x21_mapping import Array21x21Mapper, array_mapper
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you're running this script from the master directory")
    sys.exit(1)


class Array21x21Tester:
    """Test suite for the 21x21 fan array configuration."""
    
    def __init__(self):
        self.profile = profiles.ARRAY_21X21
        self.mapper = Array21x21Mapper()
        self.test_results = {}
        
    def run_all_tests(self) -> Dict[str, bool]:
        """
        Run all validation tests for the 21x21 array configuration.
        
        Returns:
            Dictionary with test names as keys and pass/fail as values
        """
        print("Running 21x21 Fan Array Configuration Tests")
        print("=" * 50)
        
        tests = [
            ("Basic Profile Structure", self.test_basic_profile_structure),
            ("Network Configuration", self.test_network_configuration),
            ("Fan Array Dimensions", self.test_fan_array_dimensions),
            ("Slave Module Count", self.test_slave_module_count),
            ("Module Configuration", self.test_module_configuration),
            ("MAC Address Uniqueness", self.test_mac_address_uniqueness),
            ("Fan Mapping Consistency", self.test_fan_mapping_consistency),
            ("Coordinate System", self.test_coordinate_system),
            ("Performance Parameters", self.test_performance_parameters),
            ("Profile Registration", self.test_profile_registration),
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\nTesting: {test_name}")
                result = test_func()
                self.test_results[test_name] = result
                status = "PASS" if result else "FAIL"
                print(f"Result: {status}")
            except Exception as e:
                print(f"ERROR: {e}")
                print(traceback.format_exc())
                self.test_results[test_name] = False
        
        return self.test_results
    
    def test_basic_profile_structure(self) -> bool:
        """Test that the profile has all required basic fields."""
        required_fields = [
            ac.name, ac.description, ac.platform,
            ac.broadcastIP, ac.broadcastPort, ac.periodMS,
            ac.defaultSlave, ac.savedSlaves, ac.fanArray
        ]
        
        for field in required_fields:
            if field not in self.profile:
                print(f"  Missing required field: {field}")
                return False
        
        print(f"  Profile name: {self.profile[ac.name]}")
        print(f"  Description: {self.profile[ac.description]}")
        return True
    
    def test_network_configuration(self) -> bool:
        """Test network configuration parameters."""
        network_config = {
            ac.broadcastIP: "192.168.21.255",
            ac.broadcastPort: 65000,
            ac.periodMS: 50,
            ac.maxLength: 1024,
            ac.maxTimeouts: 20,
        }
        
        for param, expected in network_config.items():
            if self.profile.get(param) != expected:
                print(f"  Network parameter {param} mismatch: "
                      f"expected {expected}, got {self.profile.get(param)}")
                return False
        
        print("  Network configuration validated")
        return True
    
    def test_fan_array_dimensions(self) -> bool:
        """Test fan array dimensions."""
        fan_array = self.profile[ac.fanArray]
        
        expected_dims = {
            ac.FA_rows: 21,
            ac.FA_columns: 21,
            ac.FA_layers: 1
        }
        
        for dim, expected in expected_dims.items():
            if fan_array.get(dim) != expected:
                print(f"  Fan array dimension {dim} mismatch: "
                      f"expected {expected}, got {fan_array.get(dim)}")
                return False
        
        total_fans = fan_array[ac.FA_rows] * fan_array[ac.FA_columns] * fan_array[ac.FA_layers]
        if total_fans != 441:
            print(f"  Total fans calculation error: expected 441, got {total_fans}")
            return False
        
        print(f"  Fan array dimensions: {fan_array[ac.FA_rows]}x{fan_array[ac.FA_columns]}x{fan_array[ac.FA_layers]} = {total_fans} fans")
        return True
    
    def test_slave_module_count(self) -> bool:
        """Test that we have exactly 21 slave modules."""
        saved_slaves = self.profile[ac.savedSlaves]
        
        if len(saved_slaves) != 21:
            print(f"  Incorrect number of slave modules: expected 21, got {len(saved_slaves)}")
            return False
        
        print(f"  Slave module count: {len(saved_slaves)}")
        return True
    
    def test_module_configuration(self) -> bool:
        """Test individual module configurations."""
        saved_slaves = self.profile[ac.savedSlaves]
        
        for i, slave in enumerate(saved_slaves):
            # Check module row assignment
            if slave[ac.MD_row] != i:
                print(f"  Module {i} row assignment error: expected {i}, got {slave[ac.MD_row]}")
                return False
            
            # Check fan count
            if slave[ac.SV_maxFans] != 21:
                print(f"  Module {i} max fans error: expected 21, got {slave[ac.SV_maxFans]}")
                return False
            
            # Check dimensions
            if slave[ac.MD_rows] != 1 or slave[ac.MD_columns] != 21:
                print(f"  Module {i} dimensions error: expected 1x21, got {slave[ac.MD_rows]}x{slave[ac.MD_columns]}")
                return False
            
            # Check mapping string
            expected_mapping = "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20"
            if slave[ac.MD_mapping] != expected_mapping:
                print(f"  Module {i} mapping error")
                return False
        
        print("  All module configurations validated")
        return True
    
    def test_mac_address_uniqueness(self) -> bool:
        """Test that all MAC addresses are unique."""
        saved_slaves = self.profile[ac.savedSlaves]
        mac_addresses = [slave[ac.SV_mac] for slave in saved_slaves]
        
        if len(mac_addresses) != len(set(mac_addresses)):
            print("  Duplicate MAC addresses found")
            return False
        
        # Check MAC address format
        for i, mac in enumerate(mac_addresses):
            if not mac.startswith("00:80:e1:21:00:"):
                print(f"  Module {i} MAC address format error: {mac}")
                return False
        
        print("  All MAC addresses are unique and properly formatted")
        return True
    
    def test_fan_mapping_consistency(self) -> bool:
        """Test fan mapping consistency with the mapper."""
        saved_slaves = self.profile[ac.savedSlaves]
        
        for i, slave in enumerate(saved_slaves):
            # Get fans from mapper
            mapper_fans = self.mapper.get_fans_for_module(i)
            
            # Check that module controls the correct range
            expected_start = i * 21
            expected_end = expected_start + 20
            
            if mapper_fans[0] != expected_start or mapper_fans[-1] != expected_end:
                print(f"  Module {i} fan range error: expected {expected_start}-{expected_end}, "
                      f"got {mapper_fans[0]}-{mapper_fans[-1]}")
                return False
        
        print("  Fan mapping consistency validated")
        return True
    
    def test_coordinate_system(self) -> bool:
        """Test the coordinate system mapping."""
        validation = self.mapper.validate_configuration()
        
        for test_name, result in validation.items():
            if not result:
                print(f"  Coordinate system validation failed: {test_name}")
                return False
        
        # Test some specific coordinates
        test_cases = [
            (0, 0, 0),      # Top-left corner
            (0, 20, 20),    # Top-right corner
            (20, 0, 420),   # Bottom-left corner
            (20, 20, 440),  # Bottom-right corner
            (10, 10, 220),  # Center
        ]
        
        for row, col, expected_index in test_cases:
            actual_index = self.mapper.coordinate_to_index(row, col)
            if actual_index != expected_index:
                print(f"  Coordinate ({row}, {col}) mapping error: "
                      f"expected {expected_index}, got {actual_index}")
                return False
        
        print("  Coordinate system validated")
        return True
    
    def test_performance_parameters(self) -> bool:
        """Test performance-related parameters."""
        performance_params = {
            ac.maxRPM: 16000,
            ac.maxFans: 21,
            ac.dcDecimals: 3,
            ac.socketLimit: 2048,
        }
        
        for param, expected in performance_params.items():
            if self.profile.get(param) != expected:
                print(f"  Performance parameter {param} mismatch: "
                      f"expected {expected}, got {self.profile.get(param)}")
                return False
        
        print("  Performance parameters validated")
        return True
    
    def test_profile_registration(self) -> bool:
        """Test that the profile is properly registered."""
        if "ARRAY_21X21" not in profiles.PROFILES:
            print("  Profile not found in PROFILES dictionary")
            return False
        
        if profiles.PROFILES["ARRAY_21X21"] is not self.profile:
            print("  Profile registration mismatch")
            return False
        
        print("  Profile properly registered")
        return True
    
    def print_summary(self):
        """Print a summary of all test results."""
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! The 21x21 array configuration is valid.")
        else:
            print("❌ Some tests failed. Please review the configuration.")
            print("\nFailed tests:")
            for test_name, result in self.test_results.items():
                if not result:
                    print(f"  - {test_name}")
        
        return passed == total


def main():
    """Main test execution function."""
    print("21x21 Fan Array Configuration Validation")
    print("========================================")
    
    tester = Array21x21Tester()
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Print summary
    success = tester.print_summary()
    
    # Additional information
    print(f"\nConfiguration Details:")
    print(f"- Total fans: 441 (21x21)")
    print(f"- Control modules: 21")
    print(f"- Fans per module: 21")
    print(f"- Network: 192.168.21.255:65000")
    print(f"- Update frequency: 20Hz (50ms period)")
    print(f"- Max RPM: 16,000")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()