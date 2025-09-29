################################################################################
## Project: Fan Club Mark II "Master" ## File: animations.py               ##
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
 + Animation utilities for smooth UI transitions and effects.
 + Provides easing functions, transition managers, and animation helpers.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

import tkinter as tk
import math
import time
from typing import Callable, Optional, Any

## EASING FUNCTIONS ############################################################

def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out easing function."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

def ease_out_bounce(t: float) -> float:
    """Bounce ease-out easing function."""
    n1 = 7.5625
    d1 = 2.75
    
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375

def ease_in_out_sine(t: float) -> float:
    """Sine ease-in-out easing function."""
    return -(math.cos(math.pi * t) - 1) / 2

def ease_out_elastic(t: float) -> float:
    """Elastic ease-out easing function."""
    c4 = (2 * math.pi) / 3
    
    if t == 0:
        return 0
    elif t == 1:
        return 1
    else:
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

## ANIMATION MANAGER ###########################################################

class AnimationManager:
    """Manages smooth animations using tkinter's after() method."""
    
    def __init__(self, widget: tk.Widget):
        self.widget = widget
        self.active_animations = {}
        self._animation_id_counter = 0
    
    def animate(self, 
                duration: int,
                update_func: Callable[[float], None],
                easing_func: Callable[[float], float] = ease_in_out_cubic,
                on_complete: Optional[Callable[[], None]] = None,
                animation_id: Optional[str] = None) -> str:
        """Start a new animation.
        
        Args:
            duration: Animation duration in milliseconds
            update_func: Function called with progress (0.0 to 1.0)
            easing_func: Easing function for smooth transitions
            on_complete: Optional callback when animation completes
            animation_id: Optional ID for the animation
            
        Returns:
            Animation ID for cancellation
        """
        if animation_id is None:
            animation_id = f"anim_{self._animation_id_counter}"
            self._animation_id_counter += 1
        
        # Cancel existing animation with same ID
        if animation_id in self.active_animations:
            self.cancel_animation(animation_id)
        
        start_time = time.time() * 1000  # Convert to milliseconds
        
        def animate_step():
            current_time = time.time() * 1000
            elapsed = current_time - start_time
            progress = min(elapsed / duration, 1.0)
            
            # Apply easing
            eased_progress = easing_func(progress)
            
            # Update the animation
            try:
                update_func(eased_progress)
            except Exception as e:
                print(f"Animation update error: {e}")
                self.cancel_animation(animation_id)
                return
            
            if progress < 1.0:
                # Continue animation
                try:
                    # Check if widget still exists
                    if hasattr(self.widget, 'winfo_exists') and self.widget.winfo_exists():
                        after_id = self.widget.after(16, animate_step)  # ~60 FPS
                        self.active_animations[animation_id] = after_id
                    else:
                        # Widget destroyed, cancel animation
                        if animation_id in self.active_animations:
                            del self.active_animations[animation_id]
                except (tk.TclError, AttributeError, RuntimeError):
                    # Widget destroyed, cancel animation
                    if animation_id in self.active_animations:
                        del self.active_animations[animation_id]
            else:
                # Animation complete
                if animation_id in self.active_animations:
                    del self.active_animations[animation_id]
                if on_complete:
                    try:
                        on_complete()
                    except Exception as e:
                        print(f"Animation completion callback error: {e}")
        
        # Start the animation
        try:
            # Check if widget still exists
            if hasattr(self.widget, 'winfo_exists') and self.widget.winfo_exists():
                after_id = self.widget.after(16, animate_step)
                self.active_animations[animation_id] = after_id
            else:
                # Widget destroyed, don't start animation
                return None
        except (tk.TclError, AttributeError, RuntimeError):
            # Widget destroyed, don't start animation
            return None
        
        return animation_id
    
    def cancel_animation(self, animation_id: str):
        """Cancel an active animation."""
        if animation_id in self.active_animations:
            self.widget.after_cancel(self.active_animations[animation_id])
            del self.active_animations[animation_id]
    
    def cancel_all_animations(self):
        """Cancel all active animations."""
        for animation_id in list(self.active_animations.keys()):
            self.cancel_animation(animation_id)

## ANIMATION HELPERS ###########################################################

