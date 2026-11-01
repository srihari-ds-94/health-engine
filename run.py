import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"==================================================")
    print(f"🚀 HealthEngine Server Starting")
    print(f"📱 Web Application: http://localhost:{port}")
    print(f"📖 Interactive API Docs: http://localhost:{port}/docs")
    print(f"💾 Database: SQLite (healthengine.db)")
    print(f"==================================================")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
