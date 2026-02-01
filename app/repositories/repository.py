from abc import ABC

class Repository(ABC):
    
    TABLE_NAME = "table_name"
    COLUMNS = [("column_name","column_type")]
    PRIMARY_KEY = "primary_key"
    
    @classmethod
    def get(cls):
        return f"SELECT * FROM {cls.TABLE_NAME} WHERE {cls.PRIMARY_KEY}=%s"
    
    @classmethod
    def insert(cls):
        placeholders = ",".join(['%s']*len(cls.COLUMNS))
        columns = ','.join(f"{col}" for col, _ in cls.COLUMNS)
        return f"""INSERT INTO {cls.TABLE_NAME} ({columns}) VALUES ({placeholders})"""
    
    @classmethod
    def modify(cls, field: str):
        if field.lower() not in [col.lower() for col, _ in cls.COLUMNS]:
            raise ValueError(f"Field {field} not found in table {cls.TABLE_NAME}")
        return f"UPDATE {cls.TABLE_NAME} SET {field.upper()}=%s WHERE {cls.PRIMARY_KEY}=%s"
    
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
    def _create(cls):
        return f"CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (" + \
                ', '.join(f"{col} {typ}" for col, typ in cls.COLUMNS) + ")"
    
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