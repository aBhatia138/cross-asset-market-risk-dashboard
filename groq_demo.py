import streamlit as st
from src.groq_client import generate_response

st.title("💬 MarketMate")
st.caption("Your AI-powered conversational assistant")

st.divider()

if "marketmate_messages" not in st.session_state:
    st.session_state.marketmate_messages = []

#Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#User input
prompt = st.chat_input("Ask me anything....")

if prompt:
    #Store and display the user's message
    st.session_state.messages.append({
        "role":"user",
        "content":prompt
    })

    with st.chat_message("assistant"):
        try:
            with st.spinner("MarketMate is thinking...."):
                #Exclude the current prompt from history
                #generate_response adds it separately
                history = st.session_state.messages[:-1]
                response = generate_response(
                    prompt,
                    conversation_history=history
                )

            st.markdown(response)

            #Save assistant response
            st.session_state.messages.append({
                "role":"assistant",
                "content":response
            })

        except Exception as e:
            st.error(
                "Sorry I couldn't generate a response."
                "Please try again."
            )

            print(
                "MarketMate error:",
                type(e).__name__,
                e
            )

#sidebar
with st.sidebar:
    st.subheader("MarketMate")

    st.write(
        "Standalone LLM chatbot powered by Groq"
    )

    st.divider()

    st.write(
        f"Messages exchanged: {len(st.session_state.messages)}"
    )

    if st.button("Clear conversation",use_container_width=True):
        st.session_state.messages = []
        st.rerun()