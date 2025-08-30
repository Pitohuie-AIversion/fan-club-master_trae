################################################################################
## Project: Fanclub Mark IV "Master"              ## File: modern_widgets.py  ##
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
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

## MODERN BUTTON ###############################################################
class ModernButton(tk.Frame):
    """
    A modern button with simulated rounded corners and depth effects.
    Uses layered frames to create visual depth and modern appearance.
    """
    
    def __init__(self, master, text="Button", style="primary", command=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.command = command
        self.style = style
        self.text = text
        
        # Configure frame
        self.config(bg=master.cget('bg') if hasattr(master, 'cget') else SURFACE_2)
        
        # Create shadow layer (bottom layer)
        self.shadow_frame = tk.Frame(self)
        self.shadow_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # Create main button layer
        self.button_frame = tk.Frame(self.shadow_frame)
        self.button_frame.pack(pady=(0, 2), padx=(2, 0), fill=tk.BOTH, expand=True)
        
        # Create actual button
        self.button = tk.Button(self.button_frame, text=text, command=self._on_click)
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
            # Lift effect on hover
            self.button_frame.pack_configure(pady=(1, 1), padx=(1, 1))
            
        def on_leave(event):
            # Return to normal depth
            self.button_frame.pack_configure(pady=(0, 2), padx=(2, 0))
        
        self.button.bind("<Enter>", on_enter)
        self.button.bind("<Leave>", on_leave)
    
    def _on_click(self):
        """Handle button click with depth animation."""
        # Press effect
        self.button_frame.pack_configure(pady=(2, 0), padx=(0, 2))
        self.after(100, lambda: self.button_frame.pack_configure(pady=(0, 2), padx=(2, 0)))
        
        # Execute command
        if self.command:
            self.command()
    
    def config_text(self, text):
        """Update button text."""
        self.text = text
        self.button.config(text=text)

## MODERN CARD #################################################################
class ModernCard(tk.Frame):
    """
    A modern card container with simulated shadow and elevation.
    Perfect for grouping related content with visual hierarchy.
    """
    
    def __init__(self, master, elevation="medium", **kwargs):
        super().__init__(master, **kwargs)
        
        self.elevation = elevation
        
        # Configure main frame
        self.config(bg=master.cget('bg') if hasattr(master, 'cget') else SURFACE_2)
        
        # Create shadow layers for depth
        self._create_shadow_layers()
        
        # Create content frame
        self.content_frame = tk.Frame(self.main_frame, bg=SURFACE_1, relief='flat')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
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
            shadow_frame = tk.Frame(current_frame, bg=color)
            shadow_frame.pack(fill=tk.BOTH, expand=True, pady=(0, offset), padx=(offset, 0))
            current_frame = shadow_frame
        
        # Main frame (top layer)
        self.main_frame = tk.Frame(current_frame, bg=SURFACE_1)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

## MODERN INPUT ################################################################
class ModernEntry(tk.Frame):
    """
    A modern input field with floating label and enhanced styling.
    """
    
    def __init__(self, master, placeholder="Enter text...", **kwargs):
        super().__init__(master, bg=SURFACE_2, **kwargs)
        
        self.placeholder = placeholder
        self.placeholder_color = TEXT_DISABLED
        self.text_color = TEXT_PRIMARY
        
        # Create container with border effect
        self.container = tk.Frame(self, bg=SURFACE_4, height=2)
        self.container.pack(fill=tk.X, padx=2, pady=2)
        
        # Create actual entry
        self.entry = tk.Entry(self.container, **gus.entry_conf)
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
            self.container.config(bg=PRIMARY_300)
        
        def on_focus_out(event):
            self.container.config(bg=SURFACE_4)
        
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
class ModernToggle(tk.Frame):
    """
    A modern toggle switch with smooth visual transitions.
    """
    
    def __init__(self, master, text="", variable=None, **kwargs):
        super().__init__(master, bg=SURFACE_2, **kwargs)
        
        self.variable = variable or tk.BooleanVar()
        self.text = text
        
        # Create toggle container
        self.toggle_frame = tk.Frame(self, bg=SURFACE_2)
        self.toggle_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # Create toggle track
        self.track = tk.Frame(self.toggle_frame, bg=SURFACE_4, width=50, height=24)
        self.track.pack_propagate(False)
        self.track.pack()
        
        # Create toggle thumb
        self.thumb = tk.Frame(self.track, bg=SURFACE_1, width=20, height=20)
        self.thumb.place(x=2, y=2)
        
        # Create label
        if text:
            self.label = tk.Label(self, text=text, **gus.label_conf)
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
        """Update visual state based on variable value."""
        if self.variable.get():
            # ON state
            self.track.config(bg=PRIMARY_500)
            self.thumb.config(bg=SURFACE_1)
            self.thumb.place(x=28, y=2)
        else:
            # OFF state
            self.track.config(bg=SURFACE_4)
            self.thumb.config(bg=SURFACE_1)
            self.thumb.place(x=2, y=2)

## MODERN PROGRESS BAR #########################################################
class ModernProgressBar(tk.Frame):
    """
    A modern progress bar with gradient-like appearance.
    """
    
    def __init__(self, master, width=200, height=8, **kwargs):
        super().__init__(master, bg=SURFACE_2, **kwargs)
        
        self.width = width
        self.height = height
        self.progress = 0.0
        
        # Create progress track
        self.track = tk.Frame(self, bg=SURFACE_4, width=width, height=height)
        self.track.pack_propagate(False)
        self.track.pack()
        
        # Create progress fill
        self.fill = tk.Frame(self.track, bg=PRIMARY_500, height=height)
        self.fill.pack(side=tk.LEFT, fill=tk.Y)
    
    def set_progress(self, value):
        """Set progress value (0.0 to 1.0)."""
        self.progress = max(0.0, min(1.0, value))
        fill_width = int(self.width * self.progress)
        self.fill.config(width=fill_width)
        
        # Color graduation based on progress
        if self.progress < 0.3:
            color = ERROR_MAIN
        elif self.progress < 0.7:
            color = WARNING_MAIN
        else:
            color = SUCCESS_MAIN
        
        self.fill.config(bg=color)