from typing import Dict, Any, Optional, List


class StateManager:
    """Centralized state management for Khorium application"""
    
    def __init__(self, trame_state):
        self.state = trame_state
        self._defaults = self._get_default_state()
        self._validators = self._get_state_validators()
        
    def _get_default_state(self) -> Dict[str, Any]:
        """Define default state values organized by category"""
        return {
            # Mesh state
            "mesh_visible": False,
            "mesh_size_factor": 1.0,
        }
    
    def _get_state_validators(self) -> Dict[str, callable]:
        """Define validation functions for state variables"""
        return {
            "mesh_size_factor": lambda x: 0.01 <= x <= 100.0,
        }
    
    def initialize_state(self):
        """Initialize state with default values if not already set"""
        for key, default_value in self._defaults.items():
            if not self.state.has(key):
                setattr(self.state, key, default_value)
    
    
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
    
    
    def reset_all(self):
        """Reset all state to default values"""
        self.state.update(self._defaults)
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state"""
        current_state = self.state.to_dict()
        return {
            key: value for key, value in current_state.items()
            if not key.startswith("trame__")
        }
    
    # Convenience methods for common operations
    def show_mesh(self, visible: bool = True):
        """Show or hide mesh"""
        self.set("mesh_visible", visible)
    
    def set_mesh_size_factor(self, factor: float):
        """Set mesh size factor for mesh generation"""
        self.set("mesh_size_factor", factor)