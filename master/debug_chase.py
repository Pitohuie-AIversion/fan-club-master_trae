#!/usr/bin/env python3
"""
Debug script to check CHASE command availability in running application
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time

def check_chase_status():
    """Check if CHASE command is available in the running application"""
    try:
        # Try to access the main application window
        root = tk._default_root
        if root is None:
            print("No Tkinter application is running")
            return
        
        # Find the control widget
        def find_control_widget(widget):
            """Recursively find the control widget"""
            if hasattr(widget, 'network') and hasattr(widget, 'chaseStartButton'):
                return widget
            
            for child in widget.winfo_children():
                result = find_control_widget(child)
                if result:
                    return result
            return None
        
        control_widget = find_control_widget(root)
        if control_widget:
            print(f"Found control widget: {type(control_widget)}")
            print(f"Network object type: {type(control_widget.network)}")
            print(f"Network has sendChase: {hasattr(control_widget.network, 'sendChase')}")
            
            if hasattr(control_widget.network, 'sendChase'):
                print("sendChase method is available!")
                print(f"sendChase method: {control_widget.network.sendChase}")
            else:
                print("sendChase method is NOT available")
                print(f"Available methods: {[m for m in dir(control_widget.network) if not m.startswith('_')]}")
        else:
            print("Could not find control widget")
            
    except Exception as e:
        print(f"Error checking CHASE status: {e}")

if __name__ == "__main__":
    # Run the check in a separate thread to avoid blocking
    check_thread = threading.Thread(target=check_chase_status)
    check_thread.daemon = True
    check_thread.start()
    check_thread.join()