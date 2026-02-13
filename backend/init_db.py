from backend.database import engine
from backend import models

def init_db():
    print("Creating tables...")
    models.Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    init_db()
