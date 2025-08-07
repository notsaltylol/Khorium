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
            
            # Mesh code execution state
            "execute_mesh_code": "",  # Code to execute via state change
            "mesh_code_current": "",
            "mesh_code_status": "idle",  # idle, running, completed, failed
            "mesh_code_error_message": "",
            "mesh_code_execution_start_time": None,
            "mesh_code_execution_end_time": None,
            "mesh_code_execution_duration": 0.0,
            "mesh_code_execution_complete": False,
            "mesh_code_result": {},
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
    
    # Mesh code execution convenience methods
    def set_mesh_code_execution_state(self, code: str, status: str, error_message: str = "",
                                     start_time: float = None, end_time: float = None,
                                     duration: float = 0.0, complete: bool = False,
                                     result: Dict = None):
        """Set comprehensive mesh code execution state"""
        updates = {
            "mesh_code_current": code,
            "mesh_code_status": status,
            "mesh_code_error_message": error_message,
            "mesh_code_execution_duration": duration,
            "mesh_code_execution_complete": complete,
        }
        
        if start_time is not None:
            updates["mesh_code_execution_start_time"] = start_time
        if end_time is not None:
            updates["mesh_code_execution_end_time"] = end_time
        if result is not None:
            updates["mesh_code_result"] = result
            
        self.set_multiple(updates)
    
    def start_mesh_code_execution(self, code: str):
        """Mark start of mesh code execution"""
        import time
        self.set_multiple({
            "mesh_code_current": code,
            "mesh_code_status": "running",
            "mesh_code_error_message": "",
            "mesh_code_execution_start_time": time.time(),
            "mesh_code_execution_complete": False,
        })
    
    def complete_mesh_code_execution(self, success: bool, result: Dict, error_message: str = ""):
        """Mark completion of mesh code execution"""
        import time
        end_time = time.time()
        start_time = self.get("mesh_code_execution_start_time", end_time)
        duration = end_time - start_time
        
        self.set_multiple({
            "mesh_code_status": "completed" if success else "failed",
            "mesh_code_error_message": error_message,
            "mesh_code_execution_end_time": end_time,
            "mesh_code_execution_duration": duration,
            "mesh_code_execution_complete": True,
            "mesh_code_result": result,
        })
    
    def clear_mesh_code_execution(self):
        """Clear mesh code execution state"""
        self.set_multiple({
            "mesh_code_current": "",
            "mesh_code_status": "idle",
            "mesh_code_error_message": "",
            "mesh_code_execution_start_time": None,
            "mesh_code_execution_end_time": None,
            "mesh_code_execution_duration": 0.0,
            "mesh_code_execution_complete": False,
            "mesh_code_result": {},
        })
    
    def is_mesh_code_running(self) -> bool:
        """Check if mesh code is currently executing"""
        return self.get("mesh_code_status") == "running"
    
    def get_mesh_code_execution_summary(self) -> Dict[str, Any]:
        """Get summary of current mesh code execution state"""
        return {
            "current_code": self.get("mesh_code_current", ""),
            "status": self.get("mesh_code_status", "idle"),
            "error_message": self.get("mesh_code_error_message", ""),
            "execution_complete": self.get("mesh_code_execution_complete", False),
            "execution_duration": self.get("mesh_code_execution_duration", 0.0),
            "start_time": self.get("mesh_code_execution_start_time"),
            "end_time": self.get("mesh_code_execution_end_time"),
            "result": self.get("mesh_code_result", {}),
        }