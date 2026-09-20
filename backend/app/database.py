from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Handle SQLite connect args
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_collections_schema(target_engine):
    """
    Safely inspects SQLite collections and collection_items schema.
    If legacy VARCHAR primary key columns exist, migrates data to INTEGER AUTOINCREMENT
    without data loss.
    """
    try:
        import app.models  # Ensure all SQLAlchemy models are registered
        with target_engine.connect() as conn:
            old_exists = bool(conn.execute(__import__("sqlalchemy").text("SELECT name FROM sqlite_master WHERE type='table' AND name='_collections_old'")).fetchone())
            coll_row = conn.execute(__import__("sqlalchemy").text("SELECT sql FROM sqlite_master WHERE type='table' AND name='collections'")).fetchone()

            if not old_exists and (not coll_row or not coll_row[0]):
                return

            needs_migration = old_exists or ("VARCHAR" in coll_row[0].upper() or ("TEXT" in coll_row[0].upper() and "PRIMARY KEY" in coll_row[0].upper()))

            if needs_migration:
                print("[Database Migration] Performing non-destructive collections schema migration...")

                # 1. Rename existing tables if not already renamed
                if not old_exists:
                    conn.execute(__import__("sqlalchemy").text("ALTER TABLE collections RENAME TO _collections_old"))
                    if conn.execute(__import__("sqlalchemy").text("SELECT name FROM sqlite_master WHERE type='table' AND name='collection_items'")).fetchone():
                        conn.execute(__import__("sqlalchemy").text("ALTER TABLE collection_items RENAME TO _collection_items_old"))

                # 2. Re-create new collections and collection_items tables explicitly if missing
                if not conn.execute(__import__("sqlalchemy").text("SELECT name FROM sqlite_master WHERE type='table' AND name='collections'")).fetchone():
                    conn.execute(__import__("sqlalchemy").text(
                        "CREATE TABLE collections ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "name VARCHAR NOT NULL, "
                        "description TEXT, "
                        "created_at DATETIME, "
                        "updated_at DATETIME)"
                    ))
                if not conn.execute(__import__("sqlalchemy").text("SELECT name FROM sqlite_master WHERE type='table' AND name='collection_items'")).fetchone():
                    conn.execute(__import__("sqlalchemy").text(
                        "CREATE TABLE collection_items ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "collection_id INTEGER NOT NULL, "
                        "item_type VARCHAR NOT NULL DEFAULT 'observation', "
                        "scientific_name VARCHAR NOT NULL, "
                        "common_name VARCHAR, "
                        "category VARCHAR DEFAULT 'other', "
                        "observation_id VARCHAR, "
                        "created_at DATETIME, "
                        "FOREIGN KEY(collection_id) REFERENCES collections(id) ON DELETE CASCADE, "
                        "FOREIGN KEY(observation_id) REFERENCES observations(id) ON DELETE SET NULL)"
                    ))

                # 3. Read old collections and insert into new table
                old_colls = conn.execute(__import__("sqlalchemy").text("SELECT id, name, description, created_at, updated_at FROM _collections_old")).fetchall()
                uuid_map = {}
                for old_id, name, desc, created_at, updated_at in old_colls:
                    res_ins = conn.execute(
                        __import__("sqlalchemy").text("INSERT INTO collections (name, description, created_at, updated_at) VALUES (:name, :desc, :created_at, :updated_at)"),
                        {"name": name, "desc": desc, "created_at": created_at, "updated_at": updated_at}
                    )
                    new_id = res_ins.lastrowid
                    uuid_map[str(old_id)] = new_id

                # 4. Read old collection_items and insert into new table
                if conn.execute(__import__("sqlalchemy").text("SELECT name FROM sqlite_master WHERE type='table' AND name='_collection_items_old'")).fetchone():
                    old_items = conn.execute(__import__("sqlalchemy").text("SELECT * FROM _collection_items_old")).fetchall()
                    # Inspect column names
                    col_info = conn.execute(__import__("sqlalchemy").text("PRAGMA table_info(_collection_items_old)")).fetchall()
                    col_names = [col[1] for col in col_info]
                    for row in old_items:
                        row_dict = dict(zip(col_names, row))
                        mapped_coll_id = uuid_map.get(str(row_dict.get("collection_id")))
                        if mapped_coll_id is not None:
                            conn.execute(
                                __import__("sqlalchemy").text(
                                    "INSERT INTO collection_items (collection_id, item_type, scientific_name, common_name, category, observation_id, created_at) "
                                    "VALUES (:coll_id, :item_type, :sci_name, :com_name, :cat, :obs_id, :created_at)"
                                ),
                                {
                                    "coll_id": mapped_coll_id,
                                    "item_type": row_dict.get("item_type") or "observation",
                                    "sci_name": row_dict.get("scientific_name") or row_dict.get("common_name") or "Unknown species",
                                    "com_name": row_dict.get("common_name"),
                                    "cat": row_dict.get("category") or "other",
                                    "obs_id": row_dict.get("observation_id"),
                                    "created_at": row_dict.get("created_at") or row_dict.get("added_at")
                                }
                            )

                # 5. Drop temporary old tables
                if conn.execute(__import__("sqlalchemy").text("SELECT name FROM sqlite_master WHERE type='table' AND name='_collections_old'")).fetchone():
                    conn.execute(__import__("sqlalchemy").text("DROP TABLE _collections_old"))
                if conn.execute(__import__("sqlalchemy").text("SELECT name FROM sqlite_master WHERE type='table' AND name='_collection_items_old'")).fetchone():
                    conn.execute(__import__("sqlalchemy").text("DROP TABLE _collection_items_old"))

                conn.commit()
                print("[Database Migration] Collections schema successfully migrated to INTEGER AUTOINCREMENT keys!")

    except Exception as exc:
        print(f"[Database Migration] Notice/Migration status: {exc}")

