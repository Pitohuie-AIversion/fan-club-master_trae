################################################################################
## Project: Fan Club Mark II "Master" ## File: visual_effects.py           ##
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY ## ADVANCED SYSTEMS LABORATORY ##                     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES       ##                     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\___--|_|  /_____/| |-___-_|/  /____-/|/     ##
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

## ABOUT #######################################################################
"""
Advanced visual effects system for enhanced UI appearance.
Provides gradient backgrounds, improved shadows, and micro-interactions.
"""
################################################################################

import tkinter as tk
import tkinter.ttk as ttk
from typing import Tuple, Optional, Callable
import math
from fc.frontend.gui.theme_manager import theme_manager
from fc.frontend.gui.animations import AnimationManager, ease_in_out_cubic

## GRADIENT SYSTEM #############################################################

class GradientFrame(tk.Frame):
    """Frame with gradient background support."""
    
    def __init__(self, parent, gradient_colors: Tuple[str, str], 
                 direction='vertical', **kwargs):
        super().__init__(parent, **kwargs)
        self.gradient_colors = gradient_colors
        self.direction = direction
        self.canvas = None
        self._setup_gradient()
        
    def _setup_gradient(self):
        """Setup gradient canvas background."""
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind resize event to redraw gradient
        self.canvas.bind('<Configure>', self._draw_gradient)
        
    def _draw_gradient(self, event=None):
        """Draw gradient background on canvas - 优化性能"""
        try:
            if not self.canvas or not hasattr(self, 'winfo_exists') or not self.winfo_exists():
                return
                
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            if width <= 1 or height <= 1:
                return
            
            # 检查是否需要重绘（尺寸是否改变）
            if hasattr(self, '_last_size') and self._last_size == (width, height):
                return
            self._last_size = (width, height)
                
            self.canvas.delete('gradient')
            
            # Parse colors
            color1, color2 = self.gradient_colors
            r1, g1, b1 = self._hex_to_rgb(color1)
            r2, g2, b2 = self._hex_to_rgb(color2)
            
            # 减少渐变步数以提高性能
            steps = 25 if self.direction == 'vertical' else 25
            
            if self.direction == 'vertical':
                step_height = height / steps
                for i in range(steps):
                    ratio = i / (steps - 1)
                    r = int(r1 + (r2 - r1) * ratio)
                    g = int(g1 + (g2 - g1) * ratio)
                    b = int(b1 + (b2 - b1) * ratio)
                    color = f'#{r:02x}{g:02x}{b:02x}'
                    
                    y1 = i * step_height
                    y2 = (i + 1) * step_height
                    self.canvas.create_rectangle(0, y1, width, y2, 
                                               fill=color, outline=color, tags='gradient')
            else:  # horizontal
                step_width = width / steps
                for i in range(steps):
                    ratio = i / (steps - 1)
                    r = int(r1 + (r2 - r1) * ratio)
                    g = int(g1 + (g2 - g1) * ratio)
                    b = int(b1 + (b2 - b1) * ratio)
                    color = f'#{r:02x}{g:02x}{b:02x}'
                    
                    x1 = i * step_width
                    x2 = (i + 1) * step_width
                    self.canvas.create_rectangle(x1, 0, x2, height, 
                                               fill=color, outline=color, tags='gradient')
        except (tk.TclError, AttributeError, RuntimeError):
            # 忽略错误，避免卡顿
            pass
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def update_gradient(self, new_colors: Tuple[str, str]):
        """Update gradient colors."""
        self.gradient_colors = new_colors
        self._draw_gradient()

## SHADOW SYSTEM ###############################################################

