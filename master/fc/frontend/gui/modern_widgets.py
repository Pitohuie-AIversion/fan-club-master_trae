################################################################################
## Project: Fan Club Mark II "Master" ## File: modern_widgets.py           ##
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
 + Modern widget components with enhanced visual effects.
 + Provides rounded corners simulation and depth effects using tkinter techniques.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import tkinter as tk
from tkinter import ttk
from fc.frontend.gui.theme import *
import fc.frontend.gui.guiutils as gus
from fc.frontend.gui.animations import AnimationManager, animate_scale_bounce, ease_in_out_cubic

## MODERN BUTTON ###############################################################
class ModernButton(ttk.Frame):
    """
    A modern button with simulated rounded corners and depth effects.
    Uses layered frames to create visual depth and modern appearance.
    """
    
    def __init__(self, master, text="Button", style="primary", command=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.command = command
        self.style = style
        self.text = text
        self.is_hovered = False
        
        # Initialize animation manager
        self.animation_manager = AnimationManager(self)
        
        # Configure frame
        self.config(bg=master.cget('bg') if hasattr(master, 'cget') else SURFACE_2)
        
        # Create shadow layer (bottom layer)
        self.shadow_frame = ttk.Frame(self)
        self.shadow_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # Create main button layer
        self.button_frame = ttk.Frame(self.shadow_frame)
        self.button_frame.pack(pady=(0, 2), padx=(2, 0), fill=tk.BOTH, expand=True)
        
        # Create actual button
        self.button = ttk.Button(self.button_frame, text=text, command=self._on_click)
        self.button.pack(fill=tk.BOTH, expand=True)
        
        # Apply style
        self._apply_style()
        
        # Bind hover effects
        self._bind_hover_effects()
    
    def _apply_style(self):
        """Apply the selected style to the button."""
        if self.style == "primary":
            style_config = gus.btn_primary
            shadow_color = PRIMARY_700
        elif self.style == "secondary":
            style_config = gus.btn_secondary
            shadow_color = SURFACE_5
        elif self.style == "accent":
            style_config = gus.btn_accent
            shadow_color = ACCENT_DARK
        elif self.style == "success":
            style_config = gus.btn_success
            shadow_color = SUCCESS_DARK
        elif self.style == "error":
            style_config = gus.btn_error
            shadow_color = ERROR_DARK
        elif self.style == "warning":
            style_config = gus.btn_warning
            shadow_color = WARNING_DARK
        else:
            style_config = gus.btn_primary
            shadow_color = PRIMARY_700
        
        # Configure button with style
        self.button.config(**style_config)
        
        # Configure shadow
        self.shadow_frame.config(bg=shadow_color)
        self.button_frame.config(bg=style_config["bg"])
    
    def _bind_hover_effects(self):
        """Bind hover effects for enhanced interactivity."""
        def on_enter(event):
            self.is_hovered = True
            # Animated lift effect on hover
            self.animation_manager.animate_property(
                self.button_frame, 'pack_configure',
                {'pady': (0, 2), 'padx': (2, 0)},
                {'pady': (1, 1), 'padx': (1, 1)},
                duration=150, easing=ease_in_out_cubic
            )
            # Scale bounce animation
            animate_scale_bounce(self.button, scale_factor=1.05, duration=200)
            
        def on_leave(event):
            self.is_hovered = False
            # Animated return to normal depth
            self.animation_manager.animate_property(
                self.button_frame, 'pack_configure',
                {'pady': (1, 1), 'padx': (1, 1)},
                {'pady': (0, 2), 'padx': (2, 0)},
                duration=150, easing=ease_in_out_cubic
            )
            # Return to normal scale
            animate_scale_bounce(self.button, scale_factor=1.0, duration=200)
        
        self.button.bind("<Enter>", on_enter)
        self.button.bind("<Leave>", on_leave)
    
    def _on_click(self):
        """Handle button click with depth animation."""
        # Animated press effect
        self.animation_manager.animate_property(
            self.button_frame, 'pack_configure',
            {'pady': (0, 2) if not self.is_hovered else (1, 1), 'padx': (2, 0) if not self.is_hovered else (1, 1)},
            {'pady': (2, 0), 'padx': (0, 2)},
            duration=100, easing=ease_in_out_cubic
        )
        
        # Scale down animation for click feedback
        animate_scale_bounce(self.button, scale_factor=0.95, duration=100)
        
        # Return to normal state after click
        def return_to_normal():
            target_state = {'pady': (1, 1), 'padx': (1, 1)} if self.is_hovered else {'pady': (0, 2), 'padx': (2, 0)}
            self.animation_manager.animate_property(
                self.button_frame, 'pack_configure',
                {'pady': (2, 0), 'padx': (0, 2)},
                target_state,
                duration=100, easing=ease_in_out_cubic
            )
            scale_target = 1.05 if self.is_hovered else 1.0
            animate_scale_bounce(self.button, scale_factor=scale_target, duration=100)
        
        self.after(100, return_to_normal)
        
        # Execute command
        if self.command:
            self.command()
    
    def config_text(self, text):
        """Update button text."""
        self.text = text
        self.button.config(text=text)

## MODERN CARD #################################################################
class ModernCard(ttk.Frame):
    """
    A modern card container with simulated shadow and elevation.
    Perfect for grouping related content with visual hierarchy.
    """
    
    def __init__(self, master, elevation="medium", **kwargs):
        super().__init__(master, **kwargs)
        
        self.elevation = elevation
        self.is_hovered = False
        
        # Initialize animation manager
        self.animation_manager = AnimationManager(self)
        
        # Configure main frame
        self.config(bg=master.cget('bg') if hasattr(master, 'cget') else SURFACE_2)
        
        # Create shadow layers for depth
        self._create_shadow_layers()
        
        # Create content frame
        self.content_frame = ttk.Frame(self.main_frame, style='Card.TFrame')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Bind hover effects for enhanced interactivity
        self._bind_hover_effects()
    
    def _create_shadow_layers(self):
        """Create layered frames to simulate shadow and depth."""
        if self.elevation == "low":
            shadow_layers = [(SURFACE_4, 1), (SURFACE_3, 2)]
        elif self.elevation == "medium":
            shadow_layers = [(SURFACE_5, 1), (SURFACE_4, 2), (SURFACE_3, 3)]
        elif self.elevation == "high":
            shadow_layers = [(SURFACE_5, 1), (SURFACE_5, 2), (SURFACE_4, 3), (SURFACE_3, 4)]
        else:
            shadow_layers = [(SURFACE_4, 2)]
        
        current_frame = self
        for color, offset in shadow_layers:
            shadow_frame = ttk.Frame(current_frame)
            shadow_frame.pack(fill=tk.BOTH, expand=True, pady=(0, offset), padx=(offset, 0))
            current_frame = shadow_frame
        
        # Main frame (top layer)
        self.main_frame = ttk.Frame(current_frame, style='Card.TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
    
    def _bind_hover_effects(self):
        """Bind hover effects for enhanced interactivity."""
        def on_enter(event):
            self.is_hovered = True
            # Enhanced shadow effect on hover
            self._enhance_shadow()
            # Scale animation for hover feedback
            animate_scale_bounce(self.main_frame, scale_factor=1.02, duration=200)
            
        def on_leave(event):
            self.is_hovered = False
            # Return to normal shadow
            self._restore_shadow()
            # Return to normal scale
            animate_scale_bounce(self.main_frame, scale_factor=1.0, duration=200)
        
        self.main_frame.bind("<Enter>", on_enter)
        self.main_frame.bind("<Leave>", on_leave)
        self.content_frame.bind("<Enter>", on_enter)
        self.content_frame.bind("<Leave>", on_leave)
    
    def _enhance_shadow(self):
        """Enhance shadow effect for hover state."""
        # Animate shadow enhancement by adjusting padding
        current_padding = self.main_frame.pack_info().get('pady', 0)
        if isinstance(current_padding, tuple):
            current_padding = current_padding[1]
        
        enhanced_padding = current_padding + 2
        self.animation_manager.animate_property(
            self.main_frame, 'pack_configure',
            {'pady': (0, current_padding)},
            {'pady': (0, enhanced_padding)},
            duration=200, easing=ease_in_out_cubic
        )
    
    def _restore_shadow(self):
        """Restore normal shadow effect."""
        # Animate shadow restoration
        current_padding = self.main_frame.pack_info().get('pady', 0)
        if isinstance(current_padding, tuple):
            current_padding = current_padding[1]
        
        # Calculate original padding based on elevation
        if self.elevation == "low":
            original_padding = 2
        elif self.elevation == "medium":
            original_padding = 3
        elif self.elevation == "high":
            original_padding = 4
        else:
            original_padding = 2
        
        self.animation_manager.animate_property(
            self.main_frame, 'pack_configure',
            {'pady': (0, current_padding)},
            {'pady': (0, original_padding)},
            duration=200, easing=ease_in_out_cubic
        )

## MODERN INPUT ################################################################
class ModernEntry(ttk.Frame):
    """
    A modern input field with floating label and enhanced styling.
    """
    
    def __init__(self, master, placeholder="Enter text...", **kwargs):
        super().__init__(master, **kwargs)
        
        self.placeholder = placeholder
        self.placeholder_color = TEXT_DISABLED
        self.text_color = TEXT_PRIMARY
        self.is_focused = False
        
        # Initialize animation manager
        self.animation_manager = AnimationManager(self)
        
        # Create container with border effect
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.X, padx=2, pady=2)
        
        # Create actual entry
        self.entry = ttk.Entry(self.container, **gus.entry_conf)
        self.entry.pack(fill=tk.X, padx=1, pady=1)
        
        # Add placeholder behavior
        self._add_placeholder()
        
        # Bind focus events for modern interactions
        self._bind_focus_effects()
    
    def _add_placeholder(self):
        """Add placeholder text behavior."""
        self.entry.insert(0, self.placeholder)
        self.entry.config(fg=self.placeholder_color)
        
        def on_focus_in(event):
            if self.entry.get() == self.placeholder:
                self.entry.delete(0, tk.END)
                self.entry.config(fg=self.text_color)
        
        def on_focus_out(event):
            if not self.entry.get():
                self.entry.insert(0, self.placeholder)
                self.entry.config(fg=self.placeholder_color)
        
        self.entry.bind("<FocusIn>", on_focus_in)
        self.entry.bind("<FocusOut>", on_focus_out)
    
    def _bind_focus_effects(self):
        """Bind focus effects for visual feedback."""
        def on_focus_in(event):
            self.is_focused = True
            self.container.configure(style='Focus.TFrame')
            # Animated border highlight effect
            self.animation_manager.animate_property(
                self.container, 'pack_configure',
                {'padx': 2, 'pady': 2},
                {'padx': 1, 'pady': 1},
                duration=200, easing=ease_in_out_cubic
            )
            # Scale animation for focus feedback
            animate_scale_bounce(self.entry, scale_factor=1.02, duration=150)
        
        def on_focus_out(event):
            self.is_focused = False
            self.container.configure(style='TFrame')
            # Animated return to normal border
            self.animation_manager.animate_property(
                self.container, 'pack_configure',
                {'padx': 1, 'pady': 1},
                {'padx': 2, 'pady': 2},
                duration=200, easing=ease_in_out_cubic
            )
            # Return to normal scale
            animate_scale_bounce(self.entry, scale_factor=1.0, duration=150)
        
        self.entry.bind("<FocusIn>", on_focus_in)
        self.entry.bind("<FocusOut>", on_focus_out)
    
    def get(self):
        """Get entry value, excluding placeholder."""
        value = self.entry.get()
        return "" if value == self.placeholder else value
    
    def set(self, value):
        """Set entry value."""
        self.entry.delete(0, tk.END)
        if value:
            self.entry.insert(0, value)
            self.entry.config(fg=self.text_color)
        else:
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.placeholder_color)

