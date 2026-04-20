from flask import Flask, render_template, request, jsonify
from supabase import create_client
import os
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://lfxqqubodfmtxxgvxtkt.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxmeHFxdWJvZGZtdHh4Z3Z4dGt0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjY5ODU2NSwiZXhwIjoyMDkyMjc0NTY1fQ.Pf4rN9aHRvcB81J1-EcB6C_P1pxKFu_ySNAl2l0Lt-0")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def calcular_dias(fecha):
    if not fecha:
        return 0
    try:
        fe = datetime.strptime(str(fecha)[:10], "%Y-%m-%d").date()
        return (date.today() - fe).days
    except:
        return 0

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/registros", methods=["GET"])
def get_registros():
    compania = request.args.get("compania", "")
    estado   = request.args.get("estado", "")
    buscar   = request.args.get("buscar", "")
    query = supabase.table("registro").select("*").order("fecha_emision", desc=True)
    if estado:
        query = query.eq("estado_oc", estado)
    datos = query.execute().data or []
    for r in datos:
        if r.get("estado_oc") not in ("OC CONFIRMADA", "OC RECIBIDA"):
            r["dias_sin_oc"] = calcular_dias(r.get("fecha_emision"))
    if compania:
        c = compania.lower()
        datos = [r for r in datos if c in str(r.get("tipo_compra","")).lower()]
    if buscar:
        b = buscar.lower()
        datos = [r for r in datos if
                 b in str(r.get("id_compra","")).lower() or
                 b in str(r.get("desc_id","")).lower() or
                 b in str(r.get("desc_proveedor","")).lower() or
                 b in str(r.get("tipo_compra","")).lower()]
    return jsonify(datos)

@app.route("/api/registros", methods=["POST"])
def crear_registro():
    body = request.json
    body["fecha_emision"] = body.get("fecha_emision") or date.today().isoformat()
    body["estado_oc"]     = body.get("estado_oc") or "SIN OC"
    body["dias_sin_oc"]   = 0
    body["created_at"]    = datetime.now().isoformat()
    res = supabase.table("registro").insert(body).execute()
    return jsonify(res.data[0] if res.data else {}), 201

@app.route("/api/registros/<int:id>", methods=["PUT"])
def actualizar_registro(id):
    body = request.json
    if body.get("estado_oc") in ("OC CONFIRMADA", "OC RECIBIDA"):
        body["dias_sin_oc"] = 0
    res = supabase.table("registro").update(body).eq("id_registro", id).execute()
    return jsonify(res.data[0] if res.data else {})

@app.route("/api/registros/<int:id>", methods=["DELETE"])
def eliminar_registro(id):
    supabase.table("registro").delete().eq("id_registro", id).execute()
    return jsonify({"ok": True})

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    datos = supabase.table("registro").select("*").execute().data or []
    hoy   = date.today()
    mes_actual = hoy.strftime("%Y-%m")
    total_mes  = sum(1 for r in datos if str(r.get("fecha_emision",""))[:7] == mes_actual)
    pendientes = [r for r in datos if r.get("estado_oc") in ("SIN OC", "PENDIENTE", None)]
    for r in pendientes:
        r["dias_sin_oc"] = calcular_dias(r.get("fecha_emision"))
    vencidos    = sum(1 for r in pendientes if r["dias_sin_oc"] > 4)
    en_limite   = sum(1 for r in pendientes if r["dias_sin_oc"] == 4)
    en_proceso  = sum(1 for r in datos if r.get("estado_oc") == "OC EN PROCESO")
    confirmadas = sum(1 for r in datos if r.get("estado_oc") in ("OC CONFIRMADA", "OC RECIBIDA"))
    alertas     = sorted([r for r in pendientes if r["dias_sin_oc"] >= 4], key=lambda x: x["dias_sin_oc"], reverse=True)
    return jsonify({
        "total_mes":   total_mes,
        "total":       len(datos),
        "vencidos":    vencidos,
        "en_limite":   en_limite,
        "en_proceso":  en_proceso,
        "confirmadas": confirmadas,
        "alertas":     alertas
    })
@app.route("/api/materiales/<id_compra>", methods=["GET"])
def get_materiales(id_compra):
    res = supabase.table("material").select("*").eq("id_compra", id_compra).execute()
    return jsonify(res.data or [])
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
