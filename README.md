# CSV DSL Interpreter

This project implements a small domain-specific language (DSL) for CSV data analysis. The interpreter reads a script, tokenizes it, parses it into statements, and executes those statements against a `students.csv` dataset.

## What this project demonstrates

This project is a strong fit for a programming languages assignment because it shows the full lifecycle of a tiny language implementation:

- lexical analysis via the lexer
- parsing via a recursive-descent parser
- AST construction
- a tree-walking interpreter runtime
- runtime error handling
- CSV-based data processing

## Supported DSL commands

The language supports the following statements:

- `LOAD <filename>`
- `FILTER <column> <op> <value>`
- `SORT <column> [ASC|DESC]`
- `GROUPBY <column>`
- `AVERAGE <column>`
- `SUM <column>`
- `COUNT <column>`
- `MIN <column>`
- `MAX <column>`
- `SELECT <col1>, <col2>, ...`
- `SHOW [n]`
- `EXPORT <filename>`
- `DESCRIBE`

Example comparison operators are:

- `>`
- `<`
- `>=`
- `<=`
- `==`
- `!=`

## Example script

```text
LOAD students.csv
FILTER GPA >= 3.5
GROUPBY Major
AVERAGE GPA
EXPORT report.csv
```

## How to run

From the project folder, generate sample data:

```powershell
C:/Users/sichu/AppData/Local/Programs/Python/Python313/python.exe make_sample_data
```

Then run the DSL interpreter with a script file:

```powershell
C:/Users/sichu/AppData/Local/Programs/Python/Python313/python.exe main.py sample.dsl
```

## Output

The interpreter prints progress messages while executing, and when the script ends it writes the requested output to the export file.

In the sample above, the program will:

1. load `students.csv`
2. filter rows where `GPA >= 3.5`
3. group by `Major`
4. compute `AVERAGE GPA`
5. export the aggregated results to `report.csv`

## Project files

- `lexer.py` — tokenizes the DSL source
- `dsl_parser.py` — parses tokens into statements
- `interpreter.py` — executes the AST against a pandas DataFrame
- `main.py` — command-line entrypoint and REPL
- `make_sample_data` — generates sample dataset
- `sample.dsl` — example DSL program

## Notes

The current implementation is intentionally small and readable so it remains a clear demonstration of language design and interpreter structure.
