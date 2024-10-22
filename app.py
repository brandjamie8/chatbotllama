import streamlit as st
import replicate
import os
import re

# App title and configuration
st.set_page_config(page_title="💬 SQL Query Generator")

# Define the NHS SUS APC and OPA table schemas
DATABASE_SCHEMA = """
Table: apc
- UnitID (VARCHAR): Unique identifier for the NHS Trust.
- PatientID (VARCHAR): Unique identifier for the patient.
- EpisodeID (VARCHAR): Unique identifier for the patient episode.
- AdmissionDate (DATE): Date of admission.
- AdmissionType (VARCHAR): Type of admission (e.g., Elective, Emergency).
- MainDiagnosis (VARCHAR): Primary diagnosis code.
- SecondaryDiagnosis (VARCHAR): Secondary diagnosis codes.
- Procedure (VARCHAR): Procedure codes performed during the episode.
- DischargeDate (DATE): Date of discharge.
- LengthOfStay (INT): Total number of days admitted.
- DischargeStatus (VARCHAR): Status at discharge (e.g., Recovered, Transferred).
- Age (INT): Age of the patient at admission.
- Gender (VARCHAR): Gender of the patient.
- Ethnicity (VARCHAR): Ethnic group of the patient.
- DeprivationIndex (INT): Index of Multiple Deprivation score.
- AdmissionSource (VARCHAR): Source of admission (e.g., GP Referral, Accident & Emergency).
- ReadmissionFlag (BOOLEAN): Indicates if the patient was readmitted within 30 days.

Table: opa
- UnitID (VARCHAR): Unique identifier for the NHS Trust.
- PatientID (VARCHAR): Unique identifier for the patient.
- EpisodeID (VARCHAR): Unique identifier for the patient episode.
- AppointmentDate (DATE): Date of the outpatient appointment.
- Department (VARCHAR): Department where the appointment took place (e.g., Cardiology, Orthopedics).
- Procedure (VARCHAR): Procedure codes performed during the appointment.
- Outcome (VARCHAR): Outcome of the appointment (e.g., Attended, Did Not Attend).
- Age (INT): Age of the patient at the time of appointment.
- Gender (VARCHAR): Gender of the patient.
- Ethnicity (VARCHAR): Ethnic group of the patient.
- DeprivationIndex (INT): Index of Multiple Deprivation score.
- ReferralSource (VARCHAR): Source of referral (e.g., GP Referral, Self-Referral).
"""

# Replicate Credentials and Sidebar
with st.sidebar:
    replicate_api = st.text_input('Enter Replicate API token:', type='password')
    
    # Validate Replicate API Token
    if not (replicate_api.startswith('r8_') and len(replicate_api) == 40):
        st.warning('Please enter your Replicate API token.', icon='⚠️')
    else:
        st.success('API Token Verified. Proceed to enter your query.', icon='✅')
    os.environ['REPLICATE_API_TOKEN'] = replicate_api

    st.subheader('Model Parameters')
    llm = 'meta/meta-llama-3.1-405b-instruct'  # Replace with actual version if needed

    temperature = st.slider('Temperature', min_value=0.01, max_value=1.0, value=0.1, step=0.01)
    top_p = st.slider('Top P', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.slider('Max Length', min_value=20, max_value=200, value=100, step=10)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Please enter your natural language query to generate an SQL statement."}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.code(message["content"], language='sql')
        else:
            st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "Please enter your natural language query to generate an SQL statement."}]

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function to extract SQL from response
def extract_sql(response):
    if isinstance(response, list):
        response = ''.join(response)  # Concatenate list into string if necessary
    elif not isinstance(response, str):
        response = str(response)  # Convert to string if not already

    # Regular expression to extract SQL queries
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
            "You are an SQL assistant specialized in NHS SUS APC and OPA databases. Given a natural language query and the database schema below, generate only the corresponding SQL query. Ensure the query adheres to standard SQL syntax and utilizes the appropriate tables and relationships. Do not add any explanations or additional text.\n\n"
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
        return output  # Ensure this is a string
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

