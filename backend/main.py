from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime

from db import init_db, get_conn
from models import RegisterIn, LoginIn, TargetIn
from auth import hash_password, verify_password, create_token, decode_token
from crawler import normalize_url, crawl
from scanner import scan_headers, scan_cors, scan_sensitive, client_report
from ai_advisor import ask_ai



app = FastAPI(title="W3Secure PRO (No React)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def start():
    init_db()

def require_user(authorization: str | None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        token = authorization.replace("Bearer ", "")
        return decode_token(token)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
def home():
    return {"message": "W3Secure PRO Backend Running ✅"}

@app.post("/auth/register")
def register(data: RegisterIn):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
            (data.username, hash_password(data.password), data.role)
        )
        conn.commit()
    except:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()
    return {"message": "User created"}

@app.post("/auth/login")
def login(data: LoginIn):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, role FROM users WHERE username=?", (data.username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    uid, username, pw_hash, role = row
    if not verify_password(data.password, pw_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"token": create_token(uid, username, role)}

@app.post("/targets")
def add_target(target: TargetIn, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    base_url = normalize_url(target.base_url)

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO targets(name, base_url, created_by) VALUES(?,?,?)",
            (target.name, base_url, user["uid"])
        )
        conn.commit()
    except:
        raise HTTPException(status_code=400, detail="Target already exists")
    finally:
        conn.close()

    return {"message": "Target added"}

@app.get("/targets")
def list_targets(authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, base_url FROM targets WHERE created_by=?", (user["uid"],))
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "base_url": r[2]} for r in rows]

@app.post("/scans/{target_id}")
def start_scan(target_id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, base_url FROM targets WHERE id=? AND created_by=?", (target_id, user["uid"]))
    t = cur.fetchone()
    if not t:
        conn.close()
        raise HTTPException(status_code=404, detail="Target not found")
    _, url = t

    surface = crawl(url, max_pages=25)
    headers = scan_headers(url)
    cors = scan_cors(url)
    sensitive = scan_sensitive(url)
    client = client_report(headers, cors, sensitive)

    result = {
        "target": url,
        "attack_surface": surface,
        "checks": {"headers": headers, "cors": cors, "sensitive": sensitive},
        "client_report": client
    }

    cur.execute(
        "INSERT INTO scans(target_id,status,created_at,result_json) VALUES(?,?,?,?)",
        (target_id, "completed", datetime.now().isoformat(), json.dumps(result))
    )
    conn.commit()
    scan_id = cur.lastrowid
    conn.close()

    return {"message": "Scan completed", "scan_id": scan_id, "result": result}

@app.get("/scans")
def scan_history(authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT scans.id, targets.base_url, scans.created_at, scans.status
        FROM scans
        JOIN targets ON targets.id = scans.target_id
        WHERE targets.created_by=?
        ORDER BY scans.id DESC
        LIMIT 20
    """, (user["uid"],))
    rows = cur.fetchall()
    conn.close()
    return [{"scan_id": r[0], "target": r[1], "created_at": r[2], "status": r[3]} for r in rows]

@app.get("/scans/{scan_id}")
def scan_detail(scan_id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT scans.result_json
        FROM scans
        JOIN targets ON targets.id = scans.target_id
        WHERE scans.id=? AND targets.created_by=?
    """, (scan_id, user["uid"]))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    return json.loads(row[0])

@app.get("/ai")
def ai_help(title: str, evidence: str, authorization: str | None = Header(default=None)):
    require_user(authorization)
    return {"ai": ask_ai(title, evidence)}
@app.put("/targets/{target_id}")
def update_target(target_id: int, target: TargetIn, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    base_url = normalize_url(target.base_url)

    conn = get_conn()
    cur = conn.cursor()

    # check ownership
    cur.execute("SELECT id FROM targets WHERE id=? AND created_by=?", (target_id, user["uid"]))
    t = cur.fetchone()
    if not t:
        conn.close()
        raise HTTPException(status_code=404, detail="Target not found")

    try:
        cur.execute(
            "UPDATE targets SET name=?, base_url=? WHERE id=?",
            (target.name, base_url, target_id)
        )
        conn.commit()
    except:
        conn.close()
        raise HTTPException(status_code=400, detail="Target URL already exists")

    conn.close()
    return {"message": "Target updated ✅"}

@app.delete("/targets/{target_id}")
def delete_target(target_id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM targets WHERE id=? AND created_by=?", (target_id, user["uid"]))
    t = cur.fetchone()
    if not t:
        conn.close()
        raise HTTPException(status_code=404, detail="Target not found")

    cur.execute("DELETE FROM scans WHERE target_id=?", (target_id,))
    cur.execute("DELETE FROM targets WHERE id=?", (target_id,))
    conn.commit()
    conn.close()

    return {"message": "Target deleted ✅"}