class ShadowMixin:
    """Mixin to add shadow effects to widgets."""
    
    def __init__(self, *args, **kwargs):
        self.shadow_enabled = kwargs.pop('shadow', False)
        self.shadow_blur = kwargs.pop('shadow_blur', 4)
        self.shadow_offset = kwargs.pop('shadow_offset', (2, 2))
        self.shadow_color = kwargs.pop('shadow_color', '#00000020')
        super().__init__(*args, **kwargs)
        
        if self.shadow_enabled:
            self._setup_shadow()
    
    def _setup_shadow(self):
        """Setup shadow effect using frame layering."""
        if not hasattr(self, 'master'):
            return
            
        # Create shadow frame
        self.shadow_frame = tk.Frame(
            self.master,
            bg=self.shadow_color,
            height=2,
            relief='flat',
            bd=0
        )
        
        # Position shadow frame behind main widget
        self.shadow_frame.place(
            x=self.shadow_offset[0],
            y=self.shadow_offset[1],
            width=self.winfo_reqwidth(),
            height=self.winfo_reqheight()
        )
        
        # Ensure main widget is above shadow
        self.lift()
    
    def update_shadow(self, blur=None, offset=None, color=None):
        """Update shadow properties."""
        if blur is not None:
            self.shadow_blur = blur
        if offset is not None:
            self.shadow_offset = offset
        if color is not None:
            self.shadow_color = color
            
        if hasattr(self, 'shadow_frame'):
            self.shadow_frame.configure(bg=self.shadow_color)
            self.shadow_frame.place(
                x=self.shadow_offset[0],
                y=self.shadow_offset[1]
            )

## MICRO-INTERACTIONS ##########################################################

