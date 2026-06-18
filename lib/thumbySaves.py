import pygame
import base64
import json
import os

class SavesClass:
    def __init__(self):
        os.makedirs("Saves/temp", exist_ok=True)

        self.savesPath = "Saves"
        self.saveFile = None
        self.volatileDict = {}

        self.setName("temp")

    def setName(self, subdir):
        self.savesPath = os.path.join("Saves", subdir)

        os.makedirs(self.savesPath, exist_ok=True)

        if self.saveFile is not None:
            self.saveFile.close()

        persistent = os.path.join(self.savesPath, "persistent.json")
        backup = os.path.join(self.savesPath, "backup.json")

        try:
            with open(persistent, "r") as f:
                self.volatileDict = json.load(f)

        except (OSError, json.JSONDecodeError):
            try:
                with open(backup, "r") as f:
                    self.volatileDict = json.load(f)

                self.save(False)

            except (OSError, json.JSONDecodeError):
                self.volatileDict = {}

                with open(persistent, "w") as f:
                    json.dump({}, f)

        self.saveFile = open(persistent, "r+")

    def setItem(self, key, value):
        if key.startswith("__b"):
            raise ValueError(
                'Save data key cannot be prefixed with "__b"'
            )

        if isinstance(value, (bytes, bytearray)):
            self.volatileDict.pop(key, None)

            self.volatileDict["__b" + key] = (
                base64.b64encode(value).decode("ascii")
            )

        else:
            self.volatileDict.pop("__b" + key, None)
            self.volatileDict[key] = value

    def getItem(self, key):
        ret = self.volatileDict.get(key)

        if ret is None:
            ret = self.volatileDict.get("__b" + key)

            if ret is None:
                return None

            return base64.b64decode(ret)

        return ret

    def delItem(self, key):
        ret = self.volatileDict.pop(key, None)

        if ret is None:
            ret = self.volatileDict.pop("__b" + key, None)

            if ret is None:
                return None

            return base64.b64decode(ret)

        return ret

    def hasItem(self, key):
        return (
            key in self.volatileDict
            or "__b" + key in self.volatileDict
        )

    def save(self, backup=False):
        if self.savesPath == "Saves":
            self.savesPath = os.path.join("Saves", "temp")

        persistent = os.path.join(
            self.savesPath,
            "persistent.json"
        )

        backup_file = os.path.join(
            self.savesPath,
            "backup.json"
        )

        if self.saveFile is not None:
            self.saveFile.close()

        try:
            if backup:
                if os.path.exists(persistent):
                    os.replace(persistent, backup_file)
            else:
                if os.path.exists(persistent):
                    os.remove(persistent)

        except OSError:
            pass

        with open(persistent, "w") as f:
            json.dump(self.volatileDict, f)

        self.saveFile = open(persistent, "r+")

    def getName(self):
        return self.savesPath


saveData = SavesClass()