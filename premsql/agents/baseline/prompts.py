# --------------------------------- table selection --------------------------------- #

BASELINE_TEXT2SQL_TABLE_SELECTION_PROMPT = """
### Instruction: Respond only with valid JSON. No introduction or summary needed.
Do not add ``` at start / end of the output. You will be given a database
schema and user query. Your job is to output the list of table names which will
be included in the user's SQL query. 

Here are some examples:
CREATE TABLE customers (
    customer_id INT,
    customer_name VARCHAR(100),
    contact_info VARCHAR(100)
);
CREATE TABLE orders (
    order_id INT,
    customer_id INT,
    order_date DATE,
    total_amount FLOAT
);
CREATE TABLE products (
    product_id INT,
    product_name VARCHAR(100),
    price FLOAT
);
User Query: "What are all the tables in database"
Output:
{{
    "include": ["customers", "orders", "products"]
}}

Example:
Schema:
CREATE TABLE employees (
    employee_id INT,
    employee_name VARCHAR(100),
    department VARCHAR(100),
    salary FLOAT
);
CREATE TABLE departments (
    department_id INT,
    department_name VARCHAR(100),
    location VARCHAR(100)
);
CREATE TABLE projects (
    project_id INT,
    project_name VARCHAR(100),
    budget FLOAT
);
User Query: "List the names of employees and their salaries."
Output:
{{
    "include": ["employees"]
}}
Example:
Schema:
CREATE TABLE students (
    student_id INT,
    student_name VARCHAR(100),
    grade_level INT
);

CREATE TABLE courses (
    course_id INT,
    course_name VARCHAR(100),
    teacher_id INT
);

CREATE TABLE enrollments (
    student_id INT,
    course_id INT,
    enrollment_date DATE
);
User Query: "Show the list of students enrolled in courses."
Output:
{{
    "include": ["students", "enrollments"]
}}

Example:
Schema:
CREATE TABLE authors (
    author_id INT,
    author_name VARCHAR(100)
);

CREATE TABLE books (
    book_id INT,
    book_title VARCHAR(100),
    author_id INT
);

CREATE TABLE publishers (
    publisher_id INT,
    publisher_name VARCHAR(100)
);

CREATE TABLE book_sales (
    sale_id INT,
    book_id INT,
    sale_amount FLOAT
);

User Query: "Find the total sales for each book."
Output:
{{
    "include": ["books", "book_sales"]
}}

------ Assistant's turn ------

Like above examples, here is your DB schema: {schema}
some additional info about the columns (optional): {additional_info}
and the user question: {question}

NOTE: The name of the tables should always match with the name of
the tables present the above schema

Respond only with valid JSON. Do not write an introduction or summary. output:
"""

# --------------------------------- text to sql --------------------------------- #

BASELINE_TEXT2SQL_WORKER_PROMPT_NO_FEWSHOT = """
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
# Question: {question}
# SQL:
"""

BASELINE_TEXT2SQL_WORKER_PROMPT = """
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

# --------------------------------- error handling --------------------------------- #

BASELINE_TEXT2SQL_WORKER_ERROR_HANDLING_PROMPT = """
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

# --------------------------------- analysis base --------------------------------- #

BASELINE_ANALYSIS_WORKER_PROMPT = """
### Instruction: You will receive a user question and a table. Do not add ``` at start / end of the output. 
Analyze the table and provide your analysis following the below structure

# Analysis: (This should contain the answer from user's question)
# Reasoning: (This should contain the reasoning behind the your answer or analysis)

Example 1:

table: 
| Country | Population | GDP   |
|---------|------------|-------|
| A       | 5M         | 50B   |
| B       | 10M        | 100B  |
| C       | 2M         | 10B   |

User Question: Which country has the highest GDP per capita?
Output:

# Analysis: Country A has the highest GDP per capita.
# Reasoning: Country A's GDP per capita is 10,000, higher than B (10,000) and C (5,000).


Example 2:

table:
| Month    | Product | Sales | Returns | Profit Margin (%) |
|----------|---------|-------|---------|-------------------|
| January  | A       | 1000  | 50      | 20                |
| January  | B       | 1500  | 30      | 15                |
| February | A       | 1200  | 20      | 22                |
| February | B       | 1300  | 40      | 18                |
| March    | A       | 1100  | 25      | 21                |
| March    | B       | 1400  | 35      | 16                |

User Question: Which product had the highest profit margin in February?
Output:

# Analysis: Product A had the highest profit margin in February.
# Reasoning: Product A had a profit margin of 22% compared to Product B's 18% in February.


------ Assistant's turn ------

Dataframe to analyse: {dataframe}
user question: {question}
"""

# --------------------------------- analysis merger --------------------------------- #

BASELINE_ANALYSIS_MERGER_PROMPT = """Your task is to summarise
You will be given a set of summaries and reasoning in the form of a list of
json. Your task is to review the analuse and reasoning and summarise them:

- analysis1
- analysis2
- analysis3
- analysis4
and so on....

You will see the analysis and summarise them in a good
human readible format. 

------ Assistant's turn ------

Here is your analysis: {analysis}
Summary output:
"""

# --------------------------------- plot base --------------------------------- #

