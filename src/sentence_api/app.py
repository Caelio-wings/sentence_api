"""启动入口 — python -m sentence_api.app"""

from sentence_api import config
import uvicorn
from sentence_api.main import app

if __name__ == "__main__":
    srv = config.get_server_config()
    uvicorn.run(
        "sentence_api.main:app",
        host=srv["host"],
        port=srv["port"],
    )
