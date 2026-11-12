import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from abstractions.base_task import BaseTask
from services.rule_engine import RuleEngine
from services.storage_services import HistoryService
from tasks.core_tasks import OrganizeTask, file_generator


def test_file_generator():
    with tempfile.TemporaryDirectory() as folder:
        open(os.path.join(folder, "report.txt"), "w").close()
        open(os.path.join(folder, "photo.png"), "w").close()

        files = list(file_generator(folder, ext=".txt"))

        assert len(files) == 1
        assert files[0].endswith("report.txt")


def test_rule_engine_categories():
    rules = RuleEngine("configs/rules.json")

    assert rules.get_target_folder("photo.jpeg") == "Images"
    assert rules.get_target_folder("report.docx") == "Documents"
    assert rules.get_target_folder("backup.zip") == "Archives"


def test_base_task_inheritance():
    task = OrganizeTask()

    assert isinstance(task, BaseTask)
    assert task.name == "organize"


def test_organize_task_moves_files():
    with tempfile.TemporaryDirectory() as folder:
        open(os.path.join(folder, "photo.jpg"), "w").close()
        open(os.path.join(folder, "report.pdf"), "w").close()

        task = OrganizeTask()
        task.execute(f"--path {folder}")

        assert os.path.exists(os.path.join(folder, "Images", "photo.jpg"))
        assert os.path.exists(os.path.join(folder, "Documents", "report.pdf"))


def test_history_service_limit():
    with tempfile.TemporaryDirectory() as folder:
        history_file = os.path.join(folder, "history.json")
        history = HistoryService(history_file)

        for i in range(105):
            history.log_command(f"command-{i}", "SUCCESS", "ok")

        entries = history.read_all()

        assert len(entries) == 100
        assert entries[0]["command"] == "command-5"
        assert entries[-1]["command"] == "command-104"


if __name__ == "__main__":
    test_file_generator()
    test_rule_engine_categories()
    test_base_task_inheritance()
    test_organize_task_moves_files()
    test_history_service_limit()
    print("All basic tests passed successfully!")
