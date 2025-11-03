"""
21x21 Fan Array Mapping Utilities
=================================

This module provides utilities for managing the 21x21 fan array configuration,
including coordinate conversion, fan indexing, and mapping strategies.

Author: Fan Club System
Date: 2025
"""

import math
from typing import Tuple, List, Dict, Optional


class Array21x21Mapper:
    """
    Mapping utilities for the 21x21 fan array system.
    
    This class provides methods for:
    - Converting between 2D coordinates and linear fan indices
    - Managing module-to-fan mappings
    - Calculating distances and neighborhoods
    - Pattern generation for flow control
    """
    
    def __init__(self):
        self.rows = 21
        self.columns = 21
        self.total_fans = 441
        self.modules = 21  # One module per row
        self.fans_per_module = 21
        
    def coordinate_to_index(self, row: int, col: int) -> int:
        """
        Convert 2D coordinates to linear fan index.
        
        Args:
            row: Row index (0-20)
            col: Column index (0-20)
            
        Returns:
            Linear fan index (0-440)
            
        Raises:
            ValueError: If coordinates are out of bounds
        """
        if not (0 <= row < self.rows and 0 <= col < self.columns):
            raise ValueError(f"Coordinates ({row}, {col}) out of bounds")
            
        return row * self.columns + col
    
    def index_to_coordinate(self, index: int) -> Tuple[int, int]:
        """
        Convert linear fan index to 2D coordinates.
        
        Args:
            index: Linear fan index (0-440)
            
        Returns:
            Tuple of (row, col) coordinates
            
        Raises:
            ValueError: If index is out of bounds
        """
        if not (0 <= index < self.total_fans):
            raise ValueError(f"Index {index} out of bounds")
            
        row = index // self.columns
        col = index % self.columns
        return (row, col)
    
    def get_module_for_fan(self, fan_index: int) -> int:
        """
        Get the module number that controls a specific fan.
        
        Args:
            fan_index: Linear fan index (0-440)
            
        Returns:
            Module number (0-20)
        """
        row, _ = self.index_to_coordinate(fan_index)
        return row
    
    def get_fans_for_module(self, module_id: int) -> List[int]:
        """
        Get all fan indices controlled by a specific module.
        
        Args:
            module_id: Module number (0-20)
            
        Returns:
            List of fan indices controlled by this module
        """
        if not (0 <= module_id < self.modules):
            raise ValueError(f"Module ID {module_id} out of bounds")
            
        start_index = module_id * self.fans_per_module
        return list(range(start_index, start_index + self.fans_per_module))
    
    def get_module_mapping_string(self, module_id: int) -> str:
        """
        Get the mapping string for a module (as used in profiles.py).
        
        Args:
            module_id: Module number (0-20)
            
        Returns:
            Comma-separated string of local fan indices (0-20)
        """
        return ",".join(str(i) for i in range(self.fans_per_module))
    
    def calculate_distance(self, fan1_index: int, fan2_index: int) -> float:
        """
        Calculate Euclidean distance between two fans.
        
        Args:
            fan1_index: First fan index
            fan2_index: Second fan index
            
        Returns:
            Euclidean distance between fans
        """
        row1, col1 = self.index_to_coordinate(fan1_index)
        row2, col2 = self.index_to_coordinate(fan2_index)
        
        return math.sqrt((row2 - row1)**2 + (col2 - col1)**2)
    
    def get_neighbors(self, fan_index: int, radius: int = 1) -> List[int]:
        """
        Get neighboring fans within a specified radius.
        
        Args:
            fan_index: Center fan index
            radius: Search radius (default: 1 for immediate neighbors)
            
        Returns:
            List of neighboring fan indices
        """
        center_row, center_col = self.index_to_coordinate(fan_index)
        neighbors = []
        
        for row in range(max(0, center_row - radius), 
                        min(self.rows, center_row + radius + 1)):
            for col in range(max(0, center_col - radius), 
                           min(self.columns, center_col + radius + 1)):
                if row == center_row and col == center_col:
                    continue  # Skip the center fan itself
                    
                neighbor_index = self.coordinate_to_index(row, col)
                neighbors.append(neighbor_index)
        
        return neighbors
    
    def get_cross_neighbors(self, fan_index: int) -> List[int]:
        """
        Get the four cross-pattern neighbors (up, down, left, right).
        
        Args:
            fan_index: Center fan index
            
        Returns:
            List of cross neighbors (may be less than 4 for edge fans)
        """
        row, col = self.index_to_coordinate(fan_index)
        neighbors = []
        
        # Check all four directions
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < self.rows and 0 <= new_col < self.columns:
                neighbors.append(self.coordinate_to_index(new_row, new_col))
        
        return neighbors
    
    def create_circular_pattern(self, center_row: int, center_col: int, 
                               radius: float) -> List[int]:
        """
        Create a circular pattern of fans around a center point.
        
        Args:
            center_row: Center row coordinate
            center_col: Center column coordinate
            radius: Circle radius
            
        Returns:
            List of fan indices within the circle
        """
        pattern = []
        
        for row in range(self.rows):
            for col in range(self.columns):
                distance = math.sqrt((row - center_row)**2 + (col - center_col)**2)
                if distance <= radius:
                    pattern.append(self.coordinate_to_index(row, col))
        
        return pattern
    
    def create_rectangular_pattern(self, start_row: int, start_col: int,
                                  end_row: int, end_col: int) -> List[int]:
        """
        Create a rectangular pattern of fans.
        
        Args:
            start_row: Starting row (inclusive)
            start_col: Starting column (inclusive)
            end_row: Ending row (inclusive)
            end_col: Ending column (inclusive)
            
        Returns:
            List of fan indices in the rectangle
        """
        pattern = []
        
        for row in range(max(0, start_row), min(self.rows, end_row + 1)):
            for col in range(max(0, start_col), min(self.columns, end_col + 1)):
                pattern.append(self.coordinate_to_index(row, col))
        
        return pattern
    
    def create_diagonal_pattern(self, main_diagonal: bool = True) -> List[int]:
        """
        Create a diagonal pattern across the array.
        
        Args:
            main_diagonal: If True, creates main diagonal (top-left to bottom-right)
                          If False, creates anti-diagonal (top-right to bottom-left)
            
        Returns:
            List of fan indices forming the diagonal
        """
        pattern = []
        
        for i in range(min(self.rows, self.columns)):
            if main_diagonal:
                pattern.append(self.coordinate_to_index(i, i))
            else:
                pattern.append(self.coordinate_to_index(i, self.columns - 1 - i))
        
        return pattern
    
    def get_edge_fans(self) -> Dict[str, List[int]]:
        """
        Get fans on the edges of the array.
        
        Returns:
            Dictionary with edge names as keys and fan indices as values
        """
        edges = {
            'top': [],
            'bottom': [],
            'left': [],
            'right': []
        }
        
        # Top edge (row 0)
        for col in range(self.columns):
            edges['top'].append(self.coordinate_to_index(0, col))
        
        # Bottom edge (row 20)
        for col in range(self.columns):
            edges['bottom'].append(self.coordinate_to_index(self.rows - 1, col))
        
        # Left edge (column 0)
        for row in range(self.rows):
            edges['left'].append(self.coordinate_to_index(row, 0))
        
        # Right edge (column 20)
        for row in range(self.rows):
            edges['right'].append(self.coordinate_to_index(row, self.columns - 1))
        
        return edges
    
    def get_corner_fans(self) -> Dict[str, int]:
        """
        Get the four corner fans.
        
        Returns:
            Dictionary with corner names as keys and fan indices as values
        """
        return {
            'top_left': self.coordinate_to_index(0, 0),
            'top_right': self.coordinate_to_index(0, self.columns - 1),
            'bottom_left': self.coordinate_to_index(self.rows - 1, 0),
            'bottom_right': self.coordinate_to_index(self.rows - 1, self.columns - 1)
        }
    
    def validate_configuration(self) -> Dict[str, bool]:
        """
        Validate the 21x21 array configuration.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'total_fans_correct': self.total_fans == 441,
            'modules_correct': self.modules == 21,
            'fans_per_module_correct': self.fans_per_module == 21,
            'coordinate_mapping_valid': True,
            'module_mapping_valid': True
        }
        
        # Test coordinate mapping
        try:
            for i in range(self.total_fans):
                row, col = self.index_to_coordinate(i)
                reconstructed_index = self.coordinate_to_index(row, col)
                if reconstructed_index != i:
                    results['coordinate_mapping_valid'] = False
                    break
        except Exception:
            results['coordinate_mapping_valid'] = False
        
        # Test module mapping
        try:
            total_mapped_fans = 0
            for module_id in range(self.modules):
                fans = self.get_fans_for_module(module_id)
                total_mapped_fans += len(fans)
                if len(fans) != self.fans_per_module:
                    results['module_mapping_valid'] = False
                    break
            
            if total_mapped_fans != self.total_fans:
                results['module_mapping_valid'] = False
        except Exception:
            results['module_mapping_valid'] = False
        
        return results


# Global instance for easy access
array_mapper = Array21x21Mapper()


def demo_usage():
    """
    Demonstration of the Array21x21Mapper functionality.
    """
    print("21x21 Fan Array Mapping Demo")
    print("=" * 40)
    
    mapper = Array21x21Mapper()
    
    # Basic coordinate conversion
    print(f"Fan at (10, 10) has index: {mapper.coordinate_to_index(10, 10)}")
    print(f"Fan 220 is at coordinates: {mapper.index_to_coordinate(220)}")
    
    # Module information
    print(f"Fan 220 is controlled by module: {mapper.get_module_for_fan(220)}")
    print(f"Module 10 controls fans: {mapper.get_fans_for_module(10)[:5]}... (showing first 5)")
    
    # Neighbors
    center_fan = 220  # Middle of the array
    neighbors = mapper.get_neighbors(center_fan, radius=1)
    print(f"Fan {center_fan} has {len(neighbors)} neighbors within radius 1")
    
    # Patterns
    circle = mapper.create_circular_pattern(10, 10, 3)
    print(f"Circular pattern (center 10,10, radius 3) contains {len(circle)} fans")
    
    # Validation
    validation = mapper.validate_configuration()
    print(f"Configuration validation: {validation}")


if __name__ == "__main__":
    demo_usage()