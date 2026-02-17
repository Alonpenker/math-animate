from abc import ABC

from app.schemas.schema import Schema

class Repository(ABC):
    
    TABLE_NAME = "table_name"
    SCHEMA = Schema
    PRIMARY_KEY = "primary_key"
    
    @classmethod
    def get(cls):
        return f"SELECT * FROM {cls.TABLE_NAME} WHERE {cls.PRIMARY_KEY}=%s"
    
    @classmethod
    def insert(cls):
        placeholders = ",".join(['%s']*cls.SCHEMA.field_count())
        columns = ','.join(col for col in cls.SCHEMA.column_names())
        return f"""INSERT INTO {cls.TABLE_NAME} ({columns}) VALUES ({placeholders})"""
    
    @classmethod
    def modify(cls, field: str):
        if field.upper() not in [col.upper() for col in cls.SCHEMA.column_names()]:
            raise ValueError(f"Field {field} not found in table {cls.TABLE_NAME}")
        return f"UPDATE {cls.TABLE_NAME} SET {field.upper()}=%s, {Schema.UPDATED_AT.name}=CURRENT_TIMESTAMP WHERE {cls.PRIMARY_KEY}=%s"
    
    @classmethod
    def delete(cls):
        return f"DELETE FROM {cls.TABLE_NAME} WHERE {cls.PRIMARY_KEY}=%s"
    
    @classmethod
    def get_all(cls):
        return f"SELECT * FROM {cls.TABLE_NAME}"
    
    @classmethod
    def get_all_by_key(cls):
        return f"SELECT * FROM {cls.TABLE_NAME} WHERE {cls.PRIMARY_KEY}=%s"
    
    @classmethod
    def get_all_by_job(cls):
        return f"SELECT * FROM {cls.TABLE_NAME} WHERE job_id=%s"
    
    @classmethod
    def get_all_by_field(cls, field: str):
        if field not in cls.SCHEMA.column_names():
            raise ValueError(f"Field {field} not found in table {cls.TABLE_NAME}")
        return f"SELECT * FROM {cls.TABLE_NAME} WHERE {field}=%s"
    
    @classmethod
    def search_by_vector(cls, vector_field: str, filter_field: str):
        return (
            f"SELECT *, {vector_field} <=> %s AS distance "
            f"FROM {cls.TABLE_NAME} "
            f"WHERE {filter_field} = %s "
            f"ORDER BY distance "
            f"LIMIT %s"
        )

    @classmethod
    def _create(cls):
        return f"CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (" + \
                ', '.join(f"{col.name} {col.sql_type}" for col in cls.SCHEMA.columns()) + ")"
    
    @classmethod
    def _truncate(cls):
        return f"TRUNCATE TABLE {cls.TABLE_NAME}"
    
    @classmethod
    def _drop(cls):
        return f"DROP TABLE IF EXISTS {cls.TABLE_NAME}"
    
    @classmethod
    def _constraint(cls, parent_table: str, 
                    foreign_key: str, cascade: bool = False):
        action = f"ALTER TABLE {cls.TABLE_NAME} ADD CONSTRAINT {f'{cls.TABLE_NAME.lower()}_{foreign_key}_fkey'} FOREIGN KEY ({foreign_key}) REFERENCES {parent_table}({foreign_key}) "
        if cascade:
            return action + "ON DELETE CASCADE"
        else:
            return action + "ON DELETE SET NULL"