BASELINE_CHART_WORKER_PROMPT_TEMPLATE = """
### Instruction: Respond only with valid JSON. No introduction or summary needed. You are a senior data analyst. You know how to plot data when asked some analysis question. Do not add ``` at start / end of the output.

You will be given a user question, a list of dataframe column names, and you will output a JSON with
the following structure:

{{
    "x": # output the column name which should be on x-axis,
    "y": # output the column name which should be on y-axis,
    "plot_type": # The type of plot
}}

You can choose from these plot types:

- area: if you think you need to plot an area chart,
- bar: if you think you need to plot a bar chart,
- scatter: if you think you need to plot a scatter plot,
- histogram: if you think you need to plot a histogram,
- line: if you think you need to plot a line chart,
### Examples:

Example 1:
User Question: "Show the relationship between sales and revenue."

Dataframe columns: ["product_name", "sales", "revenue"]

Output:
{{
    "x": "sales",
    "y": "revenue",
    "plot_type": "scatter"
}}

Example 2:
User Question: "Show the distribution of product sales."

Dataframe columns: ["product_name", "sales"]

Output:
{{
    "x": "product_name",
    "y": "sales",
    "plot_type": "bar"
}}

Example 3:
User Question: "Show the change in temperature over time."

Dataframe columns: ["date", "temperature"]

Output:
{{
    "x": "date",
    "y": "temperature",
    "plot_type": "line"
}}

Example 4:
User Question: "Show the frequency distribution of employee ages."

Dataframe columns: ["employee_name", "age"]

Output:
{{
    "x": "age",
    "y": None,
    "plot_type": "histogram"
}}

------ Assistant's turn ------

Like the above example, here is your dataframe columns: {columns}
and here is user question: {question}

NOTE: From user's question you need to find the column of the table that makes
sense. Do not add any column name which is not present in {columns}. If there is nothing
to add just put None

Respond only with valid JSON. Do not write an introduction or summary. output:
"""

# --------------------------------- followup base --------------------------------- #

BASELINE_FOLLOWUP_WORKER_PROMPT = """
### Instruction: Respond only with valid JSON. No introduction or summary needed.
You will act like a simple conversation agent who knows to manage it's assistant who either plots or
write SQL query. If your assistant fails in quering the DB or plotting a graph then your job is to 
suggest user an alternative question or decision that will help your assistant to be successful in either query / plot / analysis next time.
Do not add ``` at start / end of the output.

You will be recieving the following input:
1. DB Schema: The schema of the database 
2. Decision: The decision that your assistant took. Decision could be either 'query' or 'plot' or 'analyse'
3. Query: The question that user asked.
4. Dataframe: (Optinal can be null) the dataframe that was being output or given as input
5. Analysis: Some text analysis from the model
6. Error from assistant: The error that your assistant made. 

Your job is to output a JSON with the following structure:

{{
    "alternate_decision": # can be either query / plot,
    "suggestion": # the alternate suggestive question 
}}

Here is an example:
Example 1:
DB Schema: 
CREATE TABLE sales (
    product_id INT,
    product_name VARCHAR(100),
    sale_date DATE,
    revenue FLOAT
);

Decision: "query"
Query: "What is the average revenue for products sold after 2023?"
Dataframe: null
Analysis: null
Error from assistant: "Query failed due to incorrect date format."

Output:
{{
    "alternate_decision": "query",
    "suggestion": "Could you find the average revenue for products sold in 2024 onwards?"
}}
Example 2:
DB Schema:
CREATE TABLE employees (
    employee_id INT,
    employee_name VARCHAR(100),
    department VARCHAR(100),
    salary FLOAT
);

Decision: "plot"
Query: "Show a line chart of the salary distribution by department."
Dataframe: null
Analysis: null
Error from assistant: "Data insufficient to generate the plot."

Output:
{{
    "alternate_decision": "plot",
    "suggestion": "Could you plot a bar chart showing total salary by department instead?"
}}

Example 1:
DB Schema:
CREATE TABLE sales (
    product_id INT,
    product_name VARCHAR(100),
    sale_date DATE,
    revenue FLOAT
);

Decision: "plot"
Query: "Plot the monthly revenue trend for 2024."
Dataframe: null
Analysis: null
Error from assistant: "Insufficient data to plot the monthly trend."

Output:
{{
    "alternate_decision": "query",
    "suggestion": "Can you query the total monthly revenue for 2024 so we can plot the trend afterward?"
}}

Example:
DB Schema:
CREATE TABLE sales (
    product_id INT,
    product_name VARCHAR(100),
    sale_date DATE,
    revenue FLOAT
);

Decision: "analyse"
Query: "Why xyz product name is doing unwell"
Dataframe: null
Analysis: "because they have less interaction, not good product"
Error from assistant: "null"

Output:
{{
    "alternate_decision": "analyse",
    "suggestion": "Why the product name xyz is not doing good and explain it in points"
}}

------ Assistant's turn ------

DB Schema: {schema}
Decision: {decision}
Query: {question}
Dataframe: {dataframe}
Analysis: {analysis}
Error from assistant: {error_from_model}

Your JSON keys should be only: `alternate_decision` and `suggestion`
Respond only with valid JSON. Do not write an introduction or summary. output:
"""
