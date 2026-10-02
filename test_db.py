from sqlalchemy import create_engine, text


# NEW (WSL MySQL):
WINDOWS_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "mande123"
DATABASE_URL = f"mysql+pymysql://root:{DB_PASSWORD}@{WINDOWS_HOST}:3306/price_tracker"


try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"connect_timeout": 5}
    )

    with engine.connect() as connection:
        result = connection.execute(text("SELECT DATABASE()"))
        database_name = result.scalar()

        print("Connection successful!")
        print(f"Connected database: {database_name}")

except Exception as error:
    print("Connection failed:")
    print(error)
