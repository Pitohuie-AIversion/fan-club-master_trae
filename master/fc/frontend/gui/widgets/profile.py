################################################################################
## Project: Fanclub Mark IV "Master" profile GUI  ## File: profile.py         ##
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY ## ADVANCED SYSTEMS LABORATORY ##                     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __  __   __                  ##
##                  | | |  | |  | T_| | || |    |  ||_ | | _|                 ##
##                  | _ |  |T|  |  |  |  _|      ||   \\_//                   ##
##                  || || |_ _| |_|_| |_| _|    |__|  |___|                   ##
##                                                                            ##
##----------------------------------------------------------------------------##
## zhaoyang                   ## <mzymuzhaoyang@gmail.com>  ##                ##
## dashuai                    ## <dschen2018@gmail.com>     ##                ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + GUI Component in charge of displaying and manipulating FC profiles.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import tkinter as tk
import tkinter.ttk as ttk

from fc import archive as ac, printer as pt
from fc.builtin import profiles as btp
from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.widgets import loader as ldr
from fc.frontend.gui.theme import BG_ACCENT

## AUXILIARY GLOBALS ###########################################################
TAG_SUB = "M"
TAG_PRIMITIVE = "P"
TAG_LIST = "L"

## MAIN ########################################################################
class ProfileDisplay(ttk.Frame, pt.PrintClient):
    SYMBOL = "[PD]"

    def __init__(self, master, archive, callback, pqueue):
        """
        Build an empty FC profile display in container MASTER.
        - master := Tkinter parent widget
        - archive := FC Archive instance
        - callback := method to call without arguments to apply profile changes
        - pqueue := Queue object to use for I-P printing
        """
        ttk.Frame.__init__(self, master = master)
        pt.PrintClient.__init__(self, pqueue, self.SYMBOL)

        # Auto-update mechanism for external archive modifications
        self._auto_update_enabled = True
        self._last_archive_hash = None
        self._update_check_interval = 1000  # milliseconds
        
        # Core setup ..........................................................
        self.archive = archive
        self.callback = callback
        self.map = {}
        self.root = ''
        
        # Initialize auto-update monitoring
        self._schedule_update_check()

        # Grid:
        self.grid_rowconfigure(0, weight = 0)
        self.grid_rowconfigure(1, weight = 0)
        self.grid_rowconfigure(2, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(2, weight = 1)
        self.numcolumns = 3

        # Callbacks:
        self.applyCallback = callback if callback else self._nothing

        # File I/O:
        self.loader = ldr.Loader(self, (("Fan Club Profile",".fcp"),))

        # Build top bar ........................................................
        self.topBar = ttk.Frame(self)
        self.topBar.grid(row = 0, columnspan = self.numcolumns, sticky = "EW")

        self.topLabel = ttk.Label(self.topBar, text = "Profile:   ",
            justify = tk.LEFT)
        self.topLabel.pack(side = tk.LEFT)

        self.defaultButton = ttk.Button(self.topBar, text="Default", command=self._default)
        self.defaultButton.pack(side=tk.LEFT, padx=5)

        self.loadButton = ttk.Button(self.topBar, text="Load", command=self._load)
        self.loadButton.pack(side=tk.LEFT, padx=5)

        self.saveButton = ttk.Button(self.topBar, text="Save", command=self._save)
        self.saveButton.pack(side=tk.LEFT, padx=5)

        self.applyButton = ttk.Button(self.topBar, text="Apply", command=self.applyCallback)
        self.applyButton.pack(side=tk.LEFT, padx=5)

        # Built-in menu:
        self.builtin = btp.PROFILES
        builtinkeys = ("N/A",) + tuple(self.builtin.keys())
        self.builtinFrame = ttk.Frame(self.topBar)
        self.builtinFrame.pack(side = tk.RIGHT)
        self.builtinLabel = ttk.Label(self.builtinFrame,
            text = "Built-in: ")
        self.builtinLabel.pack(side = tk.LEFT)
        self.builtinMenuVar = tk.StringVar()
        self.builtinMenuVar.trace('w', self._onBuiltinMenuChange)
        self.builtinMenuVar.set(builtinkeys[0])
        self.builtinMenu = ttk.Combobox(self.builtinFrame, textvariable=self.builtinMenuVar,
            values=builtinkeys, state="readonly")
        self.builtinMenu.pack(side = tk.LEFT, expand = True)

        # Build display ........................................................
        self.displayFrame = ttk.Frame(self)
        self.displayFrame.grid(row = 2, column = 0, sticky = "NEWS", pady = 10)

        self.font = tk.font.Font(font = gus.typography["headline_large"]["font"])

        self.display = ttk.Treeview(self.displayFrame)
        self.display.configure(columns = ("Attribute", "Value"))
        self.display.column("#0", width = self.font.measure("    "),
            stretch = False)
        self.display.column("Attribute")
        self.display.column("Value")
        self.display.heading("Attribute", text = "Attribute")
        self.display.heading("Value", text = "Value")
        self.display.pack(fill = tk.BOTH, expand = True)

        self.display.tag_configure(TAG_SUB, font = gus.typography["label_small"]["font"])
        self.display.tag_configure(TAG_LIST, font = gus.typography["label_small"]["font"])

        for event in ("<ButtonRelease-1>", "<KeyRelease-Up>",
            "<KeyRelease-Down>"):
            self.display.bind(event, self._check_editability)

        for event in ("<KeyRelease-Return>", "<Double-Button-1>"):
            self.display.bind(event, self._on_double)

        # Build editor ........................................................
        self.editorFrame = ttk.Frame(self, relief = tk.RIDGE, style="Card.TFrame")
        self.editorFrame.grid(row = 2, column = 2, sticky = "NEWS", pady = 10)

        self.editor = PythonEditor(self.editorFrame,
            add_callback = self._on_add, edit_callback = self._on_edit,
            remove_callback = self._on_remove,
            printx = self._nothing, printr = self._nothing)
        self.editor.pack(fill = tk.BOTH, expand= True)


        # Scrollbar:
        self.scrollbar = ttk.Scrollbar(self)
        self.scrollbar.grid(row = 2, column = 1, pady = 10, sticky = "NS")
        self.scrollbar.config(command = self.display.yview)
        self.display.config(yscrollcommand = self.scrollbar.set)

        self.build()

    # API ----------------------------------------------------------------------
    def build(self):
        """
        Rebuild the displayed values based on the current profile attributes in
        the loaded archive.
        """
        self.clear()
        self.root = \
            self._addModule(self.archive[ac.name], self.archive.profile(), 0)
        self.display.item(self.root, open = True)

    def clear(self):
        """
        Remove all entries from the display.
        """
        if self.root:
            self.display.delete(self.root)
            self.map = {}

    # Internal methods ---------------------------------------------------------
    def _addModule(self, name, module, precedence, parent = ''):
        """
        Add MODULE to the display
        """
        iid = self.display.insert(parent, precedence, values = (name, ''),
            tag = TAG_SUB)
        for child in module:
            meta = self.archive.meta[child]
            if meta[ac.TYPE] is ac.TYPE_LIST:
                self._addList(meta[ac.NAME], module[child], meta[ac.PRECEDENCE],
                iid)
            elif meta[ac.TYPE] is ac.TYPE_SUB:
                self._addModule(meta[ac.NAME], module[child],
                meta[ac.PRECEDENCE], iid)
            elif meta[ac.TYPE] is ac.TYPE_MAP:
                self._addMap(meta[ac.NAME], module[child], meta[ac.PRECEDENCE],
                    iid)
            else:
                self._addPrimitive(meta[ac.NAME], module[child],
                    meta[ac.PRECEDENCE], iid)
        self.map[iid] = (name, module)
        return iid


    def _addPrimitive(self, name, value, precedence, parent = ''):
        iid = self.display.insert(parent, precedence, values = (name,
            repr(value)))
        self.map[iid] = (name, value)
        return iid

    def _addMap(self, name, M, precedence, parent = ''):
        iid = self.display.insert(parent, precedence, values = (name, ''),
            tag = TAG_SUB)
        for key in M:
            iid_c = self.display.insert(iid, 0, values = (key, M[key]))
        return iid

    def _addList(self, name, iterable, precedence, parent = ''):
        iid = self.display.insert(parent, precedence, values = (name, ''),
            tag = TAG_LIST)

        indexer = self.archive.defaults[ac.INVERSE[name]][ac.INDEXER]
        for element in iterable:
            # Add list elements as modules or primitives based on type
            element_iid = self._addModule(indexer(element), element, indexer(element), iid)
            self.map[element_iid] = (indexer(element), element)
        return iid

    # Callbacks ----------------------------------------------------------------
    def _default(self, event = None):
        """
        Switch to the default profile and display it.
        """
        self.archive.default()
        self.build()
        self.callback()

    def _save(self, event = None):
        """
        Save the current profile.
        """
        name = self.loader.saveDialog("fan_array_profile")
        if name:
            self.archive.save(name)

    def _load(self, event = None):
        """
        Load a new profile.
        """
        name = self.loader.loadDialog()
        if name:
            self.archive.load(name)
            self.build()
            self.callback()

    def _check_editability(self, event = None):
        """
        To be called when a new attribute is selected. Checks whether the
        attribute can be edited and, if so, how (by changing it, adding to it,
        or deleting it)

        See:
        https://stackoverflow.com/questions/30614279/
            python-tkinter-tree-get-selected-item-values

        """


        iid = self.display.focus()
        if iid == self.root:
            self.editor._untouchable()
            return

        parent_iid = self.display.parent(iid)
        parent_key = ac.INVERSE[self.display.item(parent_iid)['values'][0]] if \
            parent_iid != self.root else None
        T_parent = self.archive.meta[parent_key][ac.TYPE] if parent_key \
            else None

        name, value = self.display.item(iid)['values']

        if T_parent is ac.TYPE_MAP:
            self.editor._map_item_editable(name, value)
            return

        if T_parent is ac.TYPE_LIST:
            self.editor._list_item_editable(name, value)
            return

        key = ac.INVERSE[name]
        meta = self.archive.meta[key]
        T = meta[ac.TYPE]

        if T is ac.TYPE_PRIMITIVE:
            self.editor._editable(meta[ac.EDITABLE], value)
            self.editor._addable(False)
            self.editor._removable(False)
            return
        elif T is ac.TYPE_LIST:
            self.editor._list_editable()
            return
        elif T is ac.TYPE_MAP:
            self.editor._map_editable()
            return

        self.editor._untouchable()

    def _on_double(self, event = None):
        """
        To be called on double clicks. Checks whether an item is editable and,
        if so, edits it.
        """
        self._nothing()


    def _on_add(self, value, key = None):
        """
        Callback for when an "addition" to a list is evaluated. Adds the given
        value to the currently selected list (or map) attribute.
        """
        iid = self.display.focus()
        name = self.display.item(iid)['values'][0]
        key = ac.INVERSE[name]

        try:
            # Validate the value using the appropriate validator
            self.archive.meta[key][ac.VALIDATOR](value)
        except ValueError as e:
            self.printx(f"Validation error: {e}")
            return
        except Exception as e:
            self.printx(f"Unexpected error during validation: {e}")
            return

        value = self.archive[self.archive.defaults[key][ac.KEY]]
        self.archive.add(key, value)

        #iid = self.display.insert(iid, 0,
        #    values = ('', value), tag = TAG_PRIMITIVE)
        self.build()

    def _on_edit(self, value):
        """
        Callback for when an attribute's new value is evaluated. Validates the
        given value and stores it within the currently selected attribute.
        """
        iid = self.display.focus()
        name = self.display.item(iid)['values'][0]
        key = ac.INVERSE[name]
        self.archive.meta[key][ac.VALIDATOR](value)
        self.archive.set(key, value)
        self.display.item(iid, values = (name, value))

    def _on_remove(self, event = None):
        """
        Callback for when the Remove button is pressed. Removes the currently
        selected attribute.
        """
        iid = self.display.focus()
        if iid == self.root:
            self.printx("Cannot remove root item")
            return
            
        parent_iid = self.display.parent(iid)
        if parent_iid == self.root:
            self.printx("Cannot remove top-level configuration items")
            return
            
        parent_name = self.display.item(parent_iid)['values'][0]
        parent_key = ac.INVERSE[parent_name]
        parent_meta = self.archive.meta[parent_key]
        
        # Only allow removal from lists and maps
        if parent_meta[ac.TYPE] not in (ac.TYPE_LIST, ac.TYPE_MAP):
            self.printx("Can only remove items from lists or maps")
            return
            
        try:
            item_name, item_value = self.display.item(iid)['values']
            
            if parent_meta[ac.TYPE] == ac.TYPE_LIST:
                # For lists, remove by value
                current_list = list(self.archive[parent_key])
                if item_value in current_list:
                    current_list.remove(item_value)
                    self.archive.set(parent_key, tuple(current_list))
                else:
                    self.printx(f"Item {item_value} not found in list")
                    return
            elif parent_meta[ac.TYPE] == ac.TYPE_MAP:
                # For maps, remove by key
                current_map = dict(self.archive[parent_key])
                if item_name in current_map:
                    del current_map[item_name]
                    self.archive.set(parent_key, current_map)
                else:
                    self.printx(f"Key {item_name} not found in map")
                    return
                    
            # Rebuild the display to reflect changes
            self.build()
            self.printx(f"Successfully removed item from {parent_name}")
            
        except Exception as e:
            self.printx(f"Error removing item: {e}")


    # Auto-update mechanism ---------------------------------------------------
    def _schedule_update_check(self):
        """
        Schedule the next archive update check using Tkinter's after method.
        """
        if self._auto_update_enabled:
            self.after(self._update_check_interval, self._check_archive_updates)
    
    def _check_archive_updates(self):
        """
        Check if the archive has been modified externally and update display if needed.
        """
        try:
            # Calculate current archive hash
            current_hash = self._calculate_archive_hash()
            
            # Check if archive has changed
            if self._last_archive_hash is not None and current_hash != self._last_archive_hash:
                self.printx("[AUTO-UPDATE] Archive modified externally, refreshing display...")
                self.build()  # Rebuild the display
                
            # Update stored hash
            self._last_archive_hash = current_hash
            
        except Exception as e:
            self.printx(f"[AUTO-UPDATE] Error checking archive updates: {e}")
        
        # Schedule next check
        self._schedule_update_check()
    
    def _calculate_archive_hash(self):
        """
        Calculate a hash of the current archive state for change detection.
        """
        import hashlib
        import json
        
        try:
            # Get current profile as dictionary
            profile_data = self.archive.profile()
            
            # Convert to JSON string for consistent hashing
            profile_json = json.dumps(profile_data, sort_keys=True, default=str)
            
            # Calculate hash
            return hashlib.md5(profile_json.encode()).hexdigest()
            
        except Exception as e:
            # Fallback: use string representation
            return hashlib.md5(str(self.archive.profile()).encode()).hexdigest()
    
    def enable_auto_update(self, enabled=True):
        """
        Enable or disable automatic update checking.
        
        - enabled: bool, whether to enable auto-update monitoring
        """
        self._auto_update_enabled = enabled
        if enabled:
            self.printx("[AUTO-UPDATE] Automatic update monitoring enabled")
            self._schedule_update_check()
        else:
            self.printx("[AUTO-UPDATE] Automatic update monitoring disabled")
    
    def set_update_interval(self, interval_ms):
        """
        Set the interval for checking archive updates.
        
        - interval_ms: int, interval in milliseconds (minimum 100ms)
        """
        if interval_ms < 100:
            interval_ms = 100
            self.printx("[AUTO-UPDATE] Minimum update interval is 100ms")
            
        self._update_check_interval = interval_ms
        self.printx(f"[AUTO-UPDATE] Update check interval set to {interval_ms}ms")

    # Auxiliary ----------------------------------------------------------------
    def _nothing(*args):
        """
        Placeholder for unnasigned callbacks.
        """
        pass

    def _loadBuiltin(self, name):
        """
        Load the given built-in profile.
        - name := String, name of the built-in profile, as defined in
            fc.builtin.profiles.
        """
        try:
            # Validate profile name
            if name not in self.builtin:
                self.printx(f"Error: Built-in profile '{name}' not found")
                available_profiles = ", ".join(self.builtin.keys())
                self.printx(f"Available profiles: {available_profiles}")
                return False
                
            # Get the profile data
            profile_data = self.builtin[name]
            
            # Validate profile data structure
            if not isinstance(profile_data, dict):
                self.printx(f"Error: Invalid profile data for '{name}' - expected dictionary")
                return False
                
            # Check for required profile fields
            required_fields = [ac.name, ac.description]
            missing_fields = [field for field in required_fields if field not in profile_data]
            if missing_fields:
                self.printx(f"Warning: Profile '{name}' missing fields: {missing_fields}")
                
            # Load the profile into archive
            self.archive.profile(profile_data)
            
            # Rebuild the display
            self.build()
            
            # Apply the changes
            self.callback()
            
            # Provide user feedback
            profile_name = profile_data.get(ac.name, name)
            self.printx(f"Successfully loaded built-in profile: {profile_name}")
            
            return True
            
        except KeyError as e:
            self.printx(f"Error accessing profile data for '{name}': {e}")
            return False
        except Exception as e:
            self.printx(f"Unexpected error loading built-in profile '{name}': {e}")
            return False

    def _onBuiltinMenuChange(self, *event):
        """
        Callback for changes to the built-in profile menu.
        """
        name = self.builtinMenuVar.get()
        if name != "N/A":
            self._loadBuiltin(name)

    # Editors ------------------------------------------------------------------
    def _edit_generic(self, attribute, current = None):
        """
        Return the result of evaluating a Python expression to get a value for
        ATTRIBUTE, enforcing the corresponding validator. CURRENT is the current
        value of said attribute, if any.
        """
        try:
            # Get attribute metadata
            meta = self.archive.meta[attribute]
            attribute_name = meta[ac.NAME]
            validator = meta[ac.VALIDATOR]
            editable = meta[ac.EDITABLE]
            
            # Check if attribute is editable
            if not editable:
                self.printx(f"Attribute '{attribute_name}' is not editable")
                return None
                
            # Preset the editor with current value
            if current is not None:
                self.editor.preset(current)
            else:
                # Try to get current value from archive
                try:
                    current_value = self.archive[attribute]
                    self.editor.preset(current_value)
                except KeyError:
                    self.printx(f"No current value found for '{attribute_name}'")
                    
            # Get the new value from editor
            try:
                new_value = self.editor._eval()
                
                # Validate the new value
                validator(new_value)
                
                # Set the new value in archive
                self.archive.set(attribute, new_value)
                
                # Rebuild display to show changes
                self.build()
                
                self.printx(f"Successfully updated '{attribute_name}' to: {new_value}")
                return new_value
                
            except ValueError as e:
                self.printx(f"Validation error for '{attribute_name}': {e}")
                return None
            except Exception as e:
                self.printx(f"Error evaluating expression for '{attribute_name}': {e}")
                return None
                
        except KeyError:
            self.printx(f"Unknown attribute: {attribute}")
            return None
        except Exception as e:
            self.printx(f"Unexpected error in _edit_generic: {e}")
            return None


class PythonEditor(ttk.Frame):

    OUTPUT_ERROR_CONFIG = {'bg' : "#510000", 'fg' : "red"}
    OUTPUT_NORMAL_CONFIG = {'bg' : "white", 'fg' : "black"}

    def __init__(self, master, add_callback, edit_callback, remove_callback,
        printr, printx):
        ttk.Frame.__init__(self, master)

        self.add_callback = add_callback
        self.edit_callback = edit_callback
        self.remove_callback = remove_callback
        self.printr = printr
        self.printx = printx

        self.grid_columnconfigure(1, weight = 1)
        row = 0

        self.topLabel = ttk.Label(self, text = \
            "Value editor (as Python 3.7 expression):", anchor = tk.W)
        self.topLabel.grid(row = row, column = 0, columnspan = 2, sticky = "EW")
        row += 1

        self.font = tk.font.Font(font = gus.typography["code"]["font"])
        self.tabstr = "  "
        self.tabsize = self.font.measure(self.tabstr)
        self.realtabs = "    "

        # Input ...............................................................
        self.grid_rowconfigure(row, weight = 1)
        conf = dict(gus.text_conf)
        conf["font"] = self.font
        conf["tabs"] = self.tabsize
        self.input = tk.Text(self,
            width = 30, height = 2, padx = 10, pady = 0,
            **conf)
        self.input.grid(row = row, column = 1, rowspan = 2, sticky = "NEWS")

        # For scrollbar, see:
        # https://www.python-course.eu/tkinter_text_widget.php

        self.input_scrollbar = ttk.Scrollbar(self)
        self.input_scrollbar.grid(row = row, column = 2, rowspan = 1,
            sticky = "NS")
        self.input_scrollbar.config(command = self.input.yview)
        self.input.config(yscrollcommand = self.input_scrollbar.set)
        row += 1

        # Buttons ..............................................................
        self.buttonFrame = ttk.Frame(self)
        self.buttonFrame.grid(row = row, column = 0, columnspan = 2,
            sticky = "WE")
        self.editButtons = []

        self.addButton = ttk.Button(self.buttonFrame, text="Add to", command=self._add)
        self.addButton.pack(side = tk.LEFT)
        self.editButtons.append(self.addButton)

        self.editButton = ttk.Button(self.buttonFrame, text="Edit", command=self._edit)
        self.editButton.pack(side = tk.LEFT)
        self.editButtons.append(self.editButton)

        self.removeButton = ttk.Button(self.buttonFrame, text="Remove", style="Secondary.TButton", command=self._remove)
        self.removeButton.pack(side = tk.LEFT)
        self.editButtons.append(self.removeButton)

        row += 1

        # Output ...............................................................
        self.grid_rowconfigure(row, weight = 1)
        self.output = tk.Text(self, font = self.font,
            width = 30, height = 2, padx = 10, pady = 0, tabs = self.tabsize,
            state = tk.DISABLED, **self.OUTPUT_NORMAL_CONFIG)
        self.output.grid(row = row, column = 1, rowspan = 2, sticky = "NEWS")

        # For scrollbar, see:
        # https://www.python-course.eu/tkinter_text_widget.php

        self.output_scrollbar = ttk.Scrollbar(self)
        self.output_scrollbar.grid(row = row, column = 2, rowspan = 1,
            sticky = "NS")
        self.output_scrollbar.config(command = self.output.yview)
        self.output.config(yscrollcommand = self.output_scrollbar.set)
        row += 1

    def _eval_error(self, e):
        """
        Handle the case of an exception happening during evaluation.
        Provides detailed error information and user-friendly messages.
        """
        import traceback
        
        # Categorize error types and provide specific messages
        error_type = type(e).__name__
        error_message = str(e)
        
        if isinstance(e, SyntaxError):
            user_message = f"Syntax Error: Invalid Python expression\n{error_message}"
            suggestion = "Check for missing quotes, parentheses, or invalid syntax"
        elif isinstance(e, NameError):
            user_message = f"Name Error: Undefined variable or function\n{error_message}"
            suggestion = "Make sure all variables and functions are properly defined"
        elif isinstance(e, ValueError):
            user_message = f"Value Error: Invalid value or type\n{error_message}"
            suggestion = "Check that the value matches the expected format"
        elif isinstance(e, TypeError):
            user_message = f"Type Error: Incorrect data type\n{error_message}"
            suggestion = "Verify the data type matches what's expected"
        elif isinstance(e, KeyError):
            user_message = f"Key Error: Missing dictionary key\n{error_message}"
            suggestion = "Check that all required keys are present"
        elif isinstance(e, IndexError):
            user_message = f"Index Error: List index out of range\n{error_message}"
            suggestion = "Verify the list index is within valid range"
        elif isinstance(e, AttributeError):
            user_message = f"Attribute Error: Missing attribute or method\n{error_message}"
            suggestion = "Check that the object has the specified attribute"
        else:
            user_message = f"{error_type}: {error_message}"
            suggestion = "Please check your input and try again"
        
        # Format the complete error message
        full_message = f"Evaluation Error:\n{user_message}\n\nSuggestion: {suggestion}"
        
        # Print to output with error formatting
        self._print(full_message)
        self.output.config(**self.OUTPUT_ERROR_CONFIG)
        
        # Log detailed error information for debugging
        try:
            if hasattr(self, 'printx'):
                self.printx(f"[DEBUG] {error_type} in evaluation: {error_message}")
                # Include traceback for debugging (first few lines only)
                tb_lines = traceback.format_exc().split('\n')[:5]
                self.printx(f"[DEBUG] Traceback: {' | '.join(tb_lines)}")
        except:
            # Fallback if printx is not available
            pass
        
        # Return False to indicate error occurred
        return False

    def clear(self):
        """
        Clear both text fields.
        """
        self.clear_input()
        self.clear_output()

    def clear_input(self):
        """
        Clear the input text field.
        """
        self.input.delete(1.0, tk.END)

    def clear_output(self):
        """
        Clear the output text field.
        """
        self.output.config(state = tk.NORMAL, **self.OUTPUT_NORMAL_CONFIG)
        self.output.delete(1.0, tk.END)
        self.output.config(state = tk.DISABLED)

    def preset(self, value):
        """
        Set the input to the expression that evaluates to VALUE.
        """
        self.clear()
        self.input.insert(tk.END, str(value) + "\n")

    def _eval(self, *E):
        """
        Evaluate the expression in the input field and return its value.
        """
        raw = self.input.get(1.0, tk.END)
        result = eval(raw)
        self._output(result)
        return result

    def _edit(self, *E):
        """
        To be called when the Edit button is clicked. Parse the expression and
        pass it to the given callback.
        """
        try:
            self.edit_callback(self._eval())
        except Exception as e:
            self._eval_error(e)

    def _add(self, event = None):
        try:
            self.add_callback(None)
        except Exception as e:
            self._eval_error(e)

    def _remove(self, event = None):
        try:
            self.clear()
            self.remove_callback()
        except Exception as e:
            self._eval_error(e)

    def _print(self, text):
        """
        Print TEXT to the output space.
        """
        try:
            self.clear_output()
            self.output.config(state = tk.NORMAL)
            self.output.insert(tk.END, text + "\n")
            self.output.config(state = tk.DISABLED)
        except Exception as e:
            self.printx("Exception when displaying Python output: ", e)

    def _output(self, value):
        """
        Display the generic Python value VALUE in the output space.
        """
        self._print(str(value))

    # Editability functions ----------------------------------------------------
    def _untouchable(self):
        """
        Disable all edit buttons.
        """
        for button in self.editButtons:
            button.config(state = tk.DISABLED)

    def _list_editable(self):
        """
        Enable buttons for a list attribute.
        """
        self._editable(False)
        self._addable(True)
        self._removable(False)

    def _map_editable(self):
        """
        Enable buttons for a map attribute.
        """
        self._editable(False)
        self._addable(True)
        self._removable(False)

    def _list_item_editable(self, index, value):
        """
        Enable buttons for a list item attribute.
        """
        self._editable(True, value)
        self._addable(False)
        self._removable(True)

    def _map_item_editable(self, key, value):
        """
        Enable buttons for a map item attribute.
        """
        self._editable(True,(key, value))
        self._addable(False)
        self._removable(True)

    def _editable(self, value, preset = None):
        """
        Set whether the currently selected value can be edited.
        """
        self.clear_output()
        self.editButton.config(state = tk.NORMAL if value else tk.DISABLED)
        if value and preset:
            self.preset(preset)
        else:
            self.clear_input()

    def _addable(self, value):
        """
        Set whether the currently selected value can be added-to.
        """
        self.addButton.config(state = tk.NORMAL if value else tk.DISABLED)

    def _removable(self, value):
        """
        Set whether the currently selected value can be removed.
        """
        self.removeButton.config(state = tk.NORMAL if value else tk.DISABLED)




## DEMO ########################################################################
