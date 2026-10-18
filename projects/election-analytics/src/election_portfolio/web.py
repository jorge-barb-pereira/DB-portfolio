"""Read-only dashboard API using parameterized queries and bounded input."""
import json
import re

from flask import Flask, jsonify, render_template, request
import psycopg2
from .db import transaction


def create_app():
    app = Flask(__name__)

    @app.errorhandler(psycopg2.Error)
    def database_unavailable(error):
        app.logger.error('Database request failed (%s)',type(error).__name__)
        return jsonify(error='Database unavailable; check the local setup'),503

    @app.errorhandler(ValueError)
    def invalid_configuration(error):
        app.logger.error('Application configuration is incomplete')
        return jsonify(error='Application database configuration is incomplete'),503

    def selection():
        body = request.args.get('orgao','CM')
        territory = request.args.get('codigo','')
        if body not in ('CM','AM','AF') or (territory and not re.fullmatch(r'[0-9]{6}',territory)):
            return None
        return body,territory,'Freguesia' if body=='AF' else 'Município'

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/api/territories')
    def territories():
        choice = selection()
        if choice is None: return jsonify(error='Invalid elected body or territory code'),400
        body,_,kind = choice
        with transaction() as connection, connection.cursor() as cursor:
            cursor.execute('''SELECT t.codigo,t.nome FROM eleicoes.territorios t
                WHERE t.tipo=%s AND EXISTS(SELECT 1 FROM eleicoes.estatisticas_globais e
                    WHERE e.territorio_codigo=t.codigo AND e.orgao=%s) ORDER BY t.nome,t.codigo''',(kind,body))
            return jsonify([{'codigo':r[0],'nome':r[1]} for r in cursor.fetchall()])

    @app.get('/api/map')
    def map_data():
        choice = selection()
        if choice is None: return jsonify(error='Invalid elected body or territory code'),400
        body,_,kind = choice
        with transaction() as connection, connection.cursor() as cursor:
            cursor.execute('''WITH winners AS (
                SELECT w.territorio_codigo,string_agg(w.winning_party,' / ' ORDER BY w.winning_party) AS winner
                FROM eleicoes.vw_winning_party_per_territory w WHERE w.orgao=%s GROUP BY w.territorio_codigo)
                SELECT t.codigo,t.nome,w.winner,ST_AsGeoJSON(ST_Transform(
                    ST_SimplifyPreserveTopology(t.geom,50),4326))
                FROM eleicoes.territorios t JOIN winners w ON w.territorio_codigo=t.codigo
                WHERE t.tipo=%s AND t.geom IS NOT NULL ORDER BY t.codigo''',(body,kind))
            features = [{'type':'Feature','properties':{'codigo':r[0],'nome':r[1],'winner':r[2]},
                         'geometry':json.loads(r[3])} for r in cursor.fetchall()]
        return jsonify(type='FeatureCollection',features=features)

    @app.get('/api/results')
    def results():
        choice = selection()
        if choice is None: return jsonify(error='Invalid elected body or territory code'),400
        body,territory,kind = choice
        with transaction() as connection, connection.cursor() as cursor:
            cursor.execute('''SELECT t.codigo,t.nome FROM eleicoes.territorios t
                JOIN eleicoes.estatisticas_globais e ON e.territorio_codigo=t.codigo
                WHERE t.tipo=%s AND e.orgao=%s AND (%s='' OR t.codigo=%s) ORDER BY t.codigo''',
                (kind,body,territory,territory))
            selected = cursor.fetchall()
            if not selected: return jsonify(error='No election data for this territory/body'),404
            codes = [r[0] for r in selected]
            cursor.execute('''SELECT sum(e.inscritos),sum(e.votantes),sum(e.votos_brancos),sum(e.votos_nulos)
                FROM eleicoes.estatisticas_globais e WHERE e.orgao=%s AND e.territorio_codigo=ANY(%s)''',(body,codes))
            registered,voters,blank,null = [int(v or 0) for v in cursor.fetchone()]
            cursor.execute('''SELECT r.partido_sigla,sum(r.votos),sum(r.mandatos)
                FROM eleicoes.resultados_partidos r WHERE r.orgao=%s AND r.territorio_codigo=ANY(%s)
                GROUP BY r.partido_sigla ORDER BY sum(r.votos) DESC,r.partido_sigla''',(body,codes))
            data = cursor.fetchall()
        total = sum(int(r[1]) for r in data)
        output = [{'partido':r[0],'votos':int(r[1]),'mandatos':int(r[2]),
                   'vote_share':round(100*int(r[1])/total,2) if total else 0} for r in data]
        maximum = max((r['votos'] for r in output),default=0)
        winners = [r['partido'] for r in output if r['votos']==maximum and maximum>0]
        return jsonify(overall=not bool(territory),
            territory={'codigo':territory,'nome':selected[0][1] if territory else 'All selected territories','orgao':body},
            summary={'winner':' / '.join(winners) or 'No valid votes','winner_votes':maximum,
                     'tied':len(winners)>1,'total_votes':total,'total_municipalities':len(codes)},
            results=output,stats={'inscritos':registered,'votantes':voters,'brancos':blank,'nulos':null,
                'validos':total,'abstencao':round(100*(registered-voters)/registered,2) if registered else 0})

    return app


if __name__=='__main__':
    create_app().run(host='127.0.0.1',port=5000,debug=False)
