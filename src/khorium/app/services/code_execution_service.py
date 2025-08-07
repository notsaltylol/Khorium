import os
import subprocess
import tempfile
import time
from typing import Dict, List, Optional

from khorium.app.core.constants import CURRENT_DIRECTORY


class CodeExecutionResult:
    """Container for code execution results"""
    
    def __init__(self, success: bool, stdout: str, stderr: str, 
                 exit_code: int, execution_time: float, error_message: str = ""):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.execution_time = execution_time
        self.error_message = error_message


class CodeExecutionService:
    """Simple service for executing Python code strings"""
    
    def __init__(self, default_timeout: int = 60):
        self.default_timeout = default_timeout
        self.max_output_size = 1024 * 1024  # 1MB max output
        
    def execute_code(self, code: str, args: Optional[List[str]] = None,
                    timeout: Optional[int] = None, working_dir: Optional[str] = None,
                    env_vars: Optional[Dict[str, str]] = None) -> CodeExecutionResult:
        """
        Execute Python code from a string
        
        Args:
            code: Python code string to execute
            args: List of command line arguments
            timeout: Maximum execution time in seconds
            working_dir: Working directory for execution
            env_vars: Additional environment variables
            
        Returns:
            CodeExecutionResult containing execution details
        """
        print(f">>> CODE_EXECUTION_SERVICE: Starting execution ({len(code)} chars)")
        
        # Set up execution parameters
        timeout = timeout or self.default_timeout
        working_dir = working_dir or os.getcwd()
        args = args or []
        
        # Create temporary file with the code
        temp_script_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_script_path = temp_file.name
            
            print(f">>> CODE_EXECUTION_SERVICE: Created temporary script: {temp_script_path}")
            
            # Build command
            cmd = ["python", temp_script_path] + args
            
            # Set up environment
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            
            start_time = time.time()
            
            # Execute the script
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                env=env,
                text=True,
                universal_newlines=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
                execution_time = time.time() - start_time
                
                # Truncate output if too large
                stdout = self._truncate_output(stdout)
                stderr = self._truncate_output(stderr)
                
                success = exit_code == 0
                
                if success:
                    print(f">>> CODE_EXECUTION_SERVICE: Code executed successfully in {execution_time:.2f}s")
                else:
                    print(f">>> CODE_EXECUTION_SERVICE: Code failed with exit code {exit_code}")
                
                return CodeExecutionResult(success, stdout, stderr, exit_code, execution_time)
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                execution_time = time.time() - start_time
                error_msg = f"Code execution timed out after {timeout} seconds"
                print(f">>> CODE_EXECUTION_SERVICE: {error_msg}")
                return CodeExecutionResult(False, "", error_msg, -1, execution_time, error_msg)
                
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0
            error_msg = f"Error executing code: {str(e)}"
            print(f">>> CODE_EXECUTION_SERVICE: {error_msg}")
            return CodeExecutionResult(False, "", error_msg, -1, execution_time, error_msg)
            
        finally:
            # Clean up temporary file
            if temp_script_path and os.path.exists(temp_script_path):
                try:
                    os.unlink(temp_script_path)
                    print(f">>> CODE_EXECUTION_SERVICE: Cleaned up temporary script")
                except:
                    pass
    
    def execute_code_with_input(self, code: str, stdin_input: str,
                               args: Optional[List[str]] = None,
                               timeout: Optional[int] = None,
                               working_dir: Optional[str] = None,
                               env_vars: Optional[Dict[str, str]] = None) -> CodeExecutionResult:
        """
        Execute Python code from a string with stdin input
        
        Args:
            code: Python code string to execute
            stdin_input: Input to pass to the code via stdin
            args: List of command line arguments
            timeout: Maximum execution time in seconds
            working_dir: Working directory for execution
            env_vars: Additional environment variables
            
        Returns:
            CodeExecutionResult containing execution details
        """
        print(f">>> CODE_EXECUTION_SERVICE: Starting execution with stdin ({len(code)} chars)")
        
        # Set up execution parameters
        timeout = timeout or self.default_timeout
        working_dir = working_dir or os.getcwd()
        args = args or []
        
        # Create temporary file with the code
        temp_script_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_script_path = temp_file.name
            
            print(f">>> CODE_EXECUTION_SERVICE: Created temporary script for stdin execution")
            
            # Build command
            cmd = ["python", temp_script_path] + args
            
            # Set up environment
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            
            start_time = time.time()
            
            # Execute the script with stdin
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                env=env,
                text=True,
                universal_newlines=True
            )
            
            try:
                stdout, stderr = process.communicate(input=stdin_input, timeout=timeout)
                exit_code = process.returncode
                execution_time = time.time() - start_time
                
                # Truncate output if too large
                stdout = self._truncate_output(stdout)
                stderr = self._truncate_output(stderr)
                
                success = exit_code == 0
                
                if success:
                    print(f">>> CODE_EXECUTION_SERVICE: Code with stdin executed successfully in {execution_time:.2f}s")
                else:
                    print(f">>> CODE_EXECUTION_SERVICE: Code with stdin failed with exit code {exit_code}")
                
                return CodeExecutionResult(success, stdout, stderr, exit_code, execution_time)
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                execution_time = time.time() - start_time
                error_msg = f"Code execution with stdin timed out after {timeout} seconds"
                print(f">>> CODE_EXECUTION_SERVICE: {error_msg}")
                return CodeExecutionResult(False, "", error_msg, -1, execution_time, error_msg)
                
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0
            error_msg = f"Error executing code with stdin: {str(e)}"
            print(f">>> CODE_EXECUTION_SERVICE: {error_msg}")
            return CodeExecutionResult(False, "", error_msg, -1, execution_time, error_msg)
            
        finally:
            # Clean up temporary file
            if temp_script_path and os.path.exists(temp_script_path):
                try:
                    os.unlink(temp_script_path)
                    print(f">>> CODE_EXECUTION_SERVICE: Cleaned up temporary script")
                except:
                    pass
    
    def _truncate_output(self, output: str) -> str:
        """Truncate output if it exceeds maximum size"""
        if len(output) > self.max_output_size:
            truncated = output[:self.max_output_size]
            truncated += f"\n... [Output truncated - exceeded {self.max_output_size} bytes]"
            return truncated
        return output
    
    def set_timeout(self, timeout: int):
        """Set the default execution timeout"""
        self.default_timeout = max(1, timeout)  # Minimum 1 second
        print(f">>> CODE_EXECUTION_SERVICE: Set timeout to {self.default_timeout}s")
    
    def set_max_output_size(self, size: int):
        """Set the maximum output size"""
        self.max_output_size = max(1024, size)  # Minimum 1KB
        print(f">>> CODE_EXECUTION_SERVICE: Set max output size to {self.max_output_size} bytes")
    
    def _get_mesh_file_context(self) -> Dict[str, str]:
        """Get context information about available mesh files"""
        context = {}
        
        # Check for uploaded STL file
        uploaded_stl_path = os.path.join(CURRENT_DIRECTORY, "uploaded.stl")
        if os.path.exists(uploaded_stl_path):
            context['UPLOADED_STL_PATH'] = uploaded_stl_path
            context['HAS_UPLOADED_STL'] = 'true'
            print(f">>> CODE_EXECUTION_SERVICE: Found STL file: {uploaded_stl_path}")
        else:
            context['UPLOADED_STL_PATH'] = ''
            context['HAS_UPLOADED_STL'] = 'false'
            print(f">>> CODE_EXECUTION_SERVICE: No STL file found at: {uploaded_stl_path}")
        
        # Check for uploaded VTU file
        uploaded_vtu_path = os.path.join(CURRENT_DIRECTORY, "cad_000.vtu")
        if os.path.exists(uploaded_vtu_path):
            context['UPLOADED_VTU_PATH'] = uploaded_vtu_path
            context['HAS_UPLOADED_VTU'] = 'true'
            print(f">>> CODE_EXECUTION_SERVICE: Found VTU file: {uploaded_vtu_path}")
        else:
            context['UPLOADED_VTU_PATH'] = ''
            context['HAS_UPLOADED_VTU'] = 'false'
        
        # Set working directory
        context['MESH_WORKING_DIR'] = CURRENT_DIRECTORY
        
        return context
    
    def _prepare_code_with_context(self, code: str) -> str:
        """Prepare code with mesh file context variables"""
        file_context = self._get_mesh_file_context()
        
        # Create context setup code
        context_code = f'''
# Auto-generated mesh file context
import os
import sys

# File paths (automatically set based on uploads)
uploaded_stl_path = "{file_context['UPLOADED_STL_PATH']}"
uploaded_vtu_path = "{file_context['UPLOADED_VTU_PATH']}"
working_dir = "{file_context['MESH_WORKING_DIR']}"
has_uploaded_stl = {file_context['HAS_UPLOADED_STL'] == 'true'}
has_uploaded_vtu = {file_context['HAS_UPLOADED_VTU'] == 'true'}

# Print context for user awareness
print(f"=== Mesh Execution Context ===")
print(f"Working directory: {{working_dir}}")
print(f"Has uploaded STL: {{has_uploaded_stl}}")
if has_uploaded_stl:
    print(f"Uploaded STL file: {{uploaded_stl_path}}")
if has_uploaded_vtu:
    print(f"Uploaded VTU file: {{uploaded_vtu_path}}")
print("=== User Code Output ===")

# User code starts below
'''
        
        return context_code + code
    
    def execute_mesh_code(self, code: str, timeout: Optional[int] = None, 
                         working_dir: Optional[str] = None) -> CodeExecutionResult:
        """
        Execute Python code with mesh file context
        
        Args:
            code: Python code string to execute
            timeout: Maximum execution time in seconds
            working_dir: Working directory for execution (defaults to CURRENT_DIRECTORY)
            
        Returns:
            CodeExecutionResult containing execution details
        """
        # Use default mesh working directory if not specified
        if not working_dir:
            working_dir = CURRENT_DIRECTORY
        
        # Get mesh file context as environment variables
        env_vars = self._get_mesh_file_context()
        
        # Prepare code with context variables
        enhanced_code = self._prepare_code_with_context(code)
        
        print(f">>> CODE_EXECUTION_SERVICE: Executing mesh code with STL context")
        print(f">>> CODE_EXECUTION_SERVICE: Working dir: {working_dir}")
        print(f">>> CODE_EXECUTION_SERVICE: Has STL: {env_vars['HAS_UPLOADED_STL']}")
        print(f">>> CODE_EXECUTION_SERVICE: Has VTU: {env_vars['HAS_UPLOADED_VTU']}")
        
        return self.execute_code(enhanced_code, timeout=timeout, working_dir=working_dir, env_vars=env_vars)