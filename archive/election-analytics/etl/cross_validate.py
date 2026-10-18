import os, psycopg2

def apply_sql():
    conn = psycopg2.connect(host='127.0.0.1', port='5555', dbname='autarquicas2021', user='admin', password=os.environ["DB_PASS"])
    cur = conn.cursor()
    
    with open('Project/sql/02_functions_triggers.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
        
    cur.execute(sql)
    conn.commit()
    print("Applied 02_functions_triggers.sql")

def cross_validate():
    conn = psycopg2.connect(host='127.0.0.1', port='5555', dbname='autarquicas2021', user='admin', password=os.environ["DB_PASS"])
    cur = conn.cursor()
    
    # Let's cross validate a few random territories!
    cur.execute("""
        SELECT r.territorio_codigo, r.orgao, SUM(r.mandatos) AS total_mandates
        FROM eleicoes.resultados_partidos r
        WHERE r.mandatos > 0
        GROUP BY r.territorio_codigo, r.orgao
        LIMIT 5;
    """)
    test_cases = cur.fetchall()
    
    print("\n--- CROSS VALIDATING D'HONDT ---")
    for tc in test_cases:
        cod, org, total_mandates = tc
        
        print(f"\nTerritory: {cod} | Organ: {org} | Total Seats: {total_mandates}")
        
        # 1. Get Official Mandates
        cur.execute("""
            SELECT partido_sigla, mandatos 
            FROM eleicoes.resultados_partidos 
            WHERE territorio_codigo=%s AND orgao=%s AND mandatos > 0
            ORDER BY mandatos DESC, votos DESC
        """, (cod, org))
        official = {row[0]: row[1] for row in cur.fetchall()}
        
        # 2. Get D'Hondt Computed Mandates
        cur.execute("""
            SELECT partido_sigla, computed_mandates 
            FROM eleicoes.compute_dhondt(%s, %s, %s)
            ORDER BY computed_mandates DESC
        """, (cod, org, total_mandates))
        computed = {row[0]: row[1] for row in cur.fetchall()}
        
        print(f"Official: {official}")
        print(f"Computed: {computed}")
        
        if official == computed:
            print("EXACT MATCH!")
        else:
            print("MISMATCH!")

if __name__ == "__main__":
    apply_sql()
    cross_validate()
