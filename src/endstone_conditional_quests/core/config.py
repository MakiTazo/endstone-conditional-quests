import os
from ruamel.yaml import YAML

class Config:
    def __init__(self, data_folder: str):
        self.data_folder = data_folder
        self.config_path = os.path.join(data_folder, "config.yml")
        self.db_type = "sqlite"
        self.mysql_host = "localhost"
        self.mysql_port = 3306
        self.mysql_database = "quests"
        self.mysql_user = "root"
        self.mysql_password = ""
        self._load()

    def _load(self):
        yaml = YAML()
        if not os.path.exists(self.config_path):
            self._create_default(yaml)

        with open(self.config_path, "r") as f:
            data = yaml.load(f)
            self.db_type = data.get("database", {}).get("type", "sqlite")
            mysql = data.get("mysql", {})
            self.mysql_host = mysql.get("host", "localhost")
            self.mysql_port = mysql.get("port", 3306)
            self.mysql_database = mysql.get("database", "quests")
            self.mysql_user = mysql.get("user", "root")
            self.mysql_password = mysql.get("password", "")

    def _create_default(self, yaml):
        os.makedirs(self.data_folder, exist_ok=True)
        default = {
            "database": {"type": "sqlite"},
            "mysql": {
                "host": "localhost",
                "port": 3306,
                "database": "quests",
                "user": "root",
                "password": ""
            }
        }
        with open(self.config_path, "w") as f:
            yaml.dump(default, f)
