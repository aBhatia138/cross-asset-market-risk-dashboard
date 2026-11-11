from src.marketmate_visualizations import (
    render_rolling_volatility,
    render_correlation_heatmap,
    render_stress_analysis,
)

import streamlit as st
from src.groq_client import generate_response
import traceback

def render_tool_visualizations(tool_results):
    # Render visualisations based on the tools
    # executed during the current MarketMate response.

    if not tool_results:
        return 

    for result in tool_results:

        if not isinstance(result, dict):
            continue

        if not result.get("success"):
            continue

        tool_name = result.get("tool")

        if tool_name == "get_historical_volatility":
            render_rolling_volatility(result)

        elif tool_name == "get_cross_asset_correlations":
            render_correlation_heatmap(result)

        elif tool_name == "get_stress_regime_analysis":
            render_stress_analysis(result)

def render_chatbot(dashboard_context=None):

    st.markdown("## 💬 MarketMate")
    st.caption("Your AI-powered financial market assistant")

    #Initialize an independent conversation history
    if "marketmate_messages" not in st.session_state:
        st.session_state.marketmate_messages = []

    messages = st.session_state.marketmate_messages

    #Clear conversation control
    col1, col2 = st.columns([4,1])

    with col1:
        st.caption(
            f"Messages exchanged: {len(messages)}"
        )

    with col2:
        if st.button(
            "Clear Chat",
            key="marketmate_clear_chat",
            use_container_width=True
        ):
            st.session_state.marketmate_messages = []
            st.rerun()

    st.divider()

    #Display previous messages
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                render_tool_visualizations(
                    message.get("tool_results", [])
                )

    prompt = st.chat_input(
        "Ask MarketMate about financial markets....",
        key="marketmate_chat_input"
    )

    if prompt:
        #Preserve the previous conversation before adding the new question
        history = messages.copy()

        #Display and temporarily store the user's question
        messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        #Generate the assistant's response
        with st.chat_message("assistant"):

            try:

                with st.spinner("MarketMate is thinking...."):

                    response = generate_response(
                        prompt,
                        conversation_history=history,
                        dashboard_context=dashboard_context,
                        include_tool_results=True
                    )

                answer = response["answer"]
                tool_results = response.get("tool_results", [])

                st.markdown(answer)

                render_tool_visualizations(tool_results)

                messages.append({
                    "role": "assistant",
                    "content": answer,
                    "tool_results": tool_results
                })

            # except Exception as e:
            #     st.error("Sorry, I couldn't generate a reponse")
            #     print(f"MarketMate error: {type(e).__name__,e}")

            except Exception as e:
                traceback.print_exc()
                st.error(f"MarketMate error: {e}")

                