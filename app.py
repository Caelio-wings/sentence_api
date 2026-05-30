"""启动入口 — python app.py"""

import config
import uvicorn
from main import app

if __name__ == "__main__":
    srv = config.get_server_config()
    uvicorn.run(
        "main:app",
        host=srv["host"],
        port=srv["port"],
    )
