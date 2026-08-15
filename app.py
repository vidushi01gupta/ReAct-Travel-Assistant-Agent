import streamlit as st
import uuid

from travel_assistant import travel_assistant

# page config
st.set_page_config(
    page_title="AI Travel Assistant",
    page_icon="✈️",
    layout="wide"
)

# Store all conversations
if "conversations" not in st.session_state:
    st.session_state.conversations = {}


# active conversation
if "active_conversation" not in st.session_state:
    st.session_state.active_conversation = None

# first conversation
if st.session_state.active_conversation is None:
    conversation_id = str(uuid.uuid4())
    st.session_state.conversations[conversation_id] = {"title": "New Conversation","thread_id": conversation_id,"messages": []}
    st.session_state.active_conversation = conversation_id

active_id = st.session_state.active_conversation
conversation = st.session_state.conversations[active_id]
messages = conversation["messages"]

# sidebar
with st.sidebar:
    st.title("✈️ Travel Assistant")
    if st.button("＋ New Conversation",use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.conversations[new_id] = {
            "title": "New Conversation",
            "thread_id": new_id,
            "messages": []
        }

        st.session_state.active_conversation = new_id
        st.rerun()


    st.divider()

    # conversations

    st.subheader("Conversations")
    if len(st.session_state.conversations) == 0:
        st.caption("No conversations yet.")

    else:
        conversation_items = list(st.session_state.conversations.items())
        conversation_items.reverse()
        for conversation_id, conv in conversation_items:
            title = conv.get(
                "title",
                "New Conversation"
            )

            if conversation_id == st.session_state.active_conversation:
                button_label = f"{title}"

            else:
                button_label = f"{title}"


            if st.button(button_label,key=f"conversation_{conversation_id}",use_container_width=True):
                st.session_state.active_conversation = conversation_id
                st.rerun()

# main page

st.title("✈️ AI Travel Assistant")
st.write("Plan your trip using real-time flights, trains, buses, hotels and weather.")

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# chat input
user_input = st.chat_input("Ask me to plan your trip...")

if user_input:
    user_input = user_input.strip()
    if not user_input:
        st.stop()

    if conversation["title"] == "New Conversation":

        title = user_input.replace("\n", " ")
        # Limit title length
        if len(title) > 40:
            title = title[:40] + "..."

        conversation["title"] = title

    # save mesaage

    conversation["messages"].append({"role": "user","content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

# langgraph running
    with st.chat_message("assistant"):
        with st.spinner("✈️ Planning your trip..."):
            try:

                final_message = travel_assistant(user_input,conversation["thread_id"])

                if final_message is None:
                    final_message = ("Sorry, I couldn't generate a response.")

                elif not isinstance(final_message, str):
                    final_message = str(final_message)

            except Exception as e:
                final_message = (
                    "Something went wrong.\n\n"
                    f"`{str(e)}`"
                )

        st.markdown(final_message)

    conversation["messages"].append({
        "role": "assistant",
        "content": final_message
    })

    st.session_state.conversations[
        active_id
    ] = conversation