## MODERN TOGGLE ###############################################################
class ModernToggle(ttk.Frame):
    """
    A modern toggle switch with smooth visual transitions.
    """
    
    def __init__(self, master, text="", variable=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.variable = variable or tk.BooleanVar()
        self.text = text
        
        # Initialize animation manager
        self.animation_manager = AnimationManager(self)
        
        # Create toggle container
        self.toggle_frame = ttk.Frame(self)
        self.toggle_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # Create toggle track
        self.track = ttk.Frame(self.toggle_frame, width=50, height=24)
        self.track.pack_propagate(False)
        self.track.pack()
        
        # Create toggle thumb
        self.thumb = ttk.Frame(self.track, width=20, height=20)
        self.thumb.place(x=2, y=2)
        
        # Create label
        if text:
            self.label = ttk.Label(self, text=text, **gus.label_conf)
            self.label.pack(side=tk.LEFT)
        
        # Bind click events
        self._bind_click_events()
        
        # Update initial state
        self._update_visual_state()
        
        # Bind variable changes
        self.variable.trace('w', self._on_variable_change)
    
    def _bind_click_events(self):
        """Bind click events to toggle functionality."""
        def toggle(event=None):
            self.variable.set(not self.variable.get())
        
        self.track.bind("<Button-1>", toggle)
        self.thumb.bind("<Button-1>", toggle)
        if hasattr(self, 'label'):
            self.label.bind("<Button-1>", toggle)
    
    def _on_variable_change(self, *args):
        """Handle variable changes."""
        self._update_visual_state()
    
    def _update_visual_state(self):
        """Update visual state based on variable value with smooth animation."""
        if self.variable.get():
            # ON state with animation
            self.track.configure(style='ToggleOn.TFrame')
            self.thumb.configure(style='ToggleThumb.TFrame')
            self._animate_thumb_to_position(28)
        else:
            # OFF state with animation
            self.track.configure(style='ToggleOff.TFrame')
            self.thumb.configure(style='ToggleThumb.TFrame')
            self._animate_thumb_to_position(2)
    
    def _animate_thumb_to_position(self, target_x):
        """Animate thumb to target position."""
        current_x = self.thumb.place_info().get('x', 2)
        if isinstance(current_x, str):
            current_x = int(current_x)
        
        # Animate thumb sliding
        self.animation_manager.animate_property(
            self.thumb, 'place_configure',
            {'x': current_x, 'y': 2},
            {'x': target_x, 'y': 2},
            duration=200, easing=ease_in_out_cubic
        )

## MODERN PROGRESS BAR #########################################################
class ModernProgressBar(ttk.Frame):
    """
    A modern progress bar with smooth animations and customizable styling.
    Provides visual feedback for task progress.
    """
    
    def __init__(self, master, width=200, height=8, **kwargs):
        super().__init__(master, **kwargs)
        
        self.width = width
        self.height = height
        self.progress = 0.0
        
        # Initialize animation manager
        self.animation_manager = AnimationManager(self)
        
        # Create progress track
        self.track = ttk.Frame(self, width=width, height=height)
        self.track.pack_propagate(False)
        self.track.pack()
        
        # Create progress fill
        self.fill = ttk.Frame(self.track, height=height)
        self.fill.pack(side=tk.LEFT, fill=tk.Y)
    
    def set_progress(self, value, animate=True):
        """Set progress value (0.0 to 1.0) with smooth animation."""
        old_progress = self.progress
        self.progress = max(0.0, min(1.0, value))
        
        if animate:
            # Animate progress change
            old_width = int(self.width * old_progress)
            new_width = int(self.width * self.progress)
            
            self.animation_manager.animate_property(
                self.fill, 'config',
                {'width': old_width},
                {'width': new_width},
                duration=300, easing=ease_in_out_cubic
            )
        else:
            # Immediate update
            fill_width = int(self.width * self.progress)
            self.fill.config(width=fill_width)
        
        # Color graduation based on progress with smooth transition
        if self.progress < 0.3:
            style = 'ProgressError.TFrame'
        elif self.progress < 0.7:
            style = 'ProgressWarning.TFrame'
        else:
            style = 'ProgressSuccess.TFrame'
        
        self.fill.configure(style=style)