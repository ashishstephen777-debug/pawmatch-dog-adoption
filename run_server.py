from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    uvicorn.run("dogmatch.api:app", host="0.0.0.0", port=5000, reload=True)

