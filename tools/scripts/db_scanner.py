import os
import json
from datetime import datetime, timezone
from loguru import logger
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

# .env 파일에서 환경 변수 로드
load_dotenv('.env.dev')

# 환경 변수에서 설정 가져오기
class Settings:
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_host = os.getenv("POSTGRES_HOST")
    postgres_port = os.getenv("POSTGRES_PORT")
    postgres_dbname = os.getenv("POSTGRES_DBNAME")

settings = Settings()

# 데이터베이스 연결 문자열 생성
DATABASE_URL = f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_dbname}"

def fetch_db_info(engine):
    db_info = {}
    inspector = inspect(engine)
    
    for schema in inspector.get_schema_names():
        if schema not in ['information_schema', 'pg_catalog']:
            db_info[schema] = {}
            for table_name in inspector.get_table_names(schema=schema):
                db_info[schema][table_name] = {
                    "columns": [],
                    "foreign_keys": [],
                    "primary_key": []
                }
                
                # 컬럼 정보
                for column in inspector.get_columns(table_name, schema=schema):
                    db_info[schema][table_name]["columns"].append({
                        "column_name": column['name'],
                        "data_type": str(column['type'])
                    })
                
                # 외래 키 정보
                for fk in inspector.get_foreign_keys(table_name, schema=schema):
                    db_info[schema][table_name]["foreign_keys"].append({
                        "constrained_columns": fk['constrained_columns'],
                        "referred_schema": fk['referred_schema'],
                        "referred_table": fk['referred_table'],
                        "referred_columns": fk['referred_columns']
                    })
                
                # 기본 키 정보
                pk = inspector.get_pk_constraint(table_name, schema=schema)
                if pk and 'constrained_columns' in pk:
                    db_info[schema][table_name]["primary_key"] = pk['constrained_columns']
    
    return db_info

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def scan_and_save_db_info(engine):
    db_info = fetch_db_info(engine)
    save_to_json(db_info, 'tools/data/configs/database_schema.json')
    return db_info

def main():
    logger.info("Starting database schema scan")
    
    try:
        engine = create_engine(DATABASE_URL)
        db_info = scan_and_save_db_info(engine)
        logger.info(f"Database schema saved to database_schema.json")
        logger.info(f"Scanned {len(db_info)} schemas")
        for schema, tables in db_info.items():
            logger.info(f"Schema '{schema}' contains {len(tables)} tables")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    
    logger.info("Database schema scan completed")

if __name__ == "__main__":
    main()