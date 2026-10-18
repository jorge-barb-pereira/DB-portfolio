import os
import json
import psycopg2
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5555")
DB_NAME = os.getenv("DB_NAME", "autarquicas2021")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.environ["DB_PASS"]


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/territories")
def territories():
    orgao = request.args.get("orgao", "CM")
    tipo = "Freguesia" if orgao == "AF" else "Município"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT codigo, nome
        FROM eleicoes.territorios
        WHERE tipo = %s
          AND geom IS NOT NULL
        ORDER BY nome;
    """, (tipo,))

    rows = [{"codigo": r[0], "nome": r[1]} for r in cur.fetchall()]

    cur.close()
    conn.close()

    return jsonify(rows)


@app.route("/api/map")
def map_data():
    orgao = request.args.get("orgao", "CM")
    tipo = "Freguesia" if orgao == "AF" else "Município"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        WITH winners AS (
            SELECT DISTINCT ON (r.territorio_codigo)
                r.territorio_codigo,
                r.partido_sigla,
                r.votos
            FROM eleicoes.resultados_partidos r
            WHERE r.orgao = %s
            ORDER BY r.territorio_codigo, r.votos DESC
        )
        SELECT
            t.codigo,
            t.nome,
            w.partido_sigla,
            ST_AsGeoJSON(
                ST_Transform(
                    ST_Simplify(t.geom, CASE WHEN %s = 'Freguesia' THEN 50 ELSE 100 END),
                    4326
                )
            )
        FROM eleicoes.territorios t
        LEFT JOIN winners w
            ON w.territorio_codigo = t.codigo
        WHERE t.tipo = %s
          AND t.geom IS NOT NULL;
    """, (orgao, tipo, tipo))

    features = []

    for codigo, nome, partido, geom in cur.fetchall():
        features.append({
            "type": "Feature",
            "properties": {
                "codigo": codigo,
                "nome": nome,
                "winner": partido
            },
            "geometry": json.loads(geom)
        })

    cur.close()
    conn.close()

    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })


@app.route("/api/results")
def results():
    codigo = request.args.get("codigo")
    orgao = request.args.get("orgao", "CM")

    conn = get_conn()
    cur = conn.cursor()

    if not codigo:
        cur.execute("""
            SELECT
                SUM(inscritos) AS inscritos,
                SUM(votantes) AS votantes,
                SUM(votos_brancos) AS brancos,
                SUM(votos_nulos) AS nulos
            FROM eleicoes.estatisticas_globais
            WHERE orgao = %s;
        """, (orgao,))

        stats = cur.fetchone()

        territory_type = "Freguesia" if orgao == "AF" else "Município"

        cur.execute("""
            SELECT COUNT(*)
            FROM eleicoes.territorios
            WHERE tipo = %s
              AND geom IS NOT NULL;
        """, (territory_type,))

        total_territories = cur.fetchone()[0]

        cur.execute("""
            SELECT SUM(votos)
            FROM eleicoes.resultados_partidos
            WHERE orgao = %s;
        """, (orgao,))

        total_valid_votes = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT
                partido_sigla,
                SUM(votos) AS votos,
                SUM(mandatos) AS mandatos,
                ROUND(
                    100.0 * SUM(votos) / NULLIF(SUM(SUM(votos)) OVER (), 0),
                    2
                ) AS vote_share
            FROM eleicoes.resultados_partidos
            WHERE orgao = %s
            GROUP BY partido_sigla
            ORDER BY votos DESC
            LIMIT 15;
        """, (orgao,))

        overall_results = [
            {
                "partido": r[0],
                "votos": r[1],
                "mandatos": r[2],
                "vote_share": float(r[3]) if r[3] is not None else 0
            }
            for r in cur.fetchall()
        ]

        cur.close()
        conn.close()

        inscritos = stats[0] or 0
        votantes = stats[1] or 0
        brancos = stats[2] or 0
        nulos = stats[3] or 0

        return jsonify({
            "overall": True,
            "territory": {
                "codigo": "",
                "nome": "All Parishes" if orgao == "AF" else "All Municipalities",
                "orgao": orgao
            },
            "summary": {
                "winner": "Overall",
                "winner_votes": 0,
                "total_votes": total_valid_votes,
                "total_municipalities": total_territories
            },
            "results": overall_results,
            "stats": {
                "inscritos": inscritos,
                "votantes": votantes,
                "brancos": brancos,
                "nulos": nulos,
                "validos": total_valid_votes,
                "abstencao": round(100 - (100 * votantes / inscritos), 2) if inscritos else 0
            }
        })

    cur.execute("""
        SELECT nome
        FROM eleicoes.territorios
        WHERE codigo = %s;
    """, (codigo,))

    territory = cur.fetchone()
    territory_name = territory[0] if territory else codigo

    cur.execute("""
        SELECT
            r.partido_sigla,
            r.votos,
            r.mandatos,
            ROUND(100.0 * r.votos / NULLIF(SUM(r.votos) OVER (), 0), 2) AS vote_share
        FROM eleicoes.resultados_partidos r
        WHERE r.territorio_codigo = %s
          AND r.orgao = %s
        ORDER BY r.votos DESC;
    """, (codigo, orgao))

    results_rows = [
        {
            "partido": r[0],
            "votos": r[1],
            "mandatos": r[2],
            "vote_share": float(r[3]) if r[3] is not None else 0
        }
        for r in cur.fetchall()
    ]

    cur.execute("""
        SELECT inscritos, votantes, votos_brancos, votos_nulos
        FROM eleicoes.estatisticas_globais
        WHERE territorio_codigo = %s
          AND orgao = %s;
    """, (codigo, orgao))

    stats = cur.fetchone()

    total_votes = sum(r["votos"] for r in results_rows)
    winner = results_rows[0]["partido"] if results_rows else "N/A"
    winner_votes = results_rows[0]["votos"] if results_rows else 0

    cur.close()
    conn.close()

    return jsonify({
        "overall": False,
        "territory": {
            "codigo": codigo,
            "nome": territory_name,
            "orgao": orgao
        },
        "summary": {
            "winner": winner,
            "winner_votes": winner_votes,
            "total_votes": total_votes,
            "total_municipalities": None
        },
        "results": results_rows,
        "stats": {
            "inscritos": stats[0] if stats else 0,
            "votantes": stats[1] if stats else 0,
            "brancos": stats[2] if stats else 0,
            "nulos": stats[3] if stats else 0,
            "validos": total_votes,
            "abstencao": round(100 - (100 * stats[1] / stats[0]), 2) if stats and stats[0] else 0
        }
    })


if __name__ == "__main__":
    app.run(debug=True)