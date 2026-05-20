import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from database.database import Base

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    """Crée le moteur de base de données une seule fois pour la session."""
    engine = create_engine(TEST_DATABASE_URL)
    
    # On force SQLite à vérifier les clés étrangères
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
    return engine

@pytest.fixture(scope="function")
def db_session(engine):
    """Crée et nettoie proprement les tables à CHAQUE test."""
    # 1. On crée les tables à blanc avant le test
    Base.metadata.create_all(engine)
    
    # 2. On ouvre une session fraîche
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session  # Le test s'exécute ici

    # 3. Nettoyage strict après le test
    session.close()
    # On détruit tout pour garantir que le prochain test repart sur une base vierge
    Base.metadata.drop_all(engine)