import streamlit as st
from PIL import Image
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel(model_name="gemini-1.5-pro")

st.set_page_config(page_title="FitAI", layout="centered")
st.title("FitAI")

st.write(
    "Upload or take a photo. We will analyze your photo and provide you with a suitable fitness program as well as possible diet.")

if 'weight_data' not in st.session_state:
    st.session_state.weight_data = []


def add_weight(weight):
    st.session_state.weight_data.append({
        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Weight': weight
    })


# ======= Weight Input Section =======
st.header("Track Your Weight")

with st.form(key='weight_form'):
    weight_input = st.number_input("Enter your current weight (kg):", min_value=0.0, format="%.1f")
    submit_button = st.form_submit_button(label='Add Weight')

if submit_button:
    if weight_input > 0:
        add_weight(weight_input)
        st.success("Weight added successfully!")
    else:
        st.error("Please enter a valid weight.")

# ======= Photo Upload Section =======
col1, col2 = st.columns([1, 1], gap="small")

with col1:
    uploaded_file = st.file_uploader("Upload", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

with col2:
    user_photo = st.camera_input("Take a photo")
if uploaded_file is not None:
    image = Image.open(uploaded_file)
elif user_photo is not None:
    image = Image.open(user_photo)
else:
    image = Image.new('RGB', (400, 200), (200, 200, 200))  # Placeholder

st.image(image, caption="Your uploaded image", use_column_width=True)


# ======= Prepare Weight Data for Prompt =======
def prepare_weight_info(weight_data):
    if not weight_data:
        return "No weight data available."
    else:
        sorted_data = sorted(weight_data, key=lambda x: datetime.strptime(x['Date'], "%Y-%m-%d %H:%M:%S"))
        previous_weight = sorted_data[-2]['Weight'] if len(sorted_data) >= 2 else "No previous weight recorded."
        current_weight = sorted_data[-1]['Weight']
        weight_info = f"**Previous Weight:** {previous_weight} kg\n\n**Current Weight:** {current_weight} kg"
        return weight_info


weight_info = prepare_weight_info(st.session_state.weight_data)

# ======= Define the Prompt =======
prompt = f"""
You are a fitness and nutrition expert. Given the image of a person's body shape and their weight history, please:
1. Analyze their body composition briefly.
2. Propose a beginner-friendly fitness schedule (e.g., exercises, sets, reps, weekly schedule).
3. Suggest a balanced dietary approach.
4. Consider the user's weight change over time in your analysis.
5. Present all information in Markdown format with:
   - Headings (e.g., ## Overview, ## Recommended Exercises, ## Dietary Guidelines)
   - Bullet points for lists
   - Short but clear explanations
6. Keep in mind that this is a starting point for someone looking to improve general health and fitness.

**Weight Information:**
{weight_info}

If the image is not available or not analyzable, provide generic advice as above.
"""

# ======= Generate Content Based on the Image and Weight =======
try:
    if uploaded_file is not None or user_photo is not None:
        response = model.generate_content([prompt, image])
    else:
        response = model.generate_content([prompt])

    analysis_md = response if isinstance(response, str) else response.text
except Exception as e:
    analysis_md = f"An error occurred: {e}"

# ======= Create Tabs for Displaying Information =======
tab1, tab2 = st.tabs(["Your progress", "Our analysis"])

with tab1:
    st.subheader("The Weight")

    if st.session_state.weight_data:
        df_weight = pd.DataFrame(st.session_state.weight_data)
        df_weight['Date'] = pd.to_datetime(df_weight['Date'])
        df_weight = df_weight.sort_values('Date')

        st.line_chart(df_weight.set_index('Date')['Weight'])

        st.dataframe(df_weight)
    else:
        st.write("No weight data available. Please add your weight to track your progress.")

    st.subheader("Advice")
    if uploaded_file is not None or user_photo is not None:
        st.write(
            "Your current weight has been recorded. "
            "Please continue uploading images or tracking metrics to get personalized feedback."
        )
    else:
        st.write("Please upload an image to receive personalized advice.")

with tab2:
    st.subheader("Recommended Schedule & Diet")
    st.markdown(analysis_md)