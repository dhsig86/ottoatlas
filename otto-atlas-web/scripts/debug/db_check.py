import psycopg2
url = "postgresql://neondb_owner:npg_U1fknaVLh9su@ep-super-fog-ameqmvc0.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = cur.fetchall()
    print('Tables:', [t[0] for t in tables])
    for t in tables:
        cur.execute(f"SELECT count(*) FROM {t[0]};")
        print(f"{t[0]} count:", cur.fetchone()[0])
    conn.close()
except Exception as e:
    print('Error:', e)
