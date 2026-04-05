import psycopg2

try:
    conexion = psycopg2.connect(
        user="postgres.xrsoidiofrjyifhlekiy",
        password="Adlai2024#.", 
        host="aws-1-us-east-1.pooler.supabase.com",
        port="6543",
        database="course"  # <--- CAMBIA ESTO A "postgres"
    )
    print("✅ ¡Conexión exitosa a Supabase!")
    
    # Si quieres comprobar que tu tabla "course" existe, puedes hacer esto:
    cursor = conexion.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tablas = cursor.fetchall()
    print("Tablas en tu base de datos:", tablas)
    
    cursor.close()
    conexion.close()
    
except Exception as e:
    print("❌ Error al conectar a la base de datos:")
    print(e)