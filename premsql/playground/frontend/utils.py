import re 
import os 
import pandas as pd 
import kagglehub
import sqlite3
from pathlib import Path
from platformdirs import user_cache_dir
from premsql.logger import setup_console_logger
from premsql.security import (
    resolve_path_within_root,
    sanitize_filename,
    validate_session_name,
)

logger = setup_console_logger("[FRONTEND-UTILS]")

MAX_UPLOAD_FILES = 20
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
MAX_TOTAL_UPLOAD_SIZE_BYTES = 100 * 1024 * 1024
MAX_CSV_ROWS = 250_000
MAX_CSV_COLUMNS = 200
MAX_CSV_FILES_PER_IMPORT = 50

def _is_valid_kaggle_id(kaggle_id: str) -> bool:
    pattern = r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, kaggle_id))

def download_from_kaggle(kaggle_dataset_id: str):
    path = kagglehub.dataset_download(handle=kaggle_dataset_id)
    return path 

def _migrate_to_sqlite(csv_folder: Path, sqlite_db_path: Path) -> Path:
    """Common migration logic for both Kaggle and local CSV uploads."""
    conn = sqlite3.connect(sqlite_db_path)
    try:
        csv_files = list(csv_folder.glob("*.csv"))
        if len(csv_files) > MAX_CSV_FILES_PER_IMPORT:
            raise ValueError(
                f"Too many CSV files. Maximum allowed is {MAX_CSV_FILES_PER_IMPORT}."
            )

        for csv_file in csv_files:
            if csv_file.stat().st_size > MAX_FILE_SIZE_BYTES:
                raise ValueError(
                    f"File '{csv_file.name}' exceeds the {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB limit."
                )
            table_name = csv_file.stem
            df = pd.read_csv(csv_file)
            if len(df) > MAX_CSV_ROWS:
                raise ValueError(
                    f"File '{csv_file.name}' exceeds the maximum row limit of {MAX_CSV_ROWS}."
                )
            if len(df.columns) > MAX_CSV_COLUMNS:
                raise ValueError(
                    f"File '{csv_file.name}' exceeds the maximum column limit of {MAX_CSV_COLUMNS}."
                )
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            logger.info(f"Migrated {csv_file.name} to table '{table_name}'")
        
        logger.info(f"Successfully migrated all CSV files to {sqlite_db_path}")
        return sqlite_db_path
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise
    finally:
        conn.close()

def migrate_from_csv_to_sqlite(
    folder_containing_csvs: str, 
    session_name: str
) -> Path:
    validated_session_name = validate_session_name(session_name)
    sqlite_db_folder = Path(user_cache_dir()) / "premsql" / "kaggle"
    os.makedirs(sqlite_db_folder, exist_ok=True)
    sqlite_db_path = resolve_path_within_root(
        sqlite_db_folder, f"{validated_session_name}.sqlite"
    )
    return _migrate_to_sqlite(Path(folder_containing_csvs), sqlite_db_path)

def migrate_local_csvs_to_sqlite(
    uploaded_files: list,
    session_name: str
) -> Path:
    validated_session_name = validate_session_name(session_name)
    cache_dir = Path(user_cache_dir())
    csv_root = cache_dir / "premsql" / "csv_uploads"
    csv_folder = resolve_path_within_root(csv_root, validated_session_name)
    sqlite_db_folder = csv_root
    
    os.makedirs(csv_folder, exist_ok=True)
    os.makedirs(sqlite_db_folder, exist_ok=True)
    
    sqlite_db_path = resolve_path_within_root(
        sqlite_db_folder, f"{validated_session_name}.sqlite"
    )

    if len(uploaded_files) > MAX_UPLOAD_FILES:
        raise ValueError(f"Too many files uploaded. Maximum allowed is {MAX_UPLOAD_FILES}.")

    total_size = 0
    
    # Save uploaded files to CSV folder
    for uploaded_file in uploaded_files:
        file_size = getattr(uploaded_file, "size", len(uploaded_file.getvalue()))
        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"File '{uploaded_file.name}' exceeds the {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB limit."
            )
        total_size += file_size
        if total_size > MAX_TOTAL_UPLOAD_SIZE_BYTES:
            raise ValueError(
                f"Total upload size exceeds the {MAX_TOTAL_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB limit."
            )
        safe_name = sanitize_filename(uploaded_file.name)
        file_path = resolve_path_within_root(csv_folder, safe_name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
    
    return _migrate_to_sqlite(csv_folder, sqlite_db_path)
