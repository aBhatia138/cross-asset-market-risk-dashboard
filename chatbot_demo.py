import re
import streamlit as st
from src.data_loader import fetch_live_feed
from src.risk_metrics import calculate_metrics
from datetime import date, timedelta
import refinitiv.data as rd
from app import open_lseg_session
from src.marketmate import get_asset_snapshot, get_comparison_response, get_data_response, get_risk_response

#Page configuration
st.set_page_config(
    page_title="MarketMate | Rule-Based Chatbot",
    page_icon="🤖",
    layout="centered",
)

#Visual Styling
st.markdown(
    """
    <style>
        .stApp{
            background: linear-gradient(
                145deg,
                #0B1220 0%,
                #101B2D 55%,
                #0B1220 100%
            );
        }

        .block-container {
            max-width: 900px;
            padding-top: 2.5rem;
            padding-bottom: 3rem;
        }

        .hero {
            padding: 1.6rem;
            border: 1px solid rgba(145,161,103,0.22);
            border-radius: 20px;
            background: rgba(17,28,46,0.70);
            margin-bottom: 1.5rem;
        }

        .hero h1 {
            color: #91A1B7;
            margin-bottom: 0;
        }

        .status-pill {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            background: rgba(45,212,191,0.12);
            color: #5EEAD4;
            font-size: 0.8rem;
            border: 1px solid rgba(45,212,191,0.3);
        }

        [data-testid="stChatMessage"] {
            border: 1px solid rgba(145,161,183,0.13);
            border-radius: 16px;
            padding: 0.8rem 1rem;
            background: rgba(17,28,46,0.55);
        }

        [data-testid="stChatInput"] {
            border-radius: 14px;
        }

        div.stButton > button {
            border-radius: 12px;
            border: 1px solid rgba(45,212,191,0.25);
            background: rgba(17,28,46,0.75);
            color: #E5EDF7;
            transition: all 180ms ease;
        }

        div.stButton > button:hover {
            border-color: #2DD4BF;
            color: #5EEAD4;
        }

        .small-note {
            color: #91A1B7;
            font-size: 0.85rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

#Chatbot response logic
def get_bot_response(user_message: str) -> str:
    #Normalize the input to simplify matching
    message = user_message.lower().strip()

    #Extract words
    words = set(re.findall(r"\b[a-z]+\b",message))

    #Rule 1 - Empty input
    if not message:
        return "Please type a message so I can try to help you"

    #Rule 2 - Greetings
    if words.intersection({"hi","hello","hey","yo","greetings","wassup"}):
        return (
            "Hello! 👋 I'm MarketMate, your rule-based assistant. "
             "Ask me about volatility, returns, drawdown, or how I work."
        )

    #Rule 3 - Identity
    if "who are you" in message or "what are you" in message:
        return (
            "I'm MarketMate, a chatbot built with Python and Streamlit. "
            "I use predefined rules to respond to certain questions. "
            "I don't use an LLM or understand arbitrary questions yet."
        )

    #Rule 4 - Help
    if words.intersection({"help","topics","commands"}):
        return (
            "Here are some things you can ask me:\n\n"
            "- What is volatility?\n"
            "- Explain drawdown.\n"
            "- What is a return?\n"
            "- What is correlation?\n"
            "- How do you work?\n\n"
            "Try asking one of these in your own words!"
        )

    #Rule 5 - Volatility
    if "volatility" in words or "volatile" in words:
        return (
            "**Volatility** measures how much an asset's returns fluctuate "
            "over a period. Higher volatility generally indicates greater "
            "variability in returns.\n\n"
            "In a later version, I could explain the annualized volatility "
            "calculated by your market-risk dashboard."
        )

    #Rule 6 - Drawdown
    if "drawdown" in words:
        return (
            "**Drawdown** measures a decline from a previous peak in value. "
            "Maximum drawdown is the largest peak-to-trough decline over "
            "the selected period.\n\n"
            "It helps describe historical downside experienced during "
            "that period, but does not predict future losses."
        )

    #Rule 7 - Returns
    if "return" in words or "returns" in words:
        return (
            "**A return** measures how an asset's value changes between "
            "two observations. A simple price return is:\n\n"
            "Return = (Ending Price / Beginning Price) - 1\n\n"
            "For example, a move from 100 to 105 gives a return of 5%, "
            "before accounting for dividends, fees, or other adjustments."
        )

    #Rule 8 - Correlation
    if "correlation" in words or "correlated" in words or "corr" in words:
        return (
            "**Correlation** describes the strength and direction of a "
            "relationship between two variables.\n\n"
            "- +1: perfect positive linear correlation\n"
            "- 0: no linear correlation\n"
            "- -1: perfect negative linear correlation\n\n"
            "Correlation does not prove causation, and zero correlation "
            "does not rule out every kind of relationship."
        )

    #Rule 9 - Explain how the chatbot works
    if "work" in words or "built" in words or "function" in words:
        return (
            "I follow rules written in Python. I normalize your message, "
            "look for certain words, and return a predefined response.\n\n"
            "I don't learn from this conversation, call an AI API, or "
            "generate answers with an LLM."
        )

    #Rule 10 - Fallback
    return (
        "I'm not sure how to respond to that yet. 🤔\n\n"
        "I'm a rule-based chatbot, so I only recognize a limited set "
        "of topics. Try asking about volatility, returns, drawdown, "
        "or correlation — or type **help** to see the available topics."
    )

#Initialize conversation state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role":"assistant",
             "content": (
                "Welcome to **MarketMate**! 👋\n\n"
                "I'm your first rule-based chatbot. I can explain a few "
                "market-risk concepts and answer questions about how I work.\n\n"
                "Try asking: *What is volatility?*"
             ),
        }
    ]

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

#Header
st.markdown(
    """
    <div class="hero"> 
        <span class="status-pill">● RULE-BASED MODE</span>
        <h1>🤖 MarketMate</h1>
        <p>
            Your first conversational application.
            Built with Python and Streamlit - no AI model required (yet).
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

#Sidebar
with st.sidebar:
    st.title("MarketMate")
    st.caption("Stage 1: Learning Project")
    st.markdown("### What I can do")
    st.markdown(
        "- Explain basic risk concepts\n"
        "- Recognize selected keywords\n"
        "- Explain how this chatbot works"
    )

    st.divider()

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = [
            {
                "role":"assistant",
                "content":(
                    "Conversation cleared! 👋 "
                    "What would you like to explore?"
                ),
            }
        ]
        st.session_state.pending_prompt = None
        st.rerun()

    st.markdown("----")
    st.caption(
        "Stage 1 has no LLM, external API or market-data connection."
    )

st.markdown("### Try Asking")

suggestions = [
    "What is volatility?",
    "Explain drawdown",
    "What is correlation?"
]

suggestion_cols = st.columns(3)

for col, suggestion in zip(suggestion_cols,suggestions):
    with col:
        if st.button(
            suggestion,
            key=f"suggestion_{suggestion}",
            use_container_width=True        
        ):
            st.session_state.pending_prompt = suggestion


#Display conveersation history
for message in st.session_state.messages:
    avatar = "🧑" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"],avatar=avatar):
        st.markdown(message["content"])

#Accept input and type response
typed_prompt = st.chat_input(
    "Ask MarketMate something....",
)

#A suggested question takes priority when button is clicked
prompt = st.session_state.pending_prompt or typed_prompt
st.session_state.pending_prompt = None

if prompt:
    st.session_state.messages.append(
        {
            "role":"user",
            "content":prompt,
        }
    )

    with st.chat_message("user",avatar="🧑"):
        st.markdown(prompt)

    response = get_comparison_response(prompt)

    if response is None:
        response = get_risk_response(prompt)

    if response is None:
        response = get_data_response(prompt)

    if response is None:
        response = get_bot_response(prompt)

    #Save and display the assistant's response
    st.session_state.messages.append(
        {
            "role":"assistant",
            "content":response,
        }
    )

    with st.chat_message("assistant",avatar="🤖"):
        st.markdown(response)

st.divider()

st.markdown(
    """
    <p class="small-note">
        MarketMate · Stage 1 · Rule-based Python logic
        <br>
        Responses are predefined educational explanations, not live
        market analysis or investment advice.
    </p>
    """,
    unsafe_allow_html=True,
)

