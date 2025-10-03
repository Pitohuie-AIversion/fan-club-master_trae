################################################################################
## Project: Fan Club Mark II "Master" ## File: responsive.py                ##
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
 + Responsive layout management for Fan Club GUI.
 + Provides window size adaptation, dynamic font scaling, and adaptive spacing.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import tkinter as tk
import tkinter.ttk as ttk
from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.theme_manager import theme_manager

## CONSTANTS ###################################################################
# Breakpoints for responsive design (width in pixels)
BREAKPOINT_SMALL = 800
BREAKPOINT_MEDIUM = 1200
BREAKPOINT_LARGE = 1600

# Enhanced font scaling factors for different screen sizes
FONT_SCALE_SMALL = 0.8
FONT_SCALE_MEDIUM = 1.0
FONT_SCALE_LARGE = 1.2
FONT_SCALE_XLARGE = 1.4

# Enhanced spacing scaling factors
SPACING_SCALE_SMALL = 0.7
SPACING_SCALE_MEDIUM = 1.0
SPACING_SCALE_LARGE = 1.3
SPACING_SCALE_XLARGE = 1.6

# Layout adjustment factors
LAYOUT_COMPACT_THRESHOLD = 900
LAYOUT_COMFORTABLE_THRESHOLD = 1400

## RESPONSIVE LAYOUT MANAGER ###################################################
class ResponsiveLayoutManager:
    """
    Manages responsive layout behavior for the Fan Club GUI.
    Handles window size adaptation, dynamic font scaling, and adaptive spacing.
    """
    
    def __init__(self, root_window):
        """
        Initialize the responsive layout manager.
        
        Args:
            root_window: The main Tkinter window
        """
        self.root = root_window
        self.current_breakpoint = None
        self.current_font_scale = 1.0
        self.current_spacing_scale = 1.0
        self.current_layout_mode = 'comfortable'  # comfortable, compact, auto
        self.registered_widgets = []
        self.style = ttk.Style()
        
        # Enhanced minimum window size
        self.min_width = 700
        self.min_height = 500
        
        # Store original typography and spacing for restoration
        self.original_typography = dict(gus.typography)
        self.original_spacing = dict(gus.spacing)
        
        # Layout adjustment tracking
        self.last_width = 0
        self.last_height = 0
        self.resize_timer = None
        
        # Set initial window properties
        self._setup_window()
        
        # Bind resize event with improved handling
        self.root.bind('<Configure>', self._on_window_resize)
        
        # Initial layout update
        self.root.after(100, self._update_layout)
    
    def _setup_window(self):
        """Setup initial window properties and constraints."""
        try:
            # Set minimum window size
            self.root.minsize(self.min_width, self.min_height)
            
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Calculate optimal initial size (60% of screen)
            initial_width = int(screen_width * 0.6)
            initial_height = int(screen_height * 0.6)
            
            # Ensure minimum size
            initial_width = max(initial_width, self.min_width)
            initial_height = max(initial_height, self.min_height)
            
            # Center window on screen
            x = (screen_width - initial_width) // 2
            y = (screen_height - initial_height) // 2
            
            self.root.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
            
        except Exception as e:
            print(f"Error setting up window: {e}")
    
    def register_widget(self, widget, widget_type="default"):
        """
        Register a widget for responsive updates.
        
        Args:
            widget: The widget to register
            widget_type: Type of widget for specific handling
        """
        self.registered_widgets.append({
            'widget': widget,
            'type': widget_type
        })
    
    def _on_window_resize(self, event):
        """Handle window resize events with enhanced debouncing."""
        # Only handle resize events for the root window
        if event.widget == self.root:
            # Skip processing during window movement to prevent freezing
            try:
                # Check if this is just a window move (position change without size change)
                current_width = self.root.winfo_width()
                current_height = self.root.winfo_height()
                
                # Skip if dimensions haven't changed significantly (likely just a move)
                if (hasattr(self, 'last_width') and hasattr(self, 'last_height') and
                    abs(current_width - self.last_width) < 10 and 
                    abs(current_height - self.last_height) < 10):
                    return
                
                # Use the new debounced resize method
                self._debounced_resize(current_width, current_height)
            except (tk.TclError, AttributeError):
                # Widget destroyed or error, ignore
                pass
    
    def _update_layout(self):
        """Update layout based on current window size with enhanced logic."""
        try:
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            # Determine current breakpoint
            new_breakpoint = self._get_breakpoint(width)
            
            # Determine layout mode based on window size and user preference
            new_layout_mode = self._determine_layout_mode(width, height)
            
            # Update if breakpoint or layout mode changed
            breakpoint_changed = new_breakpoint != self.current_breakpoint
            layout_mode_changed = new_layout_mode != self.current_layout_mode
            
            if breakpoint_changed or layout_mode_changed:
                self.current_breakpoint = new_breakpoint
                self.current_layout_mode = new_layout_mode
                
                # Apply responsive styles with enhanced logic
                self._apply_responsive_styles()
                
                # Update registered widgets
                self._update_registered_widgets()
                
                # Apply layout-specific adjustments
                self._apply_layout_adjustments()
                
                # Force UI refresh
                self.root.update_idletasks()
                
        except Exception as e:
            print(f"Error updating responsive layout: {e}")
    
    def _get_breakpoint(self, width):
        """Determine the current breakpoint based on window width."""
        if width < BREAKPOINT_SMALL:
            return 'small'
        elif width < BREAKPOINT_MEDIUM:
            return 'medium'
        elif width < BREAKPOINT_LARGE:
            return 'large'
        else:
            return 'xlarge'
    
    def _determine_layout_mode(self, width, height):
        """Determine the optimal layout mode based on window dimensions."""
        # Calculate aspect ratio and available space
        aspect_ratio = width / height if height > 0 else 1.0
        total_area = width * height
        
        # Auto-determine layout mode based on space constraints
        if width < LAYOUT_COMPACT_THRESHOLD or total_area < 500000:
            return 'compact'
        elif width > LAYOUT_COMFORTABLE_THRESHOLD and total_area > 800000:
            return 'comfortable'
        else:
            return 'balanced'
    
    def _apply_layout_adjustments(self):
        """Apply layout-specific adjustments based on current mode."""
        try:
            if self.current_layout_mode == 'compact':
                self._apply_compact_layout()
            elif self.current_layout_mode == 'comfortable':
                self._apply_comfortable_layout()
            else:
                self._apply_balanced_layout()
        except Exception as e:
            print(f"Error applying layout adjustments: {e}")
    
    def _apply_compact_layout(self):
        """Apply compact layout optimizations."""
        # Reduce padding and margins for compact layout
        compact_spacing = {
            key: max(2, int(value * 0.6)) for key, value in self.original_spacing.items()
        }
        gus.spacing.update(compact_spacing)
        
        # Update ttk styles for compact layout
        self.style.configure("TNotebook.Tab", padding=(4, 2))
        self.style.configure("TButton", padding=(6, 3))
        
    def _apply_comfortable_layout(self):
        """Apply comfortable layout optimizations."""
        # Increase padding and margins for comfortable layout
        comfortable_spacing = {
            key: int(value * 1.4) for key, value in self.original_spacing.items()
        }
        gus.spacing.update(comfortable_spacing)
        
        # Update ttk styles for comfortable layout
        self.style.configure("TNotebook.Tab", padding=(16, 8))
        self.style.configure("TButton", padding=(12, 6))
        
    def _apply_balanced_layout(self):
        """Apply balanced layout optimizations."""
        # Use original spacing with slight adjustments
        balanced_spacing = {
            key: int(value * self.current_spacing_scale) for key, value in self.original_spacing.items()
        }
        gus.spacing.update(balanced_spacing)
        
        # Update ttk styles for balanced layout
        self.style.configure("TNotebook.Tab", padding=(8, 4))
        self.style.configure("TButton", padding=(8, 4))
    
    def _debounced_resize(self, width, height):
        """Handle window resize with debouncing for smoother performance."""
        try:
            # Cancel previous timer if exists
            if hasattr(self, 'resize_timer') and self.resize_timer:
                self.root.after_cancel(self.resize_timer)
                self.resize_timer = None
            
            # Calculate size difference
            width_diff = abs(width - self.last_width) if hasattr(self, 'last_width') else 0
            height_diff = abs(height - self.last_height) if hasattr(self, 'last_height') else 0
            
            # Skip micro-adjustments to prevent excessive processing
            if width_diff < 5 and height_diff < 5:
                return
            
            # Use longer delays to prevent freezing during window operations
            if width_diff > 100 or height_diff > 100:
                delay = 200  # Increased delay for major changes
            elif width_diff > 30 or height_diff > 30:
                delay = 300  # Increased delay for moderate changes
            else:
                delay = 500  # Much longer delay for small changes
            
            # Schedule the actual update with increased delay
            self.resize_timer = self.root.after(delay, lambda: self._execute_resize_update(width, height))
            
        except Exception as e:
            print(f"Error in debounced resize: {e}")
            # Clear timer on error
            if hasattr(self, 'resize_timer'):
                self.resize_timer = None
    
    def _execute_resize_update(self, width, height):
        """Execute the actual resize update."""
        try:
            # Check if widget still exists before processing
            if not self.root.winfo_exists():
                return
                
            # Update stored dimensions
            self.last_width = width
            self.last_height = height
            
            # Perform the layout update with error handling
            self._update_layout()
            
            # Clear the timer
            self.resize_timer = None
            
        except (tk.TclError, AttributeError) as e:
            print(f"Error executing resize update (widget destroyed): {e}")
            # Clear timer on widget destruction
            self.resize_timer = None
        except Exception as e:
            print(f"Error executing resize update: {e}")
            # Clear timer on any error
            self.resize_timer = None
    
    def _apply_responsive_styles(self):
        """Apply responsive styles with smooth transitions."""
        try:
            # Get scaling factors
            font_scale, spacing_scale = self._get_scale_factors()
            
            # Check if we should use smooth transition
            use_smooth_transition = (
                hasattr(self, 'current_font_scale') and 
                hasattr(self, 'current_spacing_scale') and
                abs(font_scale - self.current_font_scale) > 0.1
            )
            
            if use_smooth_transition:
                # Use smooth transition for significant changes
                self._smooth_scale_transition(font_scale, spacing_scale)
            else:
                # Direct update for small changes or initial setup
                self._update_typography(font_scale)
                self._update_spacing(spacing_scale)
                self.current_font_scale = font_scale
                self.current_spacing_scale = spacing_scale
            
            # Update widget-specific styles
            self._update_widget_styles()
            
        except Exception as e:
            print(f"Error applying responsive styles: {e}")
    
    def _get_scale_factors(self):
        """Get font and spacing scale factors for current breakpoint."""
        scales = {
            'small': (FONT_SCALE_SMALL, SPACING_SCALE_SMALL),
            'medium': (FONT_SCALE_MEDIUM, SPACING_SCALE_MEDIUM),
            'large': (FONT_SCALE_LARGE, SPACING_SCALE_LARGE),
            'xlarge': (FONT_SCALE_XLARGE, SPACING_SCALE_XLARGE)
        }
        return scales.get(self.current_breakpoint, (1.0, 1.0))
    
    def _update_typography(self, scale_factor):
        """Update typography with enhanced responsive scaling."""
        try:
            # Create scaled typography with improved algorithm
            scaled_typography = {}
            for key, config in self.original_typography.items():
                font_family, font_size, font_weight = config["font"]
                
                # Apply smart scaling based on font type and size
                if 'headline' in key:
                    # Headlines scale more aggressively
                    scaled_size = max(8, int(font_size * scale_factor * 1.1))
                elif 'title' in key:
                    # Titles scale moderately
                    scaled_size = max(7, int(font_size * scale_factor * 1.05))
                elif 'body' in key:
                    # Body text scales conservatively
                    scaled_size = max(6, int(font_size * scale_factor * 0.95))
                elif 'label' in key:
                    # Labels scale minimally
                    scaled_size = max(6, int(font_size * scale_factor * 0.9))
                else:
                    # Default scaling
                    scaled_size = max(6, int(font_size * scale_factor))
                
                # Ensure readable sizes
                if scaled_size < 8 and key in ['headline_large', 'headline_medium']:
                    scaled_size = 8
                elif scaled_size < 7 and 'title' in key:
                    scaled_size = 7
                
                scaled_typography[key] = {
                    "font": (font_family, scaled_size, font_weight)
                }
            
            # Update global typography reference
            gus.typography.update(scaled_typography)
            
        except Exception as e:
            print(f"Error updating typography: {e}")
    
    def _update_spacing(self, scale_factor):
        """Update spacing with enhanced responsive scaling."""
        try:
            # Create scaled spacing with layout mode consideration
            scaled_spacing = {}
            for key, value in self.original_spacing.items():
                # Apply different scaling based on layout mode
                if self.current_layout_mode == 'compact':
                    # More aggressive scaling down for compact mode
                    scaled_value = max(1, int(value * scale_factor * 0.7))
                elif self.current_layout_mode == 'comfortable':
                    # More generous scaling for comfortable mode
                    scaled_value = int(value * scale_factor * 1.3)
                else:
                    # Balanced scaling
                    scaled_value = max(2, int(value * scale_factor))
                
                # Ensure minimum spacing for usability
                if key == 'xs':
                    scaled_value = max(2, scaled_value)
                elif key == 'sm':
                    scaled_value = max(4, scaled_value)
                elif key == 'md':
                    scaled_value = max(6, scaled_value)
                
                scaled_spacing[key] = scaled_value
            
            # Update global spacing reference
            gus.spacing.update(scaled_spacing)
            
            # Update padding configurations with enhanced logic
            gus.pad_xs = {"padx": scaled_spacing["xs"], "pady": scaled_spacing["xs"]}
            gus.pad_sm = {"padx": scaled_spacing["sm"], "pady": scaled_spacing["sm"]}
            gus.pad_md = {"padx": scaled_spacing["md"], "pady": scaled_spacing["md"]}
            gus.pad_lg = {"padx": scaled_spacing["lg"], "pady": scaled_spacing["lg"]}
            
        except Exception as e:
            print(f"Error updating spacing: {e}")
    
    def _update_widget_styles(self):
        """Update ttk widget styles with responsive values."""
        try:
            # Check if root window and style still exist
            if not self.root or not self.root.winfo_exists():
                return
            if not hasattr(self, 'style') or not self.style:
                return
                
            # Get current theme colors
            base_bg = theme_manager.get_color('SURFACE_2')
            card_bg = theme_manager.get_color('SURFACE_1')
            fg = theme_manager.get_color('TEXT_PRIMARY')
            
            # Update basic widget styles with responsive fonts
            self.style.configure("TLabel", 
                                font=gus.typography["body_medium"]["font"],
                                background=base_bg, foreground=fg)
            
            self.style.configure("TButton", 
                                font=gus.typography["body_medium"]["font"],
                                padding=(gus.spacing["md"], gus.spacing["sm"]))
            
            self.style.configure("TEntry", 
                                font=gus.typography["body_medium"]["font"],
                                padding=gus.spacing["sm"])
            
            # Update notebook tabs
            tab_padding = (gus.spacing["lg"], gus.spacing["md"])
            if self.current_breakpoint == 'small':
                tab_padding = (gus.spacing["md"], gus.spacing["sm"])
            
            self.style.configure("TNotebook.Tab", 
                                font=gus.typography["body_medium"]["font"],
                                padding=tab_padding)
            
            # Update frame padding
            frame_padding = gus.spacing["md"]
            if self.current_breakpoint == 'small':
                frame_padding = gus.spacing["sm"]
            elif self.current_breakpoint in ['large', 'xlarge']:
                frame_padding = gus.spacing["lg"]
            
            self.style.configure("Card.TFrame", padding=frame_padding)
            
            # Update treeview row height
            row_height = 22
            if self.current_breakpoint == 'small':
                row_height = 18
            elif self.current_breakpoint in ['large', 'xlarge']:
                row_height = 26
            
            self.style.configure("Treeview", 
                                font=gus.typography["body_medium"]["font"],
                                rowheight=row_height)
            
        except (tk.TclError, AttributeError) as e:
            print(f"Error updating widget styles (application may be closing): {e}")
        except Exception as e:
            print(f"Error updating widget styles: {e}")
    
    def _update_registered_widgets(self):
        """Update all registered widgets with responsive behavior."""
        try:
            for widget_info in self.registered_widgets:
                widget = widget_info['widget']
                widget_type = widget_info['type']
                
                # Call widget-specific update method if it exists
                if hasattr(widget, 'update_responsive_layout'):
                    widget.update_responsive_layout(self.current_breakpoint, 
                                                   self.current_font_scale, 
                                                   self.current_spacing_scale)
                
                # Force widget update
                if hasattr(widget, 'update_idletasks'):
                    widget.update_idletasks()
                    
        except Exception as e:
            print(f"Error updating registered widgets: {e}")
    
    def get_current_breakpoint(self):
        """Get the current responsive breakpoint."""
        return self.current_breakpoint
    
    def get_scale_factors(self):
        """Get current font and spacing scale factors."""
        return self.current_font_scale, self.current_spacing_scale
    
    def force_update(self):
        """Force a responsive layout update."""
        self._update_layout()
    
    def _smooth_scale_transition(self, target_font_scale, target_spacing_scale, steps=5):
        """Apply smooth scaling transition for better user experience."""
        try:
            if not hasattr(self, '_current_font_scale'):
                self._current_font_scale = 1.0
            if not hasattr(self, '_current_spacing_scale'):
                self._current_spacing_scale = 1.0
            
            # Calculate step increments
            font_step = (target_font_scale - self._current_font_scale) / steps
            spacing_step = (target_spacing_scale - self._current_spacing_scale) / steps
            
            def apply_step(step_num):
                if step_num <= steps:
                    # Calculate current scale values
                    current_font = self._current_font_scale + (font_step * step_num)
                    current_spacing = self._current_spacing_scale + (spacing_step * step_num)
                    
                    # Apply the scaling
                    self._update_typography(current_font)
                    self._update_spacing(current_spacing)
                    
                    # Update registered widgets
                    self._update_registered_widgets()
                    
                    # Schedule next step
                    if step_num < steps:
                        self.root.after(20, lambda: apply_step(step_num + 1))
                    else:
                        # Final update
                        self._current_font_scale = target_font_scale
                        self._current_spacing_scale = target_spacing_scale
            
            # Start the transition
            apply_step(1)
            
        except Exception as e:
            print(f"Error in smooth scale transition: {e}")
            # Fallback to immediate update
            self._update_typography(target_font_scale)
            self._update_spacing(target_spacing_scale)
            self._update_registered_widgets()

