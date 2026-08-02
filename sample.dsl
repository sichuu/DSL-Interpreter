LOAD students.csv
FILTER GPA >= 3.5
GROUPBY Major
AVERAGE GPA
EXPORT report.csv
