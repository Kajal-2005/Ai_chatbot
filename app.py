import streamlit as st
import requests
import json
import time
import logging

# Set page config FIRST
st.set_page_config(
    page_title="💰 Smart Bill Assistant",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS with visible text
# Add this to your existing CSS section
st.markdown("""
<style>
    /* Green action buttons */
    .stButton>button {
        background-color: #4CAF50 !important;
        color: #000000 !important;
        border: 1px solid #45a049 !important;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #45a049 !important;
        border-color: #398439 !important;
        transform: scale(1.02);
    }

    /* Feature card buttons */
    .bill-card h4 {
        color: #000000 !important;
        padding: 8px;
        background: #d8f5d8 !important;
        border-radius: 8px;
        display: inline-block;
    }

    /* Quick action buttons in sidebar */
    .st-emotion-cache-6qob1r .stButton>button {
        background-color: #81C784 !important;
        color: #000000 !important;
        border: 1px solid #66BB6A !important;
    }

    /* Error/warning buttons */
    .stAlert {
        background-color: #ffebee !important;
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! I'm your Bill Assistant 💸 How can I help manage your payments today?"
    }]

# Configure sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    with st.container():
        api_key = st.text_input("OpenRouter API Key", type="password", help="Required for AI functionality")
        st.markdown("[Get API Key](https://openrouter.ai/keys)")
        
        with st.expander("📘 Quick Start"):
            st.markdown("""
            1. Obtain API key from OpenRouter
            2. Enter key above
            3. Select AI model
            4. Start managing bills!
            """)
        
        model_name = st.selectbox(
            "🤖 AI Model",
            ( "google/palm-2-chat-bison"),
            index=0
        )
        
        with st.expander("⚡ Advanced"):
            temperature = st.slider("🧠 Response Style", 0.0, 1.0, 0.3,
                                  help="Precise ↔ Creative")
            max_retries = st.number_input("🔄 Max Retries", 1, 5, 2)
        
        st.markdown("### 🚀 Quick Actions")
        if st.button("🧹 Clear Chat", use_container_width=True):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Chat cleared! Ask me about bill management!"
            }]

# Main interface
st.title("📅 Smart Bill Reminder Assistant")
st.caption("Never miss a payment with AI-powered bill tracking and reminders")

# Feature cards
with st.container():
    cols = st.columns(4)
    features = [
        ("🔔 Reminders", "Payment due alerts"),
        ("📊 Analysis", "Spending patterns"),
        ("💳 Tracking", "Multiple payment methods"),
        ("📈 Tips", "Financial optimization")
    ]
    for col, (emoji, text) in zip(cols, features):
        col.markdown(
            f"""<div class='bill-card'>
                <h4 style='color: #000000 !important'>{emoji} {text}</h4>
            </div>""", 
            unsafe_allow_html=True
        )

# Chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about bill management..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    if not api_key:
        with st.chat_message("assistant"):
            st.error("🔑 API key required in sidebar settings")
            st.markdown("""
            <div style='background: #fff3f3; padding: 15px; border-radius: 10px; color: #000000 !important;'>
                <h4 style='color: #000000 !important;'>Get Started:</h4>
                <ol style='color: #000000 !important;'>
                    <li>Visit <a href="https://openrouter.ai/keys" style='color: #1976d2 !important;'>OpenRouter</a></li>
                    <li>Create account & get key</li>
                    <li>Enter key in sidebar</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        st.stop()

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        attempts = 0
        
        with st.spinner("Analyzing your query..."):
            time.sleep(0.3)
        
        while attempts < max_retries:
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://bill-assistant.streamlit.app",
                        "X-Title": "Bill Reminder AI"
                    },
                    json={
                        "model": model_name,
                        "messages": [{
                            "role": "system",
                            "content": f"""You are a financial assistant specializing in bill management. STRICT RULES:
1. Format responses clearly:
   - Payment Name
   - Due Date (MM/DD/YYYY)
   - Amount Due
   - Payment Methods
2. Include reminders 3 days before due dates
3. Highlight overdue payments in red
4. Suggest payment optimization strategies
5. Current date: {time.strftime("%m/%d/%Y")}
6. Use financial emojis: 💸💳📅⚠️✅
7. Never use markdown"""
                        }] + st.session_state.messages[-4:],
                        "temperature": temperature,
                        "response_format": {"type": "text"}
                    },
                    timeout=15
                )

                response.raise_for_status()
                data = response.json()
                raw_response = data['choices'][0]['message']['content']
                
                # Format response
                processed_response = raw_response
                formatting_cleaners = [
                    ("**", ""), ("```", ""), ("\\n", "\n"),
                    ("Due Date:", "<strong>Due Date:</strong>"),
                    ("Amount Due:", "<strong>Amount Due:</strong>")
                ]
                
                for pattern, replacement in formatting_cleaners:
                    processed_response = processed_response.replace(pattern, replacement)
                
                # Stream response
                lines = processed_response.split('\n')
                for line in lines:
                    words = line.split()
                    for word in words:
                        full_response += word + " "
                        response_placeholder.markdown(full_response + "▌")
                        time.sleep(0.03)
                    full_response += "\n"
                    response_placeholder.markdown(full_response + "▌")
                
                # Final formatting
                full_response = full_response.replace("OVERDUE", "<span style='color: #d32f2f'>OVERDUE</span>") \
                                           .replace("Due Soon", "<span style='color: #ffa000'>Due Soon</span>")
                
                response_placeholder.markdown(full_response, unsafe_allow_html=True)
                break
                
            except json.JSONDecodeError as e:
                logging.error(f"JSON Error: {str(e)}")
                attempts += 1
                if attempts == max_retries:
                    response_placeholder.error("⚠️ Processing error. Try:")
                    response_placeholder.markdown("""
                    <div style='background: #fff3f3; padding: 15px; border-radius: 10px; color: #000000 !important;'>
                        <h4 style='color: #000000 !important;'>💡 Help:</h4>
                        <ul style='color: #000000 !important;'>
                            <li>Rephrase your question</li>
                            <li>Check payment details format</li>
                            <li>Verify internet connection</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                response_placeholder.error(f"🌐 Network Error: {str(e)}")
                full_response = "Connection issue - please try again"
                break
                
            except Exception as e:
                logging.error(f"Error: {str(e)}")
                response_placeholder.error(f"❌ Unexpected error: {str(e)}")
                full_response = "Please try again"
                break

    st.session_state.messages.append({"role": "assistant", "content": full_response})
