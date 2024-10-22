import streamlit as st
import replicate
import os
import re

# App title and configuration
st.set_page_config(page_title="🦙💬 SQL Query Generator")

# Define your database schema here
DATABASE_SCHEMA = """
Table: users
- id (INT, Primary Key)
- name (VARCHAR)
- email (VARCHAR)
- signup_date (DATE)

Table: orders
- order_id (INT, Primary Key)
- user_id (INT, Foreign Key references users(id))
- product_id (INT)
- quantity (INT)
- order_date (DATE)

Table: products
- product_id (INT, Primary Key)
- product_name (VARCHAR)
- price (DECIMAL)
"""

# Replicate Credentials and Sidebar
with st.sidebar:
    st.title('🦙💬 SQL Query Generator')
    st.write('This tool converts natural language queries into SQL queries based on your database schema.')
    replicate_api = st.text_input('Enter Replicate API token:', type='password')
    if not (replicate_api.startswith('r8_') and len(replicate_api) == 40):
        st.warning('Please enter your credentials!', icon='⚠️')
    else:
        st.success('Proceed to entering your query!', icon='👉')
    os.environ['REPLICATE_API_TOKEN'] = replicate_api

    st.subheader('Model Parameters')
    selected_model = st.selectbox('Choose a LLaMA-2 model', ['Meta LLaMA-2 7B Chat'], key='selected_model')
    if selected_model == 'Meta LLaMA-2 7B Chat':
        llm = 'meta/meta-llama-3.1-405b-instruct'  # Replace with actual version if needed

    temperature = st.slider('Temperature', min_value=0.01, max_value=1.0, value=0.1, step=0.01)
    top_p = st.slider('Top P', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.slider('Max Length', min_value=20, max_value=200, value=100, step=10)
    st.markdown('📖 Learn how to build this app in this [blog](https://blog.streamlit.io/how-to-build-a-llama-2-chatbot/)!')

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome! Please enter your natural language query to generate an SQL statement."}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.code(message["content"], language='sql')
        else:
            st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "Welcome! Please enter your natural language query to generate an SQL statement."}]

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function to extract SQL from response
def extract_sql(response):
    match = re.search(r"(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER).+?;", response, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(0)
    else:
        return response  # Return as-is if no SQL keyword is found

# Function to generate SQL response with error handling
def generate_llama2_response(prompt_input, llm, schema):
    try:
        # Construct the prompt with instructions and schema
        string_dialogue = (
            "You are an SQL assistant. Given a natural language query and the database schema below, generate only the corresponding SQL query. Do not add any explanations or additional text.\n\n"
            f"Database Schema:\n{schema}\n\n"
            "User Query: "
        )
        string_dialogue += f"{prompt_input}\n\nSQL Query:"
        
        output = replicate.run(
            llm, 
            input={
                "prompt": string_dialogue,
                "temperature": temperature, 
                "top_p": top_p, 
                "max_length": max_length, 
                "repetition_penalty": 1
            }
        )
        return output
    except replicate.exceptions.ReplicateError as e:
        st.error(f"An error occurred while generating the response: {e}")
        return "I'm sorry, but I couldn't process your request at the moment."
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return "I'm sorry, something went wrong."

# User input and response generation
if prompt := st.chat_input(disabled=not (replicate_api.startswith('r8_') and len(replicate_api) == 40)):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Generating SQL query..."):
                response = generate_llama2_response(prompt, llm, DATABASE_SCHEMA)
                sql_query = extract_sql(response)
                placeholder = st.empty()
                placeholder.code(sql_query, language='sql')
        message = {"role": "assistant", "content": sql_query}
        st.session_state.messages.append(message)
