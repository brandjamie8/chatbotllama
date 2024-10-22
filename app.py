import streamlit as st
import replicate
import os

# App title and configuration
st.set_page_config(page_title="🦙💬 LLaMA-2 7B Chatbot")

# Replicate Credentials and Sidebar
with st.sidebar:
    st.title('🦙💬 LLaMA-2 7B Chatbot')
    st.write('This chatbot is created using the open-source LLaMA-2 7B Chat model from Meta.')
    replicate_api = st.text_input('Enter Replicate API token:', type='password')
    if not (replicate_api.startswith('r8_') and len(replicate_api) == 40):
        st.warning('Please enter your credentials!', icon='⚠️')
    else:
        st.success('Proceed to entering your prompt message!', icon='👉')
    os.environ['REPLICATE_API_TOKEN'] = replicate_api

    st.subheader('Model Parameters')
    # Optionally retain model selection with a single option
    selected_model = st.selectbox('Choose a LLaMA-2 model', ['Meta LLaMA-2 7B Chat'], key='selected_model')
    if selected_model == 'Meta LLaMA-2 7B Chat':
        llm = 'meta/meta-llama-3.1-405b-instruct'  # Replace 'latest' with the actual version hash if available

    temperature = st.slider('Temperature', min_value=0.01, max_value=1.0, value=0.1, step=0.01)
    top_p = st.slider('Top P', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.slider('Max Length', min_value=20, max_value=80, value=50, step=5)
    st.markdown('📖 Learn how to build this app in this [blog](https://blog.streamlit.io/how-to-build-a-llama-2-chatbot/)!')

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function to generate LLaMA-2 7B Chat response with error handling
def generate_llama2_response(prompt_input, llm):
    try:
        string_dialogue = (
            "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. "
            "You only respond once as 'Assistant'.\n\n"
        )
        for dict_message in st.session_state.messages:
            if dict_message["role"] == "user":
                string_dialogue += f"User: {dict_message['content']}\n\n"
            else:
                string_dialogue += f"Assistant: {dict_message['content']}\n\n"
        
        output = replicate.run(
            llm, 
            input={
                "prompt": f"{string_dialogue} {prompt_input} Assistant: ",
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
            with st.spinner("Thinking..."):
                response = generate_llama2_response(prompt, llm)
                placeholder = st.empty()
                full_response = ''
                for item in response:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)

