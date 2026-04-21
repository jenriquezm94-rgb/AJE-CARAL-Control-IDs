from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
import os
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://lfxqqubodfmtxxgvxtkt.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxmeHFxdWJvZGZtdHh4Z3Z4dGt0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjY5ODU2NSwiZXhwIjoyMDkyMjc0NTY1fQ.Pf4rN9aHRvcB81J1-EcB6C_P1pxKFu_ySNAl2l0Lt-0")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def calcular_dias(fecha_emision):
    if not fecha_emision:
        return 0
    try:
        if isinstance(fecha_emision, str):
            fe = datetime.strptime(fecha_emision[:10], "%Y-%m-%d").date()
        else:
            fe = fecha_emision
        return (date.today() - fe).days
    except:
        return 0

@app.route("/")
def index():
    return render_template("index.html")

# ── REGISTROS ──────────────────────────────────────────────────────────────────

@app.route("/api/registros", methods=["GET"])
def get_registros():
    compania = request.args.get("compania", "")
    estado   = request.args.get("estado", "")
    buscar   = request.args.get("buscar", "")

    query = supabase.table("registro").select("*").order("fecha_emision", desc=True)
    if compania:
        query = query.eq("compania", compania)
    if estado:
        query = query.eq("estado_oc", estado)

    res   = query.execute()
    datos = res.data or []

    for r in datos:
        if r.get("estado_oc") not in ("OC CONFIRMADA", "OC RECIBIDA"):
            r["dias_sin_oc"] = calcular_dias(r.get("fecha_emision"))

    if buscar:
        b = buscar.lower()
        datos = [r for r in datos if
                 b in str(r.get("numero_id","")).lower() or
                 b in str(r.get("descripcion","")).lower() or
                 b in str(r.get("codigo_item","")).lower() or
                 b in str(