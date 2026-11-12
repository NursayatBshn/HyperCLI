import os
import shutil
import re
import json

from abstractions.base_task import BaseTask
from utils.decorators import log_execution
from services.result_formatter import ResultFormatter
from services.rule_engine import RuleEngine
from services.storage_services import DATA_ROOT

def file_generator(path, ext=None):
    # Generator for search
    for root, _, files in os.walk(path):
        for file in files:
            if ext:
                if file.endswith(ext):
                    yield os.path.join(root, file)
            else:
                yield os.path.join(root, file)

class SearchTask(BaseTask):
    def __init__(self):
        super().__init__(
            "search",
            "Searches for files by filters",
            usage="search --path <folder> [--ext <extension>]",
            examples=[
                "search --path /home/user/Downloads",
                "search --path /home/user/Downloads --ext .pdf"
            ]
        )

    @log_execution
    def execute(self, args):
        path = "."
        ext = None
        
        path_match = re.search(r'--path\s+([^\s]+)', args)
        ext_match = re.search(r'--ext\s+([^\s]+)', args)
        
        if path_match: path = path_match.group(1)
        if ext_match: ext = ext_match.group(1)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} does not exist.")

        # Search files
        found_files = list(file_generator(path, ext))
        
        if not found_files:
            return "No files found."

        headers = ["NAME", "SIZE", "DATE"]
        rows = []

        for file_path in found_files:
            try:
                file_info = os.stat(file_path)
                name = os.path.basename(file_path)
                
                # File size
                size_mb = f"{file_info.st_size / (1024 * 1024):.2f}MB"
                
                # Last modified date
                from datetime import datetime
                date = datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d')
                
                rows.append([name, size_mb, date])
            except Exception:
                continue # Skip files that cannot be accessed.

        # Use our formatter to create a table.
        return "Search results:\n" + ResultFormatter.format_table(headers, rows)

class OrganizeTask(BaseTask):
    def __init__(self, logger=None):
        super().__init__(
            "organize",
            "Sorts files in the specified folder using configs/rules.json",
            usage="organize --path <folder>",
            examples=["organize --path /home/user/Downloads"]
        )
        self.rule_engine = RuleEngine(os.path.join("configs", "rules.json"))
        self.logger = logger

    @log_execution
    def execute(self, args):
        path_match = re.search(r'--path\s+([^\s]+)', args)
        if not path_match:
            raise ValueError("Specify a folder with --path")
        
        path = path_match.group(1)
        if not os.path.exists(path):
            raise FileNotFoundError("The specified folder does not exist.")

        moved_count = 0
        failed_count = 0

        self._log("INFO", f"Organization started for {path}")

        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)

            if not os.path.isfile(file_path):
                continue

            if not os.path.splitext(file_name)[1]:
                continue

            folder_name = self.rule_engine.get_target_folder(file_name)
            target_dir = os.path.join(path, folder_name)
            target_path = os.path.join(target_dir, file_name)

            try:
                os.makedirs(target_dir, exist_ok=True)
                if os.path.exists(target_path):
                    failed_count += 1
                    self._log("ERROR", f"Could not move {file_name}: target already exists")
                    continue

                shutil.move(file_path, target_path)
                moved_count += 1
                self._log("INFO", f"Moved {file_name} to {folder_name}")
            except Exception as e:
                failed_count += 1
                self._log("ERROR", f"Could not move {file_name}: {e}")

        self._log("INFO", f"Organization finished. Moved {moved_count} files.")

        return f"Organization complete. Files moved: {moved_count}. Failed: {failed_count}."

    def _log(self, level, message):
        if self.logger:
            self.logger.log_event(level, message)

