################################################################################
## Project: Fan Club Mark II "Master" ## File: theme_manager.py            ##
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY ## ADVANCED SYSTEMS LABORATORY ##                     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES       ##                     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __   __                      ##
##                  | | |  | |  | T_| | || |    |  | |  |                     ##
##                  | _ |  |T|  |  |  |  _|      ||   ||                      ##
##                  || || |_ _| |_|_| |_| _|    |__| |__|                     ##
##                                                                            ##
##----------------------------------------------------------------------------##
## zhaoyang                   ## <mzymuzhaoyang@gmail.com>  ##                ##
## dashuai                    ## <dschen2018@gmail.com>     ##                ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Theme manager for dynamic light/dark mode switching.
 + Provides centralized theme management with runtime switching capabilities.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

import tkinter as tk
import tkinter.ttk as ttk
from fc.frontend.gui import guiutils as gus

## THEME DEFINITIONS ##########################################################

# Light Theme (Default)
LIGHT_THEME = {
    # Surface colors
    'SURFACE_1': '#ffffff',       # Pure white
    'SURFACE_2': '#f8f9fa',       # Very light gray
    'SURFACE_3': '#f1f3f4',       # Light gray
    'SURFACE_4': '#e8eaed',       # Medium light gray
    'SURFACE_5': '#dadce0',       # Medium gray
    
    # Text colors
    'TEXT_PRIMARY': '#202124',    # Primary text (almost black)
    'TEXT_SECONDARY': '#5f6368',  # Secondary text (gray)
    'TEXT_DISABLED': '#9aa0a6',   # Disabled text (light gray)
    'TEXT_ON_PRIMARY': '#ffffff', # White text on primary background
    'TEXT_ON_DARK': '#ffffff',    # White text on dark background
    
    # Primary colors
    'PRIMARY_500': '#2196f3',     # Primary blue
    'PRIMARY_600': '#1e88e5',     # Darker blue
    
    # Semantic colors
    'ERROR_MAIN': '#f44336',      # Error red
    'WARNING_MAIN': '#ff9800',    # Warning orange
    'SUCCESS_MAIN': '#4caf50',    # Success green
}

# Dark Theme
DARK_THEME = {
    # Surface colors (inverted)
    'SURFACE_1': '#1a1a1a',       # Dark gray
    'SURFACE_2': '#2d2d2d',       # Medium dark gray
    'SURFACE_3': '#3a3a3a',       # Lighter dark gray
    'SURFACE_4': '#4a4a4a',       # Medium gray
    'SURFACE_5': '#5a5a5a',       # Light gray
    
    # Text colors (inverted)
    'TEXT_PRIMARY': '#e8eaed',    # Light text
    'TEXT_SECONDARY': '#9aa0a6',  # Medium light text
    'TEXT_DISABLED': '#5f6368',   # Disabled text
    'TEXT_ON_PRIMARY': '#ffffff', # White text on primary
    'TEXT_ON_DARK': '#ffffff',    # White text on dark
    
    # Primary colors (slightly adjusted for dark mode)
    'PRIMARY_500': '#42a5f5',     # Lighter blue for dark mode
    'PRIMARY_600': '#2196f3',     # Medium blue
    
    # Semantic colors (adjusted for dark mode)
    'ERROR_MAIN': '#ef5350',      # Lighter red
    'WARNING_MAIN': '#ffa726',    # Lighter orange
    'SUCCESS_MAIN': '#66bb6a',    # Lighter green
}

## THEME MANAGER ##############################################################

