import streamlit as st
import os
from PIL import Image, ImageOps
import google.generativeai as genai
import re
import uuid

st.set_page_config(page_title="AI Wardrobe Assistant", layout="wide")

# Load environment variables
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

@st.cache_resource
def initialize_gemini_model():
    return genai.GenerativeModel("gemini-1.5-flash")

def input_images_setup(uploaded_files):
    image_parts = []
    for file in uploaded_files:
        bytes_data = file.getvalue()
        image_parts.append({
            "mime_type": file.type,
            "data": bytes_data,
        })
    return image_parts

def get_gemini_response(images, user_prompt, memory):
    base_prompt = """
You are a GEN-Z friendly fashion stylist. Based on the uploaded wardrobe images, respond to the user's fashion-related request.

RULES:
- Be casual and helpful like a fashion-savvy bestie.
- ONLY recommend clothes from the uploaded images.
- NEVER imagine or create outfits that are not in the uploaded set.
- If matching images are found, return the image indices (starting from 1) and give 2-3 lines of fun styling advice.
- If the query is general or not about clothes, just answer conversationally.
- If nothing matches, say it honestly in a kind way.
"""

    full_convo = base_prompt + "\n\nConversation History:\n"
    for turn in memory:
        role = "User" if turn["role"] == "user" else "Stylist"
        full_convo += f"{role}: {turn['content']}\n"
    full_convo += f"User: {user_prompt}\nStylist:"

    model = initialize_gemini_model()
    response = model.generate_content(images + [full_convo]) if images else model.generate_content(full_convo)
    return response.text

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Wardrobe Chat", "Laundry Basket"])

if "wardrobe_messages" not in st.session_state:
    st.session_state.wardrobe_messages = []

if "all_uploaded_images" not in st.session_state:
    st.session_state.all_uploaded_images = {}

if "laundry_basket" not in st.session_state:
    st.session_state.laundry_basket = {}

if "confirmed_keys" not in st.session_state:
    st.session_state.confirmed_keys = []

if page == "Wardrobe Chat":
    st.title("👗 AI Wardrobe Assistant")
    st.markdown("Upload your outfits and chat with a GEN-Z fashion stylist!")
    st.markdown("---")
    st.markdown(
    """
    <div style='text-align: center;'>
        Developed by <strong>Shreya Dhurde</strong> today ✨ <br>
        <a href='https://www.linkedin.com/in/shreya-dhurde/' target='_blank'>🔗 Connect on LinkedIn</a>
    </div>
    """,
    unsafe_allow_html=True
)

    uploaded_files = st.sidebar.file_uploader("Choose clothing images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="wardrobe_uploader")

    if uploaded_files:
        for file in uploaded_files:
            uid = str(uuid.uuid4())
            st.session_state.all_uploaded_images[uid] = {
                "file": file,
                "name": file.name
            }

    available_images = {uid: data for uid, data in st.session_state.all_uploaded_images.items() if uid not in st.session_state.laundry_basket}
    if available_images:
        st.subheader("📂 Available Clothes")
        cols = st.columns(4)
        for i, (uid, data) in enumerate(available_images.items()):
            img = Image.open(data["file"])
            square_img = ImageOps.fit(img, (200, 200), method=Image.BICUBIC)
            cols[i % 4].image(square_img, caption=f"{i+1}: {data['name']}", use_column_width=False)

    for msg in st.session_state.wardrobe_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_prompt = st.chat_input("Ask anything about your wardrobe 👗💬")
    if user_prompt:
        with st.chat_message("user"):
            st.markdown(user_prompt)
        st.session_state.wardrobe_messages.append({"role": "user", "content": user_prompt})

        image_data = input_images_setup([data["file"] for data in available_images.values()])

        with st.chat_message("assistant"):
            st.markdown("🔍 Thinking about your look...")

        response_text = get_gemini_response(image_data, user_prompt, st.session_state.wardrobe_messages)

        indices = re.findall(r"\d+", response_text)
        valid_indices = [int(i) - 1 for i in indices if i.isdigit() and 0 <= int(i) - 1 < len(available_images)]
        image_keys = list(available_images.keys())
        confirmed_keys = [image_keys[i] for i in valid_indices]
        st.session_state.confirmed_keys = confirmed_keys

        with st.chat_message("assistant"):
            if confirmed_keys:
                st.markdown("### 🔥 Your Lookbook Recommendations:")
                rec_cols = st.columns(3)
                for i, key in enumerate(confirmed_keys):
                    file = st.session_state.all_uploaded_images[key]["file"]
                    square_img = ImageOps.fit(Image.open(file), (200, 200), method=Image.BICUBIC)
                    rec_cols[i % 3].image(square_img, caption=st.session_state.all_uploaded_images[key]["name"], use_column_width=False)

            st.markdown("💬 " + response_text.strip())

        st.session_state.wardrobe_messages.append({"role": "assistant", "content": response_text.strip()})

    if st.session_state.confirmed_keys:
        if st.button("✅ Confirm Outfit"):
            for key in st.session_state.confirmed_keys:
                if key not in st.session_state.laundry_basket:
                    st.session_state.laundry_basket[key] = st.session_state.all_uploaded_images[key]
            st.success("Outfit confirmed and copied to laundry basket!")

elif page == "Laundry Basket":
    st.title("🧺 Laundry Basket")
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center;'>
        Developed by <strong>Shreya Dhurde</strong> today ✨ <br>
        <a href='https://www.linkedin.com/in/shreya-dhurde/' target='_blank'>🔗 Connect on LinkedIn</a>
    </div>
    """,
    unsafe_allow_html=True
)

    if st.session_state.laundry_basket:
        st.subheader("🧼 Outfits you've already worn:")
        cols = st.columns(3)
        for i, (uid, data) in enumerate(st.session_state.laundry_basket.items()):
            img = Image.open(data["file"])
            square_img = ImageOps.fit(img, (200, 200), method=Image.BICUBIC)
            cols[i % 3].image(square_img, caption=data["name"], use_column_width=False)

        if st.button("♻️ Clear Laundry Basket"):
            for key in list(st.session_state.laundry_basket.keys()):
                del st.session_state.laundry_basket[key]
            st.success("Laundry basket cleared! Outfits are now back in your wardrobe.")
    else:
        st.info("No outfits in the laundry basket yet.")