class CleanupTask(BaseTask):
    def __init__(self):
        super().__init__(
            "cleanup",
            "Deletes empty folders in the specified directory",
            usage="cleanup --path <folder>",
            examples=["cleanup --path /home/user/Downloads"]
        )

    @log_execution
    def execute(self, args):
        path_match = re.search(r'--path\s+([^\s]+)', args)
        if not path_match:
            raise ValueError("Specify a directory with --path")
        
        target_dir = path_match.group(1)
        if not os.path.exists(target_dir):
            raise FileNotFoundError("The specified directory does not exist.")

        removed_count = 0
        # Remove empty folders
        for root, dirs, files in os.walk(target_dir, topdown=False):
            for d in dirs:
                dir_path = os.path.join(root, d)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        removed_count += 1
                except Exception:
                    pass

        return f"Cleanup complete. Empty folders removed: {removed_count}."

class HelpTask(BaseTask):
    def __init__(self, tasks_dict):
        super().__init__(
            "help",
            "Shows the command list or details for one command",
            usage="help [command]",
            examples=["help", "help logs", "help organize"]
        )
        self.tasks_dict = tasks_dict

    def execute(self, args):
        args = args.strip().lower()
        if args in self.tasks_dict:
            task = self.tasks_dict[args]
            lines = [
                f"Help for command '{task.name}':",
                f"  Description: {task.description}"
            ]
            if task.usage:
                lines.append(f"  Usage: {task.usage}")
            if task.examples:
                lines.append("  Examples:")
                for example in task.examples:
                    lines.append(f"    {example}")
            return "\n".join(lines)
        elif args:
            raise ValueError(f"Command '{args}' not found. Enter 'help' for the command list.")

        lines = ["Available commands:"]
        for name, task in self.tasks_dict.items():
            lines.append(f"  {name} - {task.description}")
        return "\n".join(lines)

class HistoryTask(BaseTask):
    def __init__(self):
        self.display_limit = 100
        super().__init__(
            "history",
            f"Shows up to the last {self.display_limit} executed commands",
            usage="history",
            examples=["history"]
        )
        self.history_file = os.path.join(DATA_ROOT, "history.json")

    def execute(self, args):
        if not os.path.exists(self.history_file):
            return "History is empty."

        with open(self.history_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                raise ValueError("Error reading history (file is corrupted).")

        if not data:
            return "History is empty."

        recent_data = data[-self.display_limit:]
        headers = ["Time", "Command", "Status"]
        rows = [[item.get('timestamp', '-'), item.get('command', '-'), item.get('status', '-')] for item in recent_data]

        return "Recent actions:\n" + ResultFormatter.format_table(headers, rows)

class LogsTask(BaseTask):
    def __init__(self):
        self.page_size = 10
        super().__init__(
            "logs",
            f"Shows system logs, {self.page_size} entries per page",
            usage="logs [--page <number>]",
            examples=[
                "logs",
                "logs --page 2"
            ]
        )
        self.logs_file = os.path.join(DATA_ROOT, "logs.json")

    def execute(self, args):
        args = args.strip()
        if not os.path.exists(self.logs_file):
            return "Logs are empty."

        data = self._load_logs()
        if not data:
            return "Logs are empty."

        page = self._parse_page(args)
        return self._format_page(data, page)

    def _load_logs(self):
        with open(self.logs_file, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                raise ValueError("Error reading logs.")

    def _parse_page(self, args):
        page_match = re.search(r'--page\s+(\d+)', args)
        if not page_match:
            return 1

        return max(1, int(page_match.group(1)))

    def _format_page(self, data, page):
        total_pages = max(1, (len(data) + self.page_size - 1) // self.page_size)
        page = min(page, total_pages)
        newest_first = list(reversed(data))
        start = (page - 1) * self.page_size
        end = start + self.page_size
        page_data = newest_first[start:end]

        headers = ["Time", "Level", "Message"]
        rows = [
            [
                item.get('timestamp', '-'),
                item.get('level', '-'),
                item.get('message', '-')
            ]
            for item in page_data
        ]

        return (
            f"Logs (page {page}/{total_pages}):\n"
            + ResultFormatter.format_table(headers, rows)
        )
