import os
from pathlib import Path
from pydantic_settings import BaseSettings

CURRENT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = CURRENT_DIR.parent if CURRENT_DIR.name == "dts_agents" else CURRENT_DIR
_api_key = os.environ.get("DEEPTHOUGHT_API_KEY")
if not _api_key:
    raise RuntimeError("DEEPTHOUGHT_API_KEY IS NOT SET")

class Config(BaseSettings):

    deepthought_api_key: str = _api_key
    deepthought_base_url: str = "https://dtcontroller.sr.unh.edu:4242/openai/v1"
    deepthought_model_name: str = "ets:aws:us.anthropic.claude-sonnet-4-6"

    default_temp: float = 0.2
    max_turns: int = 20

    repo_path: Path = (PROJECT_ROOT / "dts_index" / "dpdk" / "dts").resolve()
    vector_store_path: Path = (PROJECT_ROOT / "dts_index" / "chroma_db").resolve()

config = Config()