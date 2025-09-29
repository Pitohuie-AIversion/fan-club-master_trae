#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              WESTLAKE UNIVERSITY                            ║
║                        ADVANCED SYSTEMS LABORATORY                          ║
║                                                                              ║
║                    ██╗    ██╗███████╗███████╗████████╗                     ║
║                    ██║    ██║██╔════╝██╔════╝╚══██╔══╝                     ║
║                    ██║ █╗ ██║█████╗  ███████╗   ██║                        ║
║                    ██║███╗██║██╔══╝  ╚════██║   ██║                        ║
║                    ╚███╔███╔╝███████╗███████║   ██║                        ║
║                     ╚══╝╚══╝ ╚══════╝╚══════╝   ╚═╝                        ║
║                                                                              ║
║                           LAKE SYSTEMS LABORATORY                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Icon Button Widget

A modern button widget that combines SVG icons with text labels.
Supports consistent spacing, hover effects, and theme integration.

Authors: zhaoyang, dashuai
Email: mzymuzhaoyang@gmail.com, dschen2018@gmail.com
Date: 2024
Version: 1.0
"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font as tkfont
import io
from PIL import Image, ImageDraw, ImageFont, ImageTk
import base64
import xml.etree.ElementTree as ET
import re

from fc.frontend.gui.embedded.icons import get_icon, get_icon_with_color
from fc.frontend.gui.theme_manager import theme_manager
from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.performance import get_performance_manager

def create_simple_icon(icon_name, size=(16, 16), color="#000000"):
    """
    Create a simple icon using basic shapes.
    """
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    if icon_name == "play":
        # Triangle pointing right
        points = [(4, 2), (4, 14), (14, 8)]
        draw.polygon(points, fill=color)
    elif icon_name == "pause":
        # Two vertical bars
        draw.rectangle([4, 2, 7, 14], fill=color)
        draw.rectangle([9, 2, 12, 14], fill=color)
    elif icon_name == "apply":
        # Checkmark
        draw.line([(3, 8), (7, 12)], fill=color, width=2)
        draw.line([(7, 12), (13, 6)], fill=color, width=2)
    elif icon_name == "print":
        # Printer shape
        draw.rectangle([2, 6, 14, 10], outline=color, width=1)
        draw.rectangle([4, 10, 12, 14], outline=color, width=1)
        draw.rectangle([4, 2, 12, 6], outline=color, width=1)
    elif icon_name == "load":
        # Folder shape
        draw.rectangle([2, 4, 14, 12], outline=color, width=1)
        draw.rectangle([2, 4, 8, 6], fill=color)
    elif icon_name == "save":
        # Floppy disk shape
        draw.rectangle([2, 2, 14, 14], outline=color, width=1)
        draw.rectangle([4, 2, 12, 6], fill=color)
        draw.ellipse([7, 8, 11, 12], outline=color, width=1)
    else:
        # Default - simple circle
        draw.ellipse([2, 2, 14, 14], outline=color, width=2)
    
    return img

