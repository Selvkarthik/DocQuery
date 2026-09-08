from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PWD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB')}"
DB_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv('DB_USER'),
    password=os.getenv('DB_PWD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB')
)

engine = create_engine(url=DB_URL)

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()