from typing import Dict, Any, Optional, List
from enum import Enum


class StateCategory(Enum):
    """State categories for organized state management"""
    MESH = "mesh"
    VIEW = "view" 
    FILE = "file"
    UI = "ui"
    DATA = "data"


class StateManager:
    """Centralized state management for Khorium application"""
    
    def __init__(self, trame_state):
        self.state = trame_state
        self._defaults = self._get_default_state()
        self._validators = self._get_state_validators()
        
    def _get_default_state(self) -> Dict[str, Any]:
        """Define default state values organized by category"""
        return {
            # Mesh visualization state
            "mesh_visible": False,
            "mesh_wireframe": False,
            "mesh_opacity": 1.0,
            "mesh_color_mode": "solid",
            "mesh_show_edges": False,
            
            # View/Camera state
            "view_mode": "3d",
            "view_camera_position": None,
            "view_zoom_level": 1.0,
            "view_auto_rotate": False,
            "view_background_color": "#2e3440",
            
            # File management state
            "file_current_path": None,
            "file_loaded_files": [],
            "file_recent_files": [],
            "file_loading": False,
            "file_save_path": None,
            
            # UI state
            "ui_sidebar_open": True,
            "ui_toolbar_visible": True,
            "ui_active_tool": "rotate",
            "ui_loading": False,
            "ui_error_message": None,
            "ui_status_message": None,
            
            # Data processing state
            "data_active_dataset": None,
            "data_available_fields": [],
            "data_selected_field": None,
            "data_processing": False,
            "data_filter_settings": {},
        }
    
    def _get_state_validators(self) -> Dict[str, callable]:
        """Define validation functions for state variables"""
        return {
            "mesh_opacity": lambda x: 0.0 <= x <= 1.0,
            "view_mode": lambda x: x in ["2d", "3d", "split"],
            "view_zoom_level": lambda x: x > 0,
            "ui_active_tool": lambda x: x in ["rotate", "pan", "zoom", "select"],
        }
    
    def initialize_state(self):
        """Initialize state with default values if not already set"""
        for key, default_value in self._defaults.items():
            if not self.state.has(key):
                setattr(self.state, key, default_value)
    
    def get_category_state(self, category: StateCategory) -> Dict[str, Any]:
        """Get all state variables for a specific category"""
        prefix = f"{category.value}_"
        current_state = self.state.to_dict()
        return {
            key: value for key, value in current_state.items()
            if key.startswith(prefix)
        }
    
    def set_category_state(self, category: StateCategory, updates: Dict[str, Any]):
        """Update multiple state variables for a category"""
        prefixed_updates = {}
        prefix = f"{category.value}_"
        
        for key, value in updates.items():
            full_key = f"{prefix}{key}" if not key.startswith(prefix) else key
            
            # Validate if validator exists
            if full_key in self._validators:
                if not self._validators[full_key](value):
                    raise ValueError(f"Invalid value for {full_key}: {value}")
            
            prefixed_updates[full_key] = value
        
        self.state.update(prefixed_updates)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a state variable with optional default"""
        if self.state.has(key):
            return getattr(self.state, key)
        return default
    
    def set(self, key: str, value: Any):
        """Set a single state variable with validation"""
        if key in self._validators:
            if not self._validators[key](value):
                raise ValueError(f"Invalid value for {key}: {value}")
        
        setattr(self.state, key, value)
    
    def set_multiple(self, updates: Dict[str, Any]):
        """Set multiple state variables with validation"""
        validated_updates = {}
        
        for key, value in updates.items():
            if key in self._validators:
                if not self._validators[key](value):
                    raise ValueError(f"Invalid value for {key}: {value}")
            validated_updates[key] = value
        
        self.state.update(validated_updates)
    
    def flush_state(self, keys: Optional[List[str]] = None):
        """Force synchronization of state changes to client"""
        if keys:
            for key in keys:
                self.state.flush(key)
        else:
            # Flush all array/object state variables
            current_state = self.state.to_dict()
            for key, value in current_state.items():
                if isinstance(value, (list, dict)):
                    self.state.flush(key)
    
    def reset_category(self, category: StateCategory):
        """Reset a category to its default values"""
        prefix = f"{category.value}_"
        category_defaults = {
            key: value for key, value in self._defaults.items()
            if key.startswith(prefix)
        }
        self.state.update(category_defaults)
    
    def reset_all(self):
        """Reset all state to default values"""
        self.state.update(self._defaults)
    
    def get_state_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get organized summary of current state by category"""
        summary = {}
        current_state = self.state.to_dict()
        
        for category in StateCategory:
            prefix = f"{category.value}_"
            category_state = {
                key: value for key, value in current_state.items()
                if key.startswith(prefix)
            }
            summary[category.value] = category_state
            
        # Add uncategorized state
        categorized_keys = set()
        for category in StateCategory:
            prefix = f"{category.value}_"
            categorized_keys.update(
                key for key in current_state.keys() if key.startswith(prefix)
            )
        
        uncategorized = {
            key: value for key, value in current_state.items()
            if key not in categorized_keys and not key.startswith("trame__")
        }
        
        if uncategorized:
            summary["uncategorized"] = uncategorized
            
        return summary
    
    # Convenience methods for common operations
    def show_mesh(self, visible: bool = True):
        """Show or hide mesh"""
        self.set("mesh_visible", visible)
    
    def set_mesh_properties(self, opacity: float = None, wireframe: bool = None, 
                           color_mode: str = None, show_edges: bool = None):
        """Set multiple mesh properties at once"""
        updates = {}
        if opacity is not None:
            updates["mesh_opacity"] = opacity
        if wireframe is not None:
            updates["mesh_wireframe"] = wireframe
        if color_mode is not None:
            updates["mesh_color_mode"] = color_mode
        if show_edges is not None:
            updates["mesh_show_edges"] = show_edges
        
        if updates:
            self.set_multiple(updates)
    
    def set_loading(self, loading: bool, message: str = None):
        """Set loading state with optional message"""
        updates = {"ui_loading": loading}
        if message is not None:
            updates["ui_status_message"] = message
        self.set_multiple(updates)
    
    def set_error(self, error_message: str = None):
        """Set or clear error message"""
        self.set("ui_error_message", error_message)
    
    def load_file_state(self, filepath: str):
        """Update state when loading a new file"""
        self.set_multiple({
            "file_current_path": filepath,
            "file_loading": True,
            "ui_loading": True,
            "ui_error_message": None
        })
    
    def complete_file_load(self, success: bool = True, error_message: str = None):
        """Complete file loading operation"""
        updates = {
            "file_loading": False,
            "ui_loading": False
        }
        
        if success:
            updates["ui_status_message"] = "File loaded successfully"
            updates["ui_error_message"] = None
        else:
            updates["ui_error_message"] = error_message or "Failed to load file"
            
        self.set_multiple(updates)