class IconButton(ttk.Frame):
    """
    A button widget that displays an icon alongside text.
    
    Features:
    - SVG icon support with dynamic coloring
    - Consistent spacing and padding
    - Theme-aware styling
    - Hover effects
    - Multiple button styles (primary, secondary, etc.)
    """
    
    def __init__(self, master, text="", icon=None, command=None, style="Secondary", **kwargs):
        super().__init__(master, **kwargs)
        
        self.text = text
        self.icon_name = icon
        self.command = command
        self.style_name = style
        self.icon_image = None
        
        # Create the actual button
        button_style = f"{style}.TButton" if style else "TButton"
        self.button = ttk.Button(
            self,
            text=text,
            command=command,
            style=button_style
        )
        self.button.pack(fill=tk.BOTH, expand=True)
        
        # Store original text for theme updates
        self._original_text = text
        
        # Set up icon if provided
        if icon:
            self._update_icon()
        
        # Register for theme changes
        theme_manager.register_callback(self._on_theme_change)
    
    def _update_icon(self):
        """
        Update the button icon based on current theme.
        Enhanced with icon caching for better performance.
        """
        if not self.icon_name:
            return
            
        try:
            # Get current theme color
            color = theme_manager.get_color('TEXT_PRIMARY')
            
            # Try to get cached icon first
            performance_manager = get_performance_manager()
            cache_key = f"{self.icon_name}_{color}_{16}_{16}"
            cached_icon = performance_manager.icon_cache.get_icon(cache_key)
            
            if cached_icon:
                self.icon_image = cached_icon
            else:
                # Create simple icon
                icon_img = create_simple_icon(self.icon_name, size=(16, 16), color=color)
                
                # Convert to PhotoImage
                self.icon_image = ImageTk.PhotoImage(icon_img)
                
                # Cache the icon for future use
                performance_manager.icon_cache.cache_icon(cache_key, self.icon_image)
            
            # Update button with icon and text
            if self.text:
                self.button.config(image=self.icon_image, text=self.text, compound=tk.LEFT)
            else:
                self.button.config(image=self.icon_image, text="")
                
        except Exception as e:
            # Fallback to text only
            print(f"Icon error: {e}")
            self.button.config(image="", text=self.text or "")
    
    def destroy(self):
        """Override destroy method to clean up theme callbacks"""
        try:
            # Unregister theme callback to prevent errors during shutdown
            from fc.frontend.gui.theme_manager import theme_manager
            if hasattr(self, '_on_theme_change'):
                theme_manager.unregister_callback(self._on_theme_change)
                print("[DEBUG] Theme callback unregistered for icon button")
        except Exception as e:
            print(f"[DEBUG] Error unregistering theme callback: {e}")
        
        # Call parent destroy
        try:
            super().destroy()
        except (tk.TclError, AttributeError, RuntimeError):
            pass

    def _on_theme_change(self):
        """
        Update button appearance when theme changes.
        """
        try:
            # Check if widget still exists
            if not (hasattr(self, 'winfo_exists') and self.winfo_exists()):
                return
                
            # Update icon with new theme colors
            if self.icon_name:
                self._update_icon()
        except (tk.TclError, AttributeError) as e:
            # Widget may be destroyed during theme change
            pass
        except Exception as e:
            print(f"Error updating icon button theme: {e}")
    
    def config_text(self, text):
        """
        Update the button text.
        """
        self.text = text
        self._original_text = text
        if self.icon_name:
            self._update_icon()
        else:
            self.button.config(text=text)
    
    def config_icon(self, icon):
        """
        Update the button icon.
        """
        self.icon_name = icon
        if icon:
            self._update_icon()
        else:
            self.button.config(image="", text=self.text or "")
    
    def config_command(self, command):
        """
        Update the button command.
        """
        self.command = command
        self.button.config(command=command)
    
    def config_style(self, style):
        """
        Update the button style.
        """
        self.style_name = style
        self.button.config(style=f"{style}.TButton")
    
    def config(self, **kwargs):
        """
        Configure the button with multiple options.
        """
        if 'text' in kwargs:
            self.config_text(kwargs.pop('text'))
        if 'icon' in kwargs:
            self.config_icon(kwargs.pop('icon'))
        if 'command' in kwargs:
            self.config_command(kwargs.pop('command'))
        if 'style' in kwargs:
            self.config_style(kwargs.pop('style'))
        
        # Pass remaining kwargs to the button
        if kwargs:
            self.button.config(**kwargs)
    
    def pack(self, **kwargs):
        """
        Override pack to apply consistent spacing.
        """
        # Apply default padding if not specified
        if 'padx' not in kwargs:
            kwargs['padx'] = 4
        if 'pady' not in kwargs:
            kwargs['pady'] = 2
        
        super().pack(**kwargs)
    
    def grid(self, **kwargs):
        """
        Override grid to apply consistent spacing.
        """
        # Apply default padding if not specified
        if 'padx' not in kwargs:
            kwargs['padx'] = 4
        if 'pady' not in kwargs:
            kwargs['pady'] = 2
        
        super().grid(**kwargs)

def create_icon_button(master, text="", icon=None, command=None, style="Secondary", **kwargs):
    """
    Convenience function to create an IconButton.
    
    Args:
        master: Parent widget
        text (str): Button text
        icon (str): Icon name from icons.py
        command: Button command callback
        style (str): Button style (Primary, Secondary, etc.)
        **kwargs: Additional arguments passed to IconButton
    
    Returns:
        IconButton: The created button widget
    """
    return IconButton(master, text=text, icon=icon, command=command, style=style, **kwargs)

# Convenience functions for common button types
def create_play_button(master, command=None, **kwargs):
    """Create a Play button with icon."""
    return create_icon_button(master, text="Play", icon="play", command=command, style="Primary", **kwargs)

def create_pause_button(master, command=None, **kwargs):
    """Create a Pause button with icon."""
    return create_icon_button(master, text="Pause", icon="pause", command=command, style="Secondary", **kwargs)

def create_stop_button(master, command=None, **kwargs):
    """Create a Stop button with icon."""
    return create_icon_button(master, text="Stop", icon="stop", command=command, style="Secondary", **kwargs)

def create_step_button(master, command=None, **kwargs):
    """Create a Step button with icon."""
    return create_icon_button(master, text="Step", icon="step", command=command, style="Secondary", **kwargs)

def create_apply_button(master, command=None, **kwargs):
    """Create an Apply button with icon."""
    return create_icon_button(master, text="Apply", icon="apply", command=command, style="Primary", **kwargs)

def create_print_button(master, command=None, **kwargs):
    """Create a Print button with printer icon"""
    return create_icon_button(master, text="Print", icon="print", command=command, **kwargs)

def create_load_button(master, command=None, **kwargs):
    """Create a Load button with folder icon"""
    return create_icon_button(master, text="Load", icon="load", command=command, **kwargs)

def create_save_button(master, command=None, **kwargs):
    """Create a Save button with save icon"""
    return create_icon_button(master, text="Save", icon="save", command=command, **kwargs)

def create_settings_button(master, command=None, **kwargs):
    """Create a Settings button with icon."""
    return create_icon_button(master, text="Settings", icon="settings", command=command, style="Secondary", **kwargs)

def create_help_button(master, command=None, **kwargs):
    """Create a Help button with icon."""
    return create_icon_button(master, text="Help", icon="help", command=command, style="Secondary", **kwargs)