## RESPONSIVE MIXIN ############################################################
class ResponsiveMixin:
    """
    Mixin class to add responsive behavior to widgets.
    """
    
    def setup_responsive(self, layout_manager):
        """Setup responsive behavior for this widget."""
        self.layout_manager = layout_manager
        layout_manager.register_widget(self)
    
    def update_responsive_layout(self, breakpoint, font_scale, spacing_scale):
        """
        Override this method in subclasses to implement custom responsive behavior.
        
        Args:
            breakpoint: Current breakpoint ('small', 'medium', 'large', 'xlarge')
            font_scale: Current font scaling factor
            spacing_scale: Current spacing scaling factor
        """
        pass

## UTILITY FUNCTIONS ###########################################################
def create_responsive_layout_manager(root_window):
    """
    Create and return a responsive layout manager for the given root window.
    
    Args:
        root_window: The main Tkinter window
        
    Returns:
        ResponsiveLayoutManager instance
    """
    return ResponsiveLayoutManager(root_window)

def get_responsive_font(base_font, scale_factor):
    """
    Get a scaled font tuple.
    
    Args:
        base_font: Base font tuple (family, size, weight)
        scale_factor: Scaling factor
        
    Returns:
        Scaled font tuple
    """
    family, size, weight = base_font
    scaled_size = max(6, int(size * scale_factor))
    return (family, scaled_size, weight)

def get_responsive_spacing(base_spacing, scale_factor):
    """
    Get scaled spacing value.
    
    Args:
        base_spacing: Base spacing value
        scale_factor: Scaling factor
        
    Returns:
        Scaled spacing value
    """
    return max(2, int(base_spacing * scale_factor))