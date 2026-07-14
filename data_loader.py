import json
from pathlib import Path

class DataManager:
def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parent
        # Strictly separated memory structures
        self.homebrew = {}
        self.srd = {}

    def _load_json_files(self, directory: Path, target_namespace: dict):
        if not directory.exists() or not directory.is_dir():
            print(f"Directory {directory} does not exist. Skipping.")
            return

        for file_path in directory.glob('*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Preserve the original JSON structure natively inside dictionaries
                    # We key it by the filename without extension to keep it organized
                    file_key = file_path.stem
                    target_namespace[file_key] = data
            except json.JSONDecodeError:
                print(f"Error decoding JSON in {file_path}")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    def load_all_data(self):
        # 1. Ingest Homebrew
        avrae_dir = self.base_dir / "data" / "avrae"
        handbooks_dir = self.base_dir / "data" / "handbooks"

        self._load_json_files(avrae_dir, self.homebrew)
        self._load_json_files(handbooks_dir, self.homebrew)

        # 2. Ingest SRD
        srd_dir = self.base_dir / "data" / "srd"
        self._load_json_files(srd_dir, self.srd)

    def _search_namespace(self, query: str, namespace: dict):
        """
        Deep search across a given namespace.
        Looks for the `name` key or `title` key.
        Returns a list of matching item dictionaries.
        """
        query_lower = query.lower()
        results = []

        # Recursively search for objects that have a "name" matching the query
        def recursive_search(data):
            if isinstance(data, dict):
                # If this dictionary represents an entity with a name
                name = data.get("name") or data.get("title")
                if name and isinstance(name, str) and query_lower in name.lower():
                    # To avoid returning massive root dictionaries, we ensure it's a specific entry
                    # Usually, entries have at least 'name' and some other attributes.
                    # We'll just add the matching dict.
                    if "_meta" not in data: # Prevent matching meta blocks if they happen to have a name
                        results.append(data)

                # Continue searching deeply
                for key, value in data.items():
                    # Skip meta fields generally to avoid false positives
                    if key == "_meta":
                        continue
                    recursive_search(value)
            elif isinstance(data, list):
                for item in data:
                    recursive_search(item)

        recursive_search(namespace)

        # Simple deduplication by identity or name (using name for simplicity)
        unique_results = []
        seen_names = set()
        for r in results:
            n = r.get("name") or r.get("title")
            if n not in seen_names:
                seen_names.add(n)
                unique_results.append(r)

        return unique_results

    def search_homebrew(self, query: str):
        return self._search_namespace(query, self.homebrew)

    def search_srd(self, query: str):
        return self._search_namespace(query, self.srd)
