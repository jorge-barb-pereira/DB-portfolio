import os, psycopg2
conn = psycopg2.connect(host='127.0.0.1', port='5555', dbname='autarquicas2021', user='admin', password=os.environ["DB_PASS"])
cur = conn.cursor()
cur.execute("SELECT orgao, partido_sigla, votos FROM eleicoes.resultados_partidos WHERE territorio_codigo='130408' ORDER BY votos DESC")
print("Rio Tinto:", cur.fetchall())
cur.execute("SELECT orgao, inscritos, votantes FROM eleicoes.estatisticas_globais WHERE territorio_codigo='130408'")
print("Stats:", cur.fetchall())
