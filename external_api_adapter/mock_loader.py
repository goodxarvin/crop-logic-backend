import json
from dataclasses import dataclass
from pathlib import Path

from .exceptions import MockDirectoryNotFound, MockFileNotFound


@dataclass
class LoadedMockResponse:
    data: object
    status_code: int
    file_path: str


class MockLoader:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path or Path(__file__).resolve().parent / "json")

    def load(self, service_name, path, method):
        mock_files = self._find_mock_files(service_name=service_name, path=path, method=method)
        if not mock_files:
            raise MockFileNotFound(
                f"No mock file found for service='{service_name}' path='{path}' method='{method}'."
            )

        selected_file = sorted(mock_files, key=self._mock_file_priority)[0]
        with selected_file.open("r", encoding="utf-8") as file:
            return LoadedMockResponse(
                data=json.load(file),
                status_code=self._extract_status_code(selected_file),
                file_path=str(selected_file),
            )

    def _find_mock_files(self, service_name, path, method):
        service_root = self.base_path / service_name
        directory_path = service_root / self._build_directory_path(path)
        pattern = f"{method.lower()}_*.json"

        if directory_path.exists() and directory_path.is_dir():
            return list(directory_path.glob(pattern))

        leaf_name = self._extract_leaf_name(path)
        parent_directory = directory_path.parent
        if parent_directory.exists() and parent_directory.is_dir():
            flat_pattern = f"{leaf_name}-{method.lower()}_*.json"
            flat_files = list(parent_directory.glob(flat_pattern))
            if flat_files:
                return flat_files

        raise MockDirectoryNotFound(
            f"Mock directory not found for service='{service_name}' path='{path}': {directory_path}"
        )

    @staticmethod
    def _build_directory_path(path):
        normalized = str(path).strip().strip("/")
        if not normalized:
            return Path(".")
        return Path(*normalized.split("/"))

    @staticmethod
    def _extract_status_code(file_path):
        parts = file_path.stem.split("_")
        if len(parts) < 2:
            return 200
        try:
            return int(parts[1])
        except ValueError:
            return 200

    @staticmethod
    def _extract_leaf_name(path):
        normalized = str(path).strip().strip("/")
        if not normalized:
            return ""
        return normalized.split("/")[-1]

    @staticmethod
    def _mock_file_priority(file_path):
        stem = file_path.stem.lower()
        status_code = MockLoader._extract_status_code(file_path)
        keyword_rank = 2
        if "success" in stem:
            keyword_rank = 0
        elif "stream" in stem:
            keyword_rank = 0
        elif "pending" in stem or "progress" in stem:
            keyword_rank = 1
        return (status_code >= 400, keyword_rank, stem)