class InteractiveWidget:
    """Mixin for adding hover and click effects to widgets."""
    
    def __init__(self, *args, **kwargs):
        # 提取交互相关参数
        self.hover_effects = kwargs.pop('hover_effects', False)  # 默认禁用
        self.click_effects = kwargs.pop('click_effects', False)  # 默认禁用
        self.animation_manager = kwargs.pop('animation_manager', None)
        
        super().__init__(*args, **kwargs)
        
        # 只有在启用效果时才设置交互
        if self.hover_effects or self.click_effects:
            self._setup_interactions()
    
    def _setup_interactions(self):
        """Setup hover and click interactions - 仅在启用时执行"""
        if not (self.hover_effects or self.click_effects):
            return
            
        if self.hover_effects:
            self.bind("<Enter>", self._on_hover_enter)
            self.bind("<Leave>", self._on_hover_leave)
        
        if self.click_effects:
            self.bind("<Button-1>", self._on_click_down)
            self.bind("<ButtonRelease-1>", self._on_click_up)
    
    def _on_hover_enter(self, event):
        """Handle mouse enter event."""
        # 简化或禁用动画效果
        pass
    
    def _on_hover_leave(self, event):
        """Handle mouse leave event."""
        # 简化或禁用动画效果
        pass
    
    def _on_click_down(self, event):
        """Handle mouse click down."""
        # 简化或禁用动画效果
        pass
    
    def _on_click_up(self, event):
        """Handle mouse click up."""
        # 简化或禁用动画效果
        pass
    
    def _darken_color(self, hex_color: str, factor: float) -> str:
        """Darken a hex color by a factor (0.0 to 1.0)."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        
        return f'#{r:02x}{g:02x}{b:02x}'

## ENHANCED WIDGETS ############################################################

class GradientButton(tk.Button, InteractiveWidget):
    """Button with gradient background and micro-interactions."""
    
    def __init__(self, parent, gradient_colors=None, **kwargs):
        # Set default gradient colors from theme
        if gradient_colors is None:
            gradient_colors = (
                theme_manager.get_color('PRIMARY_500'),
                theme_manager.get_color('PRIMARY_600')
            )
        
        self.gradient_colors = gradient_colors
        
        # Remove gradient-specific kwargs before passing to Button
        button_kwargs = {k: v for k, v in kwargs.items() 
                        if k not in ['hover_effects', 'click_effects', 'animation_manager']}
        
        tk.Button.__init__(self, parent, **button_kwargs)
        InteractiveWidget.__init__(self, **kwargs)
        
        self._setup_gradient_background()
    
    def _setup_gradient_background(self):
        """Setup gradient background using canvas."""
        # Create canvas for gradient
        self.gradient_canvas = tk.Canvas(
            self, highlightthickness=0,
            height=self.winfo_reqheight() or 30
        )
        self.gradient_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw initial gradient
        try:
            if hasattr(self, 'winfo_exists') and self.winfo_exists():
                self.after(1, self._draw_button_gradient)
        except (tk.TclError, AttributeError, RuntimeError):
            pass
        
        # Bind resize
        self.gradient_canvas.bind('<Configure>', self._draw_button_gradient)
    
    def _draw_button_gradient(self, event=None):
        """Draw gradient on button canvas."""
        try:
            # Check if widget still exists
            if not hasattr(self, 'winfo_exists') or not self.winfo_exists():
                return
                
            if not hasattr(self, 'gradient_canvas'):
                return
                
            width = self.gradient_canvas.winfo_width()
            height = self.gradient_canvas.winfo_height()
            
            if width <= 1 or height <= 1:
                return
            
            # 防止重复绘制相同尺寸
            if hasattr(self, '_last_button_size') and self._last_button_size == (width, height):
                return
            self._last_button_size = (width, height)
                
            self.gradient_canvas.delete('all')
            
            # Draw gradient
            color1, color2 = self.gradient_colors
            r1, g1, b1 = self._hex_to_rgb(color1)
            r2, g2, b2 = self._hex_to_rgb(color2)
            
            # 减少步数以提高性能
            steps = 15
            step_height = height / steps
            
            for i in range(steps):
                ratio = i / (steps - 1)
                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)
                color = f'#{r:02x}{g:02x}{b:02x}'
                
                y1 = i * step_height
                y2 = (i + 1) * step_height
                self.gradient_canvas.create_rectangle(
                    0, y1, width, y2,
                    fill=color, outline=color
                )
            
            # Add button text
            text = self.cget('text')
            if text:
                self.gradient_canvas.create_text(
                    width//2, height//2,
                    text=text,
                    fill='white',
                    font=self.cget('font')
                )
                
        except (tk.TclError, AttributeError, RuntimeError):
            # 忽略错误，避免卡顿
            pass
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

class ElevatedFrame(tk.Frame, ShadowMixin, InteractiveWidget):
    """Frame with elevation shadow and hover effects."""
    
    def __init__(self, parent, elevation='medium', **kwargs):
        # Set shadow properties based on elevation
        shadow_configs = {
            'low': {'shadow_blur': 2, 'shadow_offset': (1, 1), 'shadow_color': '#00000010'},
            'medium': {'shadow_blur': 4, 'shadow_offset': (2, 2), 'shadow_color': '#00000020'},
            'high': {'shadow_blur': 8, 'shadow_offset': (4, 4), 'shadow_color': '#00000030'}
        }
        
        shadow_config = shadow_configs.get(elevation, shadow_configs['medium'])
        kwargs.update(shadow_config)
        kwargs['shadow'] = True
        
        tk.Frame.__init__(self, parent, **{k: v for k, v in kwargs.items() 
                                          if k not in ['shadow', 'shadow_blur', 'shadow_offset', 'shadow_color', 
                                                      'hover_effects', 'click_effects', 'animation_manager']})
        ShadowMixin.__init__(self, **kwargs)
        InteractiveWidget.__init__(self, **kwargs)

## VISUAL EFFECTS MANAGER #####################################################

class VisualEffectsManager:
    """Manager for coordinating visual effects across the application."""
    
    def __init__(self, root_widget):
        self.root = root_widget
        # 禁用动画管理器以提高性能
        self.animation_manager = None  # AnimationManager(root_widget)
        self.effects_enabled = False  # 默认禁用视觉效果
        
    def create_gradient_frame(self, parent, gradient_type='primary', **kwargs):
        """Create a gradient frame with predefined color schemes."""
        # 如果效果被禁用，返回普通Frame
        if not self.effects_enabled:
            return tk.Frame(parent, **{k: v for k, v in kwargs.items() 
                                     if k not in ['gradient_colors', 'direction']})
        
        gradient_schemes = {
            'primary': (theme_manager.get_color('PRIMARY_500'), theme_manager.get_color('PRIMARY_600')),
            'surface': (theme_manager.get_color('SURFACE_1'), theme_manager.get_color('SURFACE_2')),
            'accent': ('#00bcd4', '#0097a7'),  # Cyan gradient
            'success': ('#4caf50', '#388e3c'),  # Green gradient
            'warning': ('#ff9800', '#f57c00'),  # Orange gradient
            'error': ('#f44336', '#d32f2f')     # Red gradient
        }
        
        colors = gradient_schemes.get(gradient_type, gradient_schemes['primary'])
        return GradientFrame(parent, colors, **kwargs)
    
    def create_elevated_frame(self, parent, elevation='medium', **kwargs):
        """Create an elevated frame with shadow effects."""
        # 如果效果被禁用，返回普通Frame
        if not self.effects_enabled:
            return tk.Frame(parent, **{k: v for k, v in kwargs.items() 
                                     if k not in ['shadow', 'shadow_blur', 'shadow_offset', 'shadow_color', 
                                                 'hover_effects', 'click_effects', 'animation_manager']})
        
        kwargs['animation_manager'] = self.animation_manager
        return ElevatedFrame(parent, elevation, **kwargs)
    
    def create_gradient_button(self, parent, style='primary', **kwargs):
        """Create a gradient button with micro-interactions."""
        # 如果效果被禁用，返回普通Button
        if not self.effects_enabled:
            return tk.Button(parent, **{k: v for k, v in kwargs.items() 
                                      if k not in ['gradient_colors', 'animation_manager']})
        
        gradient_schemes = {
            'primary': (theme_manager.get_color('PRIMARY_500'), theme_manager.get_color('PRIMARY_600')),
            'success': ('#4caf50', '#388e3c'),
            'warning': ('#ff9800', '#f57c00'),
            'error': ('#f44336', '#d32f2f')
        }
        
        colors = gradient_schemes.get(style, gradient_schemes['primary'])
        kwargs['gradient_colors'] = colors
        kwargs['animation_manager'] = self.animation_manager
        return GradientButton(parent, **kwargs)
    
    def add_ripple_effect(self, widget, color=None):
        """Add ripple effect to a widget (simplified version)."""
        if not self.effects_enabled:
            return
            
        if color is None:
            color = theme_manager.get_color('PRIMARY_500')
        
        def create_ripple(event):
            # Create a temporary overlay for ripple effect
            overlay = tk.Frame(widget, bg=color, height=2, width=2)
            overlay.place(x=event.x-1, y=event.y-1)
            
            # Animate ripple expansion
            def expand_ripple(size=2):
                try:
                    # Check if widget still exists
                    if not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
                        if hasattr(overlay, 'destroy'):
                            overlay.destroy()
                        return
                        
                    if size > 50:  # Max ripple size
                        overlay.destroy()
                        return
                        
                    overlay.configure(width=size, height=size)
                    overlay.place(x=event.x-size//2, y=event.y-size//2)
                    widget.after(20, lambda: expand_ripple(size + 5))
                except (tk.TclError, AttributeError, RuntimeError):
                    # Widget destroyed, clean up
                    try:
                        if hasattr(overlay, 'destroy'):
                            overlay.destroy()
                    except:
                        pass
            
            expand_ripple()
        
        widget.bind('<Button-1>', create_ripple)
    
    def enable_effects(self, enabled=True):
        """Enable or disable visual effects globally."""
        self.effects_enabled = enabled
    
    def apply_theme_effects(self):
        """Apply theme-specific visual effects."""
        # This would be called when theme changes
        # Update all gradient colors, shadows, etc.
        pass

## GLOBAL INSTANCE #############################################################

# Global visual effects manager (will be initialized by main application)
visual_effects_manager = None

def initialize_visual_effects(root_widget):
    """Initialize the global visual effects manager."""
    global visual_effects_manager
    visual_effects_manager = VisualEffectsManager(root_widget)
    return visual_effects_manager