"""
File manipulation tools
"""

import os
from typing import Optional
from mangaba.tools.base import BaseTool


class FileReaderTool(BaseTool):
    """Tool for reading text files.

    Example:
        tool = FileReaderTool()
        content = tool.run("document.txt")
    """

    name = "file_reader"
    description = "Read text files and return their contents"

    def _run(self, file_path: str, encoding: str = "utf-8") -> str:
        """Read the content of a file.

        Args:
            file_path: Path to the file.
            encoding: File encoding (default: utf-8).

        Returns:
            The content of the file.
        """
        try:
            if not os.path.exists(file_path):
                return f"Error: File '{file_path}' not found"

            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()

            return content

        except Exception as e:
            return f"Error reading file: {str(e)}"


class FileWriterTool(BaseTool):
    """Tool for writing to files.

    Example:
        tool = FileWriterTool()
        tool.run("output.txt", "Content to write")
    """

    name = "file_writer"
    description = "Write content to text files"

    def _run(
        self, file_path: str, content: str, mode: str = "w", encoding: str = "utf-8"
    ) -> str:
        """Write content to a file.

        Args:
            file_path: Path to the file.
            content: Content to write.
            mode: Write mode ('w' for write or 'a' for append).
            encoding: File encoding (default: utf-8).

        Returns:
            Success message or error message.
        """
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)

            return f"Successfully wrote to '{file_path}'"

        except Exception as e:
            return f"Error writing file: {str(e)}"


class DirectoryListTool(BaseTool):
    """Tool for listing directory contents.

    Example:
        tool = DirectoryListTool()
        files = tool.run("./documents")
    """

    name = "directory_list"
    description = "List files and directories in a given path"

    def _run(self, directory_path: str, pattern: Optional[str] = None) -> str:
        """List the contents of a directory.

        Args:
            directory_path: Path to the directory.
            pattern: Filter pattern (e.g., "*.txt").

        Returns:
            Formatted list of files and folders.
        """
        try:
            if not os.path.exists(directory_path):
                return f"Error: Directory '{directory_path}' not found"

            if not os.path.isdir(directory_path):
                return f"Error: '{directory_path}' is not a directory"

            items = os.listdir(directory_path)

            # Apply filter if specified
            if pattern:
                import fnmatch

                items = [item for item in items if fnmatch.fnmatch(item, pattern)]

            if not items:
                return "Directory is empty or no files match the pattern"

            # Separate files and directories
            files = []
            directories = []

            for item in sorted(items):
                full_path = os.path.join(directory_path, item)
                if os.path.isdir(full_path):
                    directories.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(full_path)
                    files.append(f"📄 {item} ({size} bytes)")

            result = []
            if directories:
                result.append("Directories:")
                result.extend(directories)
            if files:
                result.append("\nFiles:")
                result.extend(files)

            return "\n".join(result)

        except Exception as e:
            return f"Error listing directory: {str(e)}"
