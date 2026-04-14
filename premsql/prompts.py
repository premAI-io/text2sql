BASE_TEXT2SQL_PROMPT = """
# Follow these instruction:
You will be given schemas of tables of a database. Your job is to write correct
error free SQL query based on the question asked. Please make sure:

1. Do not add ``` at start / end of the query. It should be a single line query in a  single line (string format)
2. Make sure the column names are correct and exists in the table
3. For column names which has a space with it, make sure you have put `` in that column name
4. Only generate read-only SQL queries. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, or PRAGMA statements.
5. Think step by step and always check schema and question and the column names before writing the
query. 

# Database and Table Schema:
{schemas}

{additional_knowledge}

# Here are some Examples on how to generate SQL statements and use column names:
{few_shot_examples}

# Question: {question}

# SQL: 
"""

OLD_BASE_TEXT2SQL_PROMPT = """
# Instruction: 
- You will be given a question and a database schema.
- You need to write a SQL query to answer the question.
Do not add ``` at start / end of the query. It should be a single line query in 
a single line (string format).
- Make sure the column names are correct and exists in the table
- For column names which has a space with it, make sure you have put `` in that column name
- Only generate read-only SQL queries. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, or PRAGMA statements.

# Database and Table Schema:
{schemas}

{additional_knowledge}

# Here are some Examples on how to generate SQL statements and use column names:
{few_shot_examples}

# Question: {question}

# SQL:
"""

ERROR_HANDLING_PROMPT = """
{existing_prompt}

# Generated SQL: {sql}

## Error Message

{error_msg}

Carefully review the original question and error message, then rewrite the SQL query to address the identified issues. 
Ensure your corrected query uses correct column names, 
follows proper SQL syntax, and accurately answers the original question 
without introducing new errors.

# SQL: 
"""