class ThemeManager:
    """Manages theme switching and provides current theme colors."""
    
    def __init__(self):
        self.current_theme = 'light'
        self.themes = {
            'light': LIGHT_THEME,
            'dark': DARK_THEME
        }
        self.callbacks = []  # List of callbacks to call when theme changes
    
    def get_color(self, color_name):
        """Get a color value from the current theme."""
        return self.themes[self.current_theme].get(color_name, '#000000')
    
    def get_theme(self):
        """Get the current theme name."""
        return self.current_theme
    
    def set_theme(self, theme_name):
        """Set the current theme and notify all callbacks."""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self._notify_callbacks()
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.set_theme(new_theme)
    
    def register_callback(self, callback):
        """Register a callback to be called when theme changes."""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks of theme change."""
        # Create a copy of callbacks to avoid modification during iteration
        callbacks_copy = self.callbacks.copy()
        for callback in callbacks_copy:
            try:
                # Check if callback is still valid before calling
                if callable(callback):
                    callback()
            except (tk.TclError, AttributeError, RuntimeError) as e:
                print(f"Theme callback error (application may be closing): {e}")
                # Remove invalid callback to prevent future errors
                if callback in self.callbacks:
                    self.callbacks.remove(callback)
            except Exception as e:
                print(f"Theme callback error: {e}")
                # Remove problematic callback
                if callback in self.callbacks:
                    self.callbacks.remove(callback)
    
    def apply_ttk_theme(self, style):
        """Apply current theme to ttk.Style object."""
        try:
            # Check if style object is valid and application is not destroyed
            if not style:
                return
                
            # Additional safety checks
            if not hasattr(style, 'configure'):
                return
                
            # Try to access the style to see if it's still valid
            try:
                style.theme_names()  # This will fail if the application is destroyed
            except (tk.TclError, AttributeError, RuntimeError):
                return
            
            # Get current theme colors
            base_bg = self.get_color('SURFACE_2')
            card_bg = self.get_color('SURFACE_1')
            accent = self.get_color('PRIMARY_500')
            accent_hover = self.get_color('PRIMARY_600')
            fg = self.get_color('TEXT_PRIMARY')
            fg_muted = self.get_color('TEXT_SECONDARY')
            surface_3 = self.get_color('SURFACE_3')
            
            # Apply base styles with individual error handling
            try:
                style.configure("TLabel", background=base_bg, foreground=fg, font=gus.typography["body_medium"]["font"])
                style.configure("TFrame", background=base_bg)
                style.configure("TPanedwindow", background=base_bg)
            except (tk.TclError, AttributeError, RuntimeError):
                return
            
            # Topbar & Bottombar styles
            try:
                style.configure("Topbar.TFrame", background=surface_3)
                style.configure("Topbar.TLabel", background=surface_3, foreground=fg)
                style.configure("Bottombar.TFrame", background=surface_3)
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            
            # Card styles
            try:
                style.configure("Card.TFrame", background=card_bg, padding=(16, 12))
                style.configure("TitleLabel.TLabel", background=card_bg, foreground=fg, font=gus.typography["title_large"]["font"])
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            
            # Button styles
            try:
                style.configure("TButton", background=accent, foreground=self.get_color('TEXT_ON_PRIMARY'), padding=(10, 6), borderwidth=0, focusthickness=0)
                style.map("TButton", background=[("active", accent_hover), ("pressed", accent_hover)], relief=[("pressed", "flat"), ("!pressed", "flat")])
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            
            # Secondary button
            try:
                style.configure("Secondary.TButton", background=card_bg, foreground=fg, padding=(10, 6), borderwidth=1)
                style.map("Secondary.TButton", background=[("active", surface_3), ("pressed", surface_3)])
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            
            # Entry styles
            try:
                style.configure("TEntry", fieldbackground=card_bg, background=card_bg, foreground=fg, padding=6, borderwidth=1)
                style.map("TEntry", fieldbackground=[["focus", card_bg]], foreground=[["disabled", fg_muted]])
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            
            # Treeview styles
            try:
                style.configure("Treeview", background=card_bg, fieldbackground=card_bg, foreground=fg, rowheight=22, borderwidth=0)
                style.configure("Treeview.Heading", background=base_bg, foreground=fg, relief="flat", padding=(8, 6))
                style.map("Treeview", background=[["selected", accent]], foreground=[["selected", self.get_color('TEXT_ON_PRIMARY')]])
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            
            # Notebook styles
            try:
                style.configure("TNotebook", background=base_bg, borderwidth=0)
                style.configure("TNotebook.Tab", background=base_bg, foreground=fg_muted, padding=(16, 10))
                style.map("TNotebook.Tab", background=[["selected", card_bg]], foreground=[["selected", fg]])
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            
            # Other widget styles
            try:
                style.configure("TCheckbutton", background=base_bg, foreground=fg, padding=(6, 4))
                style.configure("TRadiobutton", background=base_bg, foreground=fg, padding=(6, 4))
                style.configure("TCombobox", fieldbackground=card_bg, background=card_bg, foreground=fg)
                style.configure("TMenubutton", background=card_bg, foreground=fg, padding=(10, 6))
                style.configure("TScale", background=base_bg)
                style.configure("TProgressbar", background=accent, troughcolor=surface_3)
                style.configure("TScrollbar", background=card_bg)
                style.configure("TSeparator", background=surface_3)
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            
            # Error banner
            try:
                style.configure("ErrorBanner.TLabel", background=self.get_color('ERROR_MAIN'), foreground=self.get_color('TEXT_ON_DARK'), padding=(10, 6), font=gus.typography["label_large"]["font"])
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            
            # Additional styles
            try:
                style.configure("Secondary.TLabel", background=base_bg, foreground=fg_muted)
                style.configure("Warning.TLabel", background=base_bg, foreground=self.get_color('WARNING_MAIN'))
                style.configure("Surface3.TLabel", background=surface_3, foreground=fg)
                style.configure("Splash.TLabel", background=base_bg, foreground=fg, borderwidth=0)
                style.configure("Toolbar.TFrame", background=surface_3)
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            
        except (tk.TclError, AttributeError, RuntimeError) as e:
            print(f"Error applying theme (application may be closing): {e}")
        except Exception as e:
            print(f"Error applying theme: {e}")

# Global theme manager instance
theme_manager = ThemeManager()

# Convenience functions for backward compatibility
def get_current_theme():
    return theme_manager.get_theme()

def set_theme(theme_name):
    theme_manager.set_theme(theme_name)

def toggle_theme():
    theme_manager.toggle_theme()

def get_color(color_name):
    return theme_manager.get_color(color_name)

# Export current theme colors (for backward compatibility)
SURFACE_1 = theme_manager.get_color('SURFACE_1')
SURFACE_2 = theme_manager.get_color('SURFACE_2')
SURFACE_3 = theme_manager.get_color('SURFACE_3')
TEXT_PRIMARY = theme_manager.get_color('TEXT_PRIMARY')
TEXT_SECONDARY = theme_manager.get_color('TEXT_SECONDARY')
TEXT_ON_DARK = theme_manager.get_color('TEXT_ON_DARK')
PRIMARY_500 = theme_manager.get_color('PRIMARY_500')
PRIMARY_600 = theme_manager.get_color('PRIMARY_600')