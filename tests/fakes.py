"""A tiny in-memory stand-in for the Supabase client, just enough for tests.

It supports the chained style the app uses:
    supabase.table("x").select("*").eq("id", v).execute()
    supabase.table("x").update({...}).eq("id", v).execute()
    supabase.table("x").delete().eq("id", v).execute()
"""

import re


class _Resp:
    def __init__(self, data):
        self.data = data


class _FakeTable:
    def __init__(self, store, name):
        self.store = store
        self.name = name
        self._conditions = {}
        self._not_conditions = {}
        self._ilike_conditions = {}
        self._update = None
        self._insert = None
        self._delete = False
        self._single = False
        self._range = None
        self._less_than = {}
        self._or_conditions = []

    def select(self, *args, **kwargs):
        return self

    def update(self, data):
        self._update = data
        return self

    def delete(self):
        self._delete = True
        return self

    def insert(self, data):
        self._insert = data
        return self

    def eq(self, column, value):
        self._conditions[column] = value
        return self

    def neq(self, column, value):
        self._not_conditions[column] = value
        return self

    def ilike(self, column, pattern):
        self._ilike_conditions[column] = pattern
        return self

    def or_(self, expression):
        self._or_conditions.append(expression)
        return self

    def lt(self, column, value):
        self._less_than[column] = value
        return self

    def single(self):
        self._single = True
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def range(self, start, end):
        self._range = (start, end)
        return self

    def _matches(self, row):
        if any(row.get(k) != v for k, v in self._conditions.items()):
            return False
        if any(row.get(k) == v for k, v in self._not_conditions.items()):
            return False
        for column, pattern in self._ilike_conditions.items():
            regex = "^" + re.escape(pattern).replace("%", ".*").replace("_", ".") + "$"
            if not re.match(regex, str(row.get(column) or ""), re.IGNORECASE):
                return False
        for column, value in self._less_than.items():
            try:
                if int(row.get(column) or 0) >= int(value):
                    return False
            except (TypeError, ValueError):
                return False

        for expression in self._or_conditions:
            matched = False
            for part in expression.split(","):
                match = re.match(r"^([^.]+)\.(ilike|eq)\.(.*)$", part)
                if not match:
                    continue
                column, operator, value = match.groups()
                cell = str(row.get(column) or "")
                if operator == "eq" and cell == value:
                    matched = True
                    break
                if operator == "ilike":
                    pattern = "^" + re.escape(value).replace("%", ".*").replace("_", ".") + "$"
                    if re.match(pattern, cell, re.IGNORECASE):
                        matched = True
                        break
            if not matched:
                return False
        return True

    def execute(self):
        rows = self.store.setdefault(self.name, [])

        if self._insert is not None:
            if isinstance(self._insert, dict):
                self._insert.setdefault("id", f"{self.name}-{len(rows) + 1}")
            rows.append(self._insert)
            return _Resp([self._insert])

        matched = [r for r in rows if self._matches(r)]

        if self._delete:
            for row in matched:
                rows.remove(row)
            return _Resp(matched)

        if self._update is not None:
            for row in matched:
                row.update(self._update)
            return _Resp(matched)

        # select: return copies so tests can assert on the store independently
        selected = [dict(row) for row in matched]
        if self._range:
            start, end = self._range
            selected = selected[start : end + 1]
        if self._single:
            return _Resp(selected[0] if selected else None)
        return _Resp(selected)


class FakeSupabase:
    def __init__(self):
        self.store = {}

    def table(self, name):
        return _FakeTable(self.store, name)
