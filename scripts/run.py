"""One-command local launcher for the FastAPI service and Streamlit dashboard."""
from __future__ import annotations
import os, signal, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main() -> int:
    api_port=os.getenv("FINRISK_API_PORT","8000")
    app_port=os.getenv("FINRISK_APP_PORT","8501")
    env=os.environ.copy()
    env.setdefault("FINRISK_IMPACT_THRESHOLD","7")
    env.setdefault("FINRISK_DB_PATH",str(ROOT/"data"/"finrisk_events.sqlite3"))
    cmds=[
        ([sys.executable,"-m","uvicorn","api:app","--host","127.0.0.1","--port",api_port],"api"),
        ([sys.executable,"-m","streamlit","run","app.py","--server.port",app_port,"--server.address","127.0.0.1","--server.headless","true"],"dashboard"),
    ]
    procs=[]
    try:
        for cmd,name in cmds:
            print(f"Starting {name}: {' '.join(cmd)}",flush=True)
            procs.append(subprocess.Popen(cmd,cwd=ROOT,env=env))
            time.sleep(0.5)
        print("\nFinRisk services started. Stop both with Ctrl+C.",flush=True)
        print(f"Dashboard: http://127.0.0.1:{app_port}",flush=True)
        print(f"API docs:  http://127.0.0.1:{api_port}/docs",flush=True)
        while True:
            for p in procs:
                code=p.poll()
                if code is not None:
                    print(f"A service exited with code {code}; stopping remaining services.",flush=True)
                    return code
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping FinRisk services...",flush=True)
        return 0
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: p.kill()
    return 0

if __name__=="__main__":
    raise SystemExit(main())
