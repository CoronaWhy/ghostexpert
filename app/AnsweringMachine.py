import re
import pandas as pd
import ollama
from rdflib import Graph
import duckdb
import os
import requests

class AnsweringMachine:
    def __init__(self, question, user_request, DEBUG=False):
        self.question = question
        self.user_request = user_request
        self.OLLAMA_HOST = os.getenv('OLLAMA_HOST')
        self.MODEL = os.getenv('MODEL')
        self.DEBUG = DEBUG
        self.db_file = 'tempodata.duckdb'
        self.datastream = None

    def set_rdf_file(self, rdf_file_path):
        self.rdf_file_path = rdf_file_path
        self.df = self.rdf_to_dataframe(self.rdf_file_path)
        return self.df

    def rdf_to_dataframe(self, rdf_file):
        # Create a new RDF graph
        graph = Graph()
        
        # Parse the RDF file
        graph.parse(rdf_file, format='turtle')  # Adjust format as necessary

        # Prepare a list to hold the data
        data = []

        # Iterate over all subject-predicate-object triples in the graph
        for subject, predicate, obj in graph:
            # Create a dictionary for each SPO triplet
            triplet_data = {
                'subject': str(subject),
                'predicate': str(predicate),
                'object': str(obj)
            }
            
            # Append the triplet data to the list
            data.append(triplet_data)

        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(data, columns=['subject', 'predicate', 'object'])

        return df

    def save_to_duckdb(self, df, table_name='rdf_data'):
        if not os.path.exists(self.db_file):
            print("DB file does not exist, creating it")
            # Connect to DuckDB (it will create the database file if it doesn't exist)
            conn = duckdb.connect(self.db_file)

            # Create a mapping of DataFrame dtypes to DuckDB types
            dtype_mapping = {
                'int64': 'INTEGER',
                'float64': 'FLOAT',
                'object': 'VARCHAR',
                'bool': 'BOOLEAN',
                'datetime64[ns]': 'TIMESTAMP'
            }

            # Create the table with the appropriate columns and their data types
            columns_with_types = []
            for column in df.columns:
                dtype = str(df[column].dtype)
                duckdb_type = dtype_mapping.get(dtype, 'VARCHAR')  # Default to VARCHAR if type not found
                columns_with_types.append(f"{column} {duckdb_type}")

            # Execute the CREATE TABLE statement
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_with_types)})")

            # Insert the DataFrame into the DuckDB table
            conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")

            # Close the connection
            conn.close()
            return conn
        else:
            print("DB file exists, connecting to it")
            conn = duckdb.connect(self.db_file)
            return conn 

    def generate_sql_query(self, table_name, columns, user_request):
        # Construct the prompt for the Ollama model
        prompt = f"Given the following SQL table, your job is to write queries given a user's request.\nCREATE TABLE {table_name} ({', '.join(columns)});\nUser request: {user_request}\nSQL Query:"

        # Call the Ollama model
        if self.DEBUG:
            print(prompt)
        try:
            response = ollama.chat(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract the SQL query from the response
            sql_query = response.json() #.get('message', {}).get('content', 'No query generated.')
            if self.DEBUG:
                print("sql_query", sql_query)
            # If the response contains the SQL query in a specific format, extract it
            sql_query = re.findall(r"```sql(.*)```", sql_query, re.DOTALL)[0]
            if self.DEBUG:
                print("[cleaned] sql_query", sql_query)
            sql_query = sql_query.strip()  # Remove any leading/trailing whitespace
            sql_query = sql_query.replace("```", "")
            sql_query = sql_query.replace("\\n", " ")
            #sql_query = "SELECT * FROM rdf_data LIMIT 5;"
            return sql_query
        except Exception as e:
            print(f"Error during query generation: {e}")
            return None

    def execute_sql_query(self, db_file='tempodata.duckdb', sql_query=None):
        if sql_query is None:
            print("No SQL query provided.")
            return None

        # Connect to DuckDB
        conn = duckdb.connect(db_file)

        # Execute the SQL query and fetch results
        result = conn.execute(sql_query).fetchall()
        return result
        try:
            result = conn.execute(sql_query).fetchall()
            self.datastream = result
            return result
        except Exception as e:
            print(f"Error executing SQL query: {e}")
            return None
        finally:
            conn.close()


    def librarian(self, question, sql_query, results):
        # Format the results for the Ollama model
        formatted_results = "\n".join([str(row) for row in results])
        advanced_prompt = f"Question: {question}\nSQL Query to answer the question: {sql_query}\nResults: {formatted_results}\nExplain the results in a way that is easy to understand:"
        if 'list' in self.user_request.lower():
            prompt = f"Question: {question}\nResults: {formatted_results}\nShow the results CBS databases without extra information in a way that is easy to understand:"
        else:
            prompt = f"Question: {question}\nResults: {formatted_results}\nExplain the results CBS databases without extra information in a way that is easy to understand:"

        # Call the Ollama model with the results
        try:
            response = ollama.chat(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            # Extract the response content
            if self.DEBUG:
                print("response", response)
            # Check if the expected keys are present
            if 'message' in response and 'content' in response['message']:
                answer = response['message']['content']
            else:
                answer = 'No valid answer found in the response.'

            return answer
        except Exception as e:
            print(f"Error sending results to Ollama: {e}")
            return None

    def clean_answer(self, answer):
        answer = answer.replace("(","")
        answer = answer.replace(")","")
        answer = answer.replace("'","")
        answer = answer.replace("\"","")
        answer = answer.replace("\\","")
        answer = answer.replace("`","")
        answer = answer.replace("*","")
        answer = answer.replace("^","")
        answer = answer.replace("~","")
        answer = answer.replace("|","")
        answer = answer.replace("\\","")
        answer = answer.replace("\\","")
        answer = answer.replace("\\","")
        answer = answer.replace("\\","")
        return answer

    def process_question(self, question, user_request):
        df = self.df
        
        # Print the DataFrame to verify its structure
        if self.DEBUG:
            print("DataFrame Structure:\n", df)

        # Save the DataFrame to DuckDB
        self.save_to_duckdb(df)

        # Example table name and columns
        table_name = "rdf_data"
        columns = df.columns.tolist()
        if self.DEBUG:
            print("columns", columns)
        # User request for SQL query
        sql_query = self.generate_sql_query(table_name, columns, user_request)
        #sql_query = "PRAGMA table_info('rdf_data');"
        # Print the generated SQL query
        self.DEBUG = True
        if self.DEBUG:
            print("Generated SQL Query:", sql_query)

        # Execute the SQL query on DuckDB
        results = self.execute_sql_query(sql_query=sql_query)

        # Print the results
        #print("Query Results:", results)
        if self.DEBUG:
            for row in results:
                print(row)
        
        answer = self.librarian(question, sql_query, results)
        answer = self.clean_answer(answer)
        return answer