def animate_color_transition(widget: tk.Widget, 
                           from_color: str, 
                           to_color: str, 
                           duration: int = 300,
                           property_name: str = 'bg'):
    """Animate color transition for a widget."""
    # Parse colors (simplified - assumes hex colors)
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(rgb):
        return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"
    
    try:
        from_rgb = hex_to_rgb(from_color)
        to_rgb = hex_to_rgb(to_color)
    except:
        # Fallback to immediate change if color parsing fails
        widget.config(**{property_name: to_color})
        return
    
    animation_manager = AnimationManager(widget)
    
    def update_color(progress):
        # Interpolate between colors
        r = from_rgb[0] + (to_rgb[0] - from_rgb[0]) * progress
        g = from_rgb[1] + (to_rgb[1] - from_rgb[1]) * progress
        b = from_rgb[2] + (to_rgb[2] - from_rgb[2]) * progress
        
        color = rgb_to_hex((r, g, b))
        try:
            widget.config(**{property_name: color})
        except:
            pass  # Widget might not support this property
    
    animation_manager.animate(duration, update_color, ease_in_out_sine)

def animate_scale_bounce(widget: tk.Widget, duration: int = 200):
    """Animate a bounce effect by scaling the widget."""
    original_width = widget.winfo_reqwidth()
    original_height = widget.winfo_reqheight()
    
    animation_manager = AnimationManager(widget)
    
    def update_scale(progress):
        # Bounce effect: scale up then down
        if progress < 0.5:
            scale = 1.0 + (progress * 2) * 0.1  # Scale up to 110%
        else:
            scale = 1.1 - ((progress - 0.5) * 2) * 0.1  # Scale back to 100%
        
        try:
            # For buttons, we can simulate scaling with padding
            if hasattr(widget, 'configure'):
                padding = int(2 * (scale - 1.0))
                widget.configure(padding=(padding, padding))
        except:
            pass
    
    animation_manager.animate(duration, update_scale, ease_out_bounce)

def animate_fade_in(widget: tk.Widget, duration: int = 300):
    """Animate fade-in effect (simplified for tkinter)."""
    # Since tkinter doesn't support opacity directly,
    # we simulate fade-in by changing colors gradually
    animation_manager = AnimationManager(widget)
    
    def update_fade(progress):
        try:
            # Simulate fade by adjusting state
            if progress < 0.3:
                widget.configure(state='disabled')
            else:
                widget.configure(state='normal')
        except:
            pass
    
    animation_manager.animate(duration, update_fade, ease_in_out_sine)

## BUTTON ANIMATION MIXINS #####################################################

class AnimatedButtonMixin:
    """Mixin to add animation effects to buttons."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.animation_manager = AnimationManager(self)
        self._setup_button_animations()
    
    def _setup_button_animations(self):
        """Setup hover and click animations."""
        # Bind hover effects
        self.bind('<Enter>', self._on_hover_enter)
        self.bind('<Leave>', self._on_hover_leave)
        self.bind('<Button-1>', self._on_click_start)
        self.bind('<ButtonRelease-1>', self._on_click_end)
    
    def _on_hover_enter(self, event):
        """Handle mouse enter (hover start)."""
        try:
            # Subtle scale animation on hover
            def update_hover(progress):
                scale = 1.0 + progress * 0.02  # 2% scale increase
                padding = int(scale * 2)
                if hasattr(self, 'configure'):
                    self.configure(padding=(padding, padding))
            
            self.animation_manager.animate(150, update_hover, ease_out_elastic, animation_id='hover')
        except:
            pass
    
    def _on_hover_leave(self, event):
        """Handle mouse leave (hover end)."""
        try:
            def update_unhover(progress):
                scale = 1.02 - progress * 0.02  # Scale back to normal
                padding = int(scale * 2)
                if hasattr(self, 'configure'):
                    self.configure(padding=(padding, padding))
            
            self.animation_manager.animate(150, update_unhover, ease_in_out_cubic, animation_id='hover')
        except:
            pass
    
    def _on_click_start(self, event):
        """Handle click start."""
        animate_scale_bounce(self, 100)
    
    def _on_click_end(self, event):
        """Handle click end."""
        pass  # Bounce animation handles the full effect