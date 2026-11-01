import json, sqlite3, os
from flask import Flask, request, jsonify
from flask_cors import CORS
import engine

app = Flask(__name__); CORS(app)
DB = os.path.join(os.path.dirname(__file__), "moodpalette.db")

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS palettes(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, mood TEXT,
        archetype TEXT, scheme TEXT, traits TEXT, colors TEXT, favourite INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

def row(r): d = dict(r); d["traits"] = json.loads(d["traits"]); d["colors"] = json.loads(d["colors"]); d["favourite"] = bool(d["favourite"]); return d

@app.post("/api/generate")
def generate():
    j = request.json; p = engine.recommend(j["traits"], j["mood"], n=j.get("n", 6))
    with db() as c:
        cur = c.execute("INSERT INTO palettes(name,mood,archetype,scheme,traits,colors) VALUES(?,?,?,?,?,?)",
                        (p["name"], p["mood"], p["archetype"], p["scheme"], json.dumps(p["traits"]), json.dumps(p["colors"])))
        return jsonify(row(c.execute("SELECT * FROM palettes WHERE id=?", (cur.lastrowid,)).fetchone()))

@app.post("/api/replace")
def replace():
    j = request.json
    return jsonify(engine.replace_colour(j["hexes"], j["index"], j["traits"], j["mood"]))

@app.get("/api/palettes")
def list_():
    with db() as c: return jsonify([row(r) for r in c.execute("SELECT * FROM palettes ORDER BY id DESC")])

@app.patch("/api/palettes/<int:i>")
def patch(i):
    j = request.json
    with db() as c:
        if "favourite" in j: c.execute("UPDATE palettes SET favourite=? WHERE id=?", (int(j["favourite"]), i))
        if "colors" in j: c.execute("UPDATE palettes SET colors=? WHERE id=?", (json.dumps(j["colors"]), i))
        return jsonify(row(c.execute("SELECT * FROM palettes WHERE id=?", (i,)).fetchone()))

@app.delete("/api/palettes/<int:i>")
def delete(i):
    with db() as c: c.execute("DELETE FROM palettes WHERE id=?", (i,))
    return "", 204

if __name__ == "__main__": app.run(port=5000, debug=True)
