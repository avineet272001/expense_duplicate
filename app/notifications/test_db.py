from app.database import engine

try:
    with engine.connect() as conn:
        print("Database Connected Successfully!")
except Exception as e:
    print("Error:")
    print(e)