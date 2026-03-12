from app.schemas.db_column import DBColumn

class Schema:
    CREATED_AT = DBColumn(name="created_at",type="TIMESTAMP",attributes=["NOT NULL", "DEFAULT CURRENT_TIMESTAMP"])
    UPDATED_AT = DBColumn(name="updated_at", type="TIMESTAMP", attributes=["NOT NULL", "DEFAULT CURRENT_TIMESTAMP"])
    
    _TAIL_FIELDS = {"created_at", "updated_at"}

    @classmethod
    def columns(cls) -> list[DBColumn]:
        cols = {}

        for base in reversed(cls.__mro__):
            for v in vars(base).values():
                if isinstance(v, DBColumn):
                    cols[v.name] = v   

        return list(cols.values())
    
    @classmethod
    def column_names(cls) -> list[str]:
        return [c.name for c in cls.columns() if c.name not in cls._TAIL_FIELDS]

    @classmethod
    def field_count(cls) -> int:
        return len([c for c in cls.columns() if c.name not in cls._TAIL_FIELDS])
