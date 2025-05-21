from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sqlite3, datetime, os

app = FastAPI()
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"],
    allow_headers=["*"], allow_credentials=True)

UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('''
      CREATE TABLE IF NOT EXISTS projects(
        id INTEGER PRIMARY KEY,
        client_name TEXT,
        moto_info TEXT,
        created_at TEXT,
        photo TEXT
      )
    ''')
    c.execute('''
      CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY,
        project_id INTEGER,
        description TEXT,
        cost INTEGER,
        is_done INTEGER
      )
    ''')
    c.execute('''
      CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY,
        job_id INTEGER,
        amount INTEGER,
        paid_at TEXT
      )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.post("/project")
async def add_project(
    client_name: str = Form(...),
    moto_info: str = Form(...),
    file: UploadFile = File(None)
):
    photo_path = None
    if file:
        ext = file.filename.split('.')[-1]
        fname = f"{datetime.datetime.now().timestamp()}.{ext}"
        path = os.path.join(UPLOAD_DIR, fname)
        with open(path, "wb") as f:
            f.write(await file.read())
        photo_path = "/" + path
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute(
      "INSERT INTO projects(client_name,moto_info,created_at,photo) VALUES(?,?,?,?)",
      (client_name, moto_info, datetime.datetime.now().isoformat(), photo_path)
    )
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return {"id": pid, "client_name": client_name,
            "moto_info": moto_info, "photo": photo_path}

@app.get("/projects")
def get_projects():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    rows = c.execute("SELECT * FROM projects").fetchall()
    conn.close()
    return [
      {"id":r[0], "client_name":r[1], "moto_info":r[2],
       "created_at":r[3], "photo":r[4]}
      for r in rows
    ]

@app.get("/photo/{fname}")
def get_photo(fname: str):
    path = os.path.join(UPLOAD_DIR, fname)
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "not found"}

@app.post("/job")
def add_job(
    project_id: int = Form(...),
    description: str = Form(...),
    cost: int = Form(...)
):
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute(
      "INSERT INTO jobs(project_id,description,cost,is_done) VALUES(?,?,?,0)",
      (project_id, description, cost)
    )
    conn.commit()
    jid = c.lastrowid
    conn.close()
    return {"id": jid}

@app.get("/jobs/{project_id}")
def get_jobs(project_id: int):
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    rows = c.execute(
      "SELECT * FROM jobs WHERE project_id=?", (project_id,)
    ).fetchall()
    conn.close()
    return [
      {"id":r[0], "project_id":r[1],
       "description":r[2], "cost":r[3], "is_done":bool(r[4])}
      for r in rows
    ]

@app.post("/job_done/{job_id}")
def mark_done(job_id: int):
    conn = sqlite3.connect('db.sqlite')
    conn.cursor().execute(
      "UPDATE jobs SET is_done=1 WHERE id=?", (job_id,)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@app.post("/payment")
def add_payment(
    job_id: int = Form(...),
    amount: int = Form(...)
):
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute(
      "INSERT INTO payments(job_id,amount,paid_at) VALUES(?,?,?)",
      (job_id, amount, datetime.datetime.now().isoformat())
    )
    conn.commit()
    payid = c.lastrowid
    conn.close()
    return {"id": payid}

@app.get("/payments/{job_id}")
def get_payments(job_id: int):
    conn = sqlite3.connect('db.sqlite')
    rows = conn.cursor().execute(
      "SELECT * FROM payments WHERE job_id=?", (job_id,)
    ).fetchall()
    conn.close()
    return [{"id":r[0], "job_id":r[1], "amount":r[2], "paid_at":r[3]} for r in rows]
