"""Tree-walking interpreter: executes AST nodes against a pandas DataFrame."""
import operator
import pandas as pd

from dsl_parser import (
    LoadStmt, FilterStmt, SortStmt, GroupByStmt, AggregateStmt,
    SelectStmt, ExportStmt, ShowStmt, DescribeStmt,
)

OPS = {
    '>': operator.gt, '<': operator.lt,
    '>=': operator.ge, '<=': operator.le,
    '==': operator.eq, '=': operator.eq, '!=': operator.ne,
}

FUNC_MAP = {
    'AVERAGE': 'mean', 'SUM': 'sum', 'COUNT': 'count',
    'MIN': 'min', 'MAX': 'max',
}


class DSLRuntimeError(Exception):
    def __init__(self, message, line=None):
        loc = f" (line {line})" if line else ""
        super().__init__(f"Runtime error{loc}: {message}")
        self.line = line


class Interpreter:
    """Holds the running program state: current DataFrame, active GROUPBY
    column, and the most recent aggregation result."""

    def __init__(self, verbose=True):
        self.df = None
        self.group_col = None
        self.last_result = None
        self.verbose = verbose

    def run(self, statements):
        for stmt in statements:
            self.execute(stmt)

    def execute(self, stmt):
        handler = getattr(self, f"exec_{type(stmt).__name__}", None)
        if handler is None:
            raise DSLRuntimeError(f"no handler for {type(stmt).__name__}")
        handler(stmt)

    def _active(self):
        if self.df is None:
            raise DSLRuntimeError("no data loaded — use LOAD <file.csv> first")
        return self.df

    def _log(self, msg):
        if self.verbose:
            print(msg)

    # ---- statement handlers ----

    def exec_LoadStmt(self, s: LoadStmt):
        try:
            self.df = pd.read_csv(s.filename)
        except FileNotFoundError:
            raise DSLRuntimeError(f"file not found: {s.filename}", s.line)
        except Exception as e:
            raise DSLRuntimeError(f"failed to load {s.filename}: {e}", s.line)
        self.group_col = None
        self.last_result = None
        self._log(f"[LOAD] {s.filename} -> {len(self.df)} rows, {len(self.df.columns)} columns")

    def exec_FilterStmt(self, s: FilterStmt):
        df = self._active()
        if s.column not in df.columns:
            raise DSLRuntimeError(f"unknown column '{s.column}'", s.line)
        comparand = df[s.value] if (isinstance(s.value, str) and s.value in df.columns) else s.value
        try:
            mask = OPS[s.op](df[s.column], comparand)
        except Exception as e:
            raise DSLRuntimeError(f"cannot compare '{s.column}' {s.op} {s.value!r}: {e}", s.line)
        before = len(df)
        self.df = df[mask].reset_index(drop=True)
        self.last_result = None
        self._log(f"[FILTER] {s.column} {s.op} {s.value} -> {len(self.df)}/{before} rows kept")

    def exec_SortStmt(self, s: SortStmt):
        df = self._active()
        if s.column not in df.columns:
            raise DSLRuntimeError(f"unknown column '{s.column}'", s.line)
        self.df = df.sort_values(by=s.column, ascending=(s.order == 'ASC')).reset_index(drop=True)
        self.last_result = None
        self._log(f"[SORT] by {s.column} {s.order}")

    def exec_GroupByStmt(self, s: GroupByStmt):
        df = self._active()
        if s.column not in df.columns:
            raise DSLRuntimeError(f"unknown column '{s.column}'", s.line)
        self.group_col = s.column
        self.last_result = None
        self._log(f"[GROUPBY] {s.column}")

    def exec_AggregateStmt(self, s: AggregateStmt):
        df = self._active()
        if s.column not in df.columns:
            raise DSLRuntimeError(f"unknown column '{s.column}'", s.line)
        pandas_func = FUNC_MAP[s.func]
        out_col = f"{s.func.lower()}_{s.column}"
        try:
            if self.group_col:
                result = getattr(df.groupby(self.group_col)[s.column], pandas_func)()
                self.last_result = result.reset_index().rename(columns={s.column: out_col})
            else:
                value = getattr(df[s.column], pandas_func)()
                self.last_result = pd.DataFrame({out_col: [value]})
        except Exception as e:
            raise DSLRuntimeError(f"failed to compute {s.func}({s.column}): {e}", s.line)
        label = f"grouped by {self.group_col}" if self.group_col else "overall"
        self._log(f"[{s.func}] {s.column} ({label})")
        if self.verbose:
            print(self.last_result.to_string(index=False))

    def exec_SelectStmt(self, s: SelectStmt):
        df = self._active()
        missing = [c for c in s.columns if c not in df.columns]
        if missing:
            raise DSLRuntimeError(f"unknown column(s): {', '.join(missing)}", s.line)
        self.df = df[s.columns].reset_index(drop=True)
        self.last_result = None
        self._log(f"[SELECT] {', '.join(s.columns)}")

    def exec_ExportStmt(self, s: ExportStmt):
        target = self.last_result if self.last_result is not None else self._active()
        try:
            target.to_csv(s.filename, index=False)
        except Exception as e:
            raise DSLRuntimeError(f"failed to export to {s.filename}: {e}", s.line)
        self._log(f"[EXPORT] wrote {len(target)} rows -> {s.filename}")

    def exec_ShowStmt(self, s: ShowStmt):
        target = self.last_result if self.last_result is not None else self._active()
        n = s.n or 10
        print(target.head(n).to_string(index=False))

    def exec_DescribeStmt(self, s: DescribeStmt):
        df = self._active()
        print(df.describe(include='all').to_string())
