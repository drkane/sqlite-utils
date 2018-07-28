import sqlite3
from collections import namedtuple

Column = namedtuple(
    "Column", ("cid", "name", "type", "notnull", "default_value", "is_pk")
)


class Database:
    def __init__(self, filename_or_conn):
        if isinstance(filename_or_conn, str):
            self.conn = sqlite3.connect(filename_or_conn)
        else:
            self.conn = filename_or_conn

    def __getitem__(self, table_name):
        return Table(self, table_name)

    @property
    def tables(self):
        return [
            r[0]
            for r in self.conn.execute(
                "select name from sqlite_master where type = 'table'"
            ).fetchall()
        ]

    def create_table(self, name, columns, pk=None):
        sql = """CREATE TABLE {table} (
            {columns}
        );
        """.format(
            table=name,
            columns=",\n".join(
                "   {col_name} {col_type} {primary_key}".format(
                    col_name=col_name,
                    col_type={
                        float: "FLOAT",
                        int: "INTEGER",
                        bool: "INTEGER",
                        str: "TEXT",
                        None.__class__: "TEXT",
                    }[col_type],
                    primary_key=" PRIMARY KEY" if (pk == col_name) else "",
                )
                for col_name, col_type in columns.items()
            ),
        )
        self.conn.execute(sql)
        return self[name]


class Table:
    def __init__(self, db, name):
        self.db = db
        self.name = name
        self.exists = self.name in self.db.tables

    @property
    def columns(self):
        if not self.exists:
            return []
        rows = self.db.conn.execute(
            "PRAGMA table_info([{}])".format(self.name)
        ).fetchall()
        return [Column(*row) for row in rows]

    def create(self, columns, pk=None, foreign_keys=None):
        # Ignore columns in foreign_keys list
        columns = {
            name: value
            for name, value in columns.items()
            if name not in {fk[0] for fk in (foreign_keys or [])}
        }
        self.db.create_table(self.name, columns, pk=pk)
        if foreign_keys:
            for args in foreign_keys:
                self.add_foreign_key(*args)
        self.exists = True

    def drop(self):
        return self.db.conn.execute("DROP TABLE {}".format(self.name))

    def add_foreign_key(self, column, column_type, other_table, other_column):
        sql = """
            ALTER TABLE {table} ADD COLUMN {column} {column_type}
            REFERENCES {other_table}({other_column});
        """.format(
            table=self.name,
            column=column,
            column_type=column_type,
            other_table=other_table,
            other_column=other_column,
        )
        result = self.db.conn.execute(sql)
        self.db.conn.commit()
        return result

    def detect_column_types(self, records):
        all_column_types = {}
        for record in records:
            for key, value in record.items():
                all_column_types.setdefault(key, set()).add(type(value))
        column_types = {}
        for key, types in all_column_types.items():
            if len(types) == 1:
                t = list(types)[0]
            elif {int, bool}.issuperset(types):
                t = int
            elif {int, float, bool}.issuperset(types):
                t = float
            else:
                t = str
            column_types[key] = t
        return column_types

    def insert(self, record, pk=None, foreign_keys=None, upsert=False):
        return self.insert_all(
            [record], pk=pk, foreign_keys=foreign_keys, upsert=upsert
        )

    def insert_all(
        self, records, pk=None, foreign_keys=None, upsert=False, batch_size=100
    ):
        """
        Like .insert() but takes a list of records and ensures that the table
        that it creates (if table does not exist) has columns for ALL of that
        data
        """
        if not self.exists:
            self.create(self.detect_column_types(records), pk, foreign_keys)
        all_columns = set()
        for record in records:
            all_columns.update(record.keys())
        all_columns = list(sorted(all_columns))
        for chunk in chunks(records, batch_size):
            sql = """
                INSERT {upsert} INTO {table} ({columns}) VALUES {rows};
            """.format(
                upsert="OR REPLACE" if upsert else "",
                table=self.name,
                columns=", ".join(all_columns),
                rows=", ".join(
                    """
                    ({placeholders})
                """.format(
                        placeholders=", ".join(["?"] * len(all_columns))
                    )
                    for record in chunk
                ),
            )
            values = []
            for record in chunk:
                values.extend(record.get(key, None) for key in all_columns)
            result = self.db.conn.execute(sql, values)
            self.db.conn.commit()
        return result

    def upsert(self, record, pk=None, foreign_keys=None):
        return self.insert(record, pk=pk, foreign_keys=foreign_keys, upsert=True)

    def upsert_all(self, records, pk=None, foreign_keys=None):
        return self.insert_all(records, pk=pk, foreign_keys=foreign_keys, upsert=True)


def chunks(sequence, size):
    for i in range(0, len(sequence), size):
        yield sequence[i : i + size]