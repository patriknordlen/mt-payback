import json
from json.decoder import JSONDecodeError
from lockfile import locked


class JsonStore:
    @locked("jsonstore.lock")
    def __init__(self, filename):
        self.filename = filename

        try:
            with open(self.filename, "r") as f:
                json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            with open(self.filename, "w") as f:
                json.dump({}, f)

    @locked("jsonstore.lock")
    def set(self, key, value):
        with open(self.filename, "r") as f:
            store = json.load(f)
            store[key] = value
        with open(self.filename, "w") as f:
            json.dump(store, f)

    @locked("jsonstore.lock")
    def set_all(self, input_dict):
        with open(self.filename, "r") as f:
            store = json.load(f)
            updated_store = store | input_dict
        with open(self.filename, "w") as f:
            json.dump(updated_store, f)

    @locked("jsonstore.lock")
    def unset(self, key):
        with open(self.filename, "r") as f:
            store = json.load(f)
            store.pop(key, None)
        with open(self.filename, "w") as f:
            json.dump(store, f)

    @locked("jsonstore.lock")
    def get(self, key):
        try:
            with open(self.filename, "r") as f:
                store = json.load(f)
                return store.get(key)
        except FileNotFoundError:
            return None

    @locked("jsonstore.lock")
    def get_all(self):
        try:
            with open(self.filename, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
