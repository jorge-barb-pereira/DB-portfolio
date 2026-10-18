import os
import psycopg2, os

def test_triggers_and_views():
    conn = psycopg2.connect(host='127.0.0.1', port='5555', dbname='autarquicas2021', user='admin', password=os.environ["DB_PASS"])
    conn.autocommit = True
    cur = conn.cursor()

    print('1. Applying 04_triggers_views.sql...')
    with open('Project/sql/04_triggers_views.sql', 'r', encoding='utf-8') as f:
        cur.execute(f.read())
    print('Triggers and Views created successfully.')

    print('\n2. Testing Validation Trigger (Negative Votes)...')
    try:
        cur.execute("INSERT INTO eleicoes.resultados_partidos (territorio_codigo, orgao, partido_sigla, votos, mandatos) VALUES ('130408', 'CM', 'TEST', -50, 0)")
    except Exception as e:
        print('Caught expected exception:', str(e).strip())

    print('\n3. Testing Audit Trigger...')
    # Insert a dummy row
    cur.execute("INSERT INTO eleicoes.partidos (sigla, nome_completo) VALUES ('TEST_AUDIT', 'Audit Party') ON CONFLICT DO NOTHING")
    cur.execute("INSERT INTO eleicoes.resultados_partidos (territorio_codigo, orgao, partido_sigla, votos, mandatos) VALUES ('130408', 'CM', 'TEST_AUDIT', 100, 1) ON CONFLICT DO NOTHING")
    # Update it
    cur.execute("UPDATE eleicoes.resultados_partidos SET votos = 150 WHERE partido_sigla = 'TEST_AUDIT'")
    # Check audit log
    cur.execute("SELECT old_votos, new_votos FROM eleicoes.audit_resultados_partidos WHERE partido_sigla = 'TEST_AUDIT'")
    audit_row = cur.fetchone()
    if audit_row:
        print(f'Audit Log Entry: Old Votes={audit_row[0]}, New Votes={audit_row[1]}')
    else:
        print('Audit Log Entry not found!')
    
    # Cleanup
    cur.execute("DELETE FROM eleicoes.resultados_partidos WHERE partido_sigla IN ('TEST', 'TEST_AUDIT')")
    cur.execute("DELETE FROM eleicoes.audit_resultados_partidos WHERE partido_sigla = 'TEST_AUDIT'")
    cur.execute("DELETE FROM eleicoes.partidos WHERE sigla = 'TEST_AUDIT'")

    print('\n4. Testing Views...')
    cur.execute("SELECT territorio_nome, taxa_abstencao_perc FROM eleicoes.vw_turnout_computation LIMIT 1")
    print('Turnout View Output:', cur.fetchone())

    cur.execute("SELECT territorio_nome, winning_party, winning_votes FROM eleicoes.vw_winning_party_per_territory LIMIT 1")
    print('Winning Party View Output:', cur.fetchone())

    cur.close()
    conn.close()

if __name__ == '__main__':
    test_triggers_and_views()
