import json
from pathlib import Path

app_dir = Path(__file__).parent
config_file_path = app_dir / "config.json"

with open(config_file_path, "rt") as json_file:
    config_data = json.load(json_file)


class Config:
    pass


# apply base config from json file
for k, v in config_data.items():
    setattr(Config, k, v)
