import os
import re
import shutil
from trame.app.file_upload import ClientFile

from khorium.app.core.constants import CURRENT_DIRECTORY


class FileService:
    """Service for handling file operations"""
    
    def __init__(self):
        pass
    
    def process_uploaded_files(self, files) -> str | None:
        """
        Process uploaded files and save to target location
        
        Args:
            files: List of uploaded files from Trame
            
        Returns:
            Path to processed file if successful, None otherwise
        """
        if not files or len(files) == 0:
            print(">>> FILE_SERVICE: No files selected for upload")
            return None
        
        if len(files) > 1:
            print(">>> FILE_SERVICE: Multiple files detected, processing only the first one")
        
        # Process only the first file
        file = files[0]
        file_helper = ClientFile(file)
        print(f">>> FILE_SERVICE: Uploading file: {file_helper.info}")

        # Get filename - file_helper.info might be a string or dict
        filename = self._extract_filename(file_helper, file)
        
        # Validate file extension
        if not (filename.lower().endswith(".vtu") or filename.lower().endswith(".stl")):
            print(f">>> FILE_SERVICE: Invalid file format. Expected .vtu or .stl, got: {filename}")
            return None

        # Validate file content
        if not file_helper.content or len(file_helper.content) == 0:
            print(f">>> FILE_SERVICE: Error - Empty file: {filename}")
            return None

        # Save the uploaded file temporarily
        if not file_helper.name:
            print(">>> FILE_SERVICE: Error - No temporary file name available")
            return None

        try:
            with open(file_helper.name, "wb") as f:
                f.write(file_helper.content)
            temp_file_path = file_helper.name
            print(f">>> FILE_SERVICE: File saved temporarily to: {temp_file_path}")
        except IOError as e:
            print(f">>> FILE_SERVICE: Error saving temporary file: {e}")
            return None

        # Determine target file path based on file type
        if filename.lower().endswith(".stl"):
            target_file_path = os.path.join(CURRENT_DIRECTORY, "uploaded.stl")
        else:
            target_file_path = os.path.join(CURRENT_DIRECTORY, "cad_000.vtu")
        try:
            shutil.copy2(temp_file_path, target_file_path)
            print(f">>> FILE_SERVICE: Replaced {target_file_path} with uploaded file")

            # Verify file was written correctly
            if not os.path.exists(target_file_path) or os.path.getsize(target_file_path) == 0:
                print(">>> FILE_SERVICE: Error - Target file not properly written")
                return None

        except (IOError, OSError) as e:
            print(f">>> FILE_SERVICE: Error copying file to target: {e}")
            return None

        # Clean up temporary file
        self._cleanup_temp_file(temp_file_path)
        
        return target_file_path
    
    def _extract_filename(self, file_helper: ClientFile, file) -> str:
        """Extract filename from file helper or file object"""
        filename = ""
        if isinstance(file_helper.info, dict):
            filename = file_helper.info.get("name", "")
        elif isinstance(file_helper.info, str):
            # If info is a string like "File: cad_378.vtu of size 5639377 and type "
            # Extract the filename from the string
            match = re.search(r"File: ([^\s]+)", file_helper.info)
            if match:
                filename = match.group(1)
            else:
                filename = file_helper.info
        else:
            # Try to get name attribute from the file object
            filename = getattr(file, "name", "")
        
        return filename
    
    def _cleanup_temp_file(self, temp_file_path: str):
        """Clean up temporary file"""
        try:
            if temp_file_path:
                os.remove(temp_file_path)
            print(f">>> FILE_SERVICE: Cleaned up temporary file: {temp_file_path}")
        except OSError:
            pass  # Ignore if temp file cleanup fails
    
    def get_current_vtu_file(self) -> str:
        """Get path to current VTU file"""
        return os.path.join(CURRENT_DIRECTORY, "cad_000.vtu")
    
    def get_uploaded_stl_file(self) -> str:
        """Get path to uploaded STL file"""
        return os.path.join(CURRENT_DIRECTORY, "uploaded.stl")
    
    def is_stl_file(self, filename: str) -> bool:
        """Check if filename is an STL file"""
        return filename.lower().endswith(".stl")