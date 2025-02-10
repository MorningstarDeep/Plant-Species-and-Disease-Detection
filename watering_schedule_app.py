import streamlit as st
import google.generativeai as genai
import pandas as pd

# Configure page settings
st.set_page_config(page_title="Water Schedule Generator")

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #1a237e;
        color: white;
    }
    .title {
        color: white;
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        padding: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Configure Gemini API
GOOGLE_API_KEY = ""

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-pro")
except Exception as e:
    st.error(f"Error configuring API: {str(e)}")
    model = None

def get_watering_schedule(plant_name):
    """Get watering schedule for a plant"""
    try:
        prompt = f"""
        Create a detailed watering schedule for {plant_name}.
        Format as a table with 4 rows (one for each season) with these columns:
        Season | Watering Frequency | Water Amount | Special Care Notes
        
        Example format:
        Spring|Every 3 days|250ml|Keep soil moist
        Summer|Daily|300ml|Water early morning
        Fall|Every 5 days|200ml|Check soil moisture
        Winter|Weekly|150ml|Reduce watering
        """
        
        response = model.generate_content(prompt)
        if response and hasattr(response, 'text'):
            st.write("Debug: Raw API Response")
            st.write(response.text)  # Display the raw response for debugging
            return response.text
        return None
        
    except Exception as e:
        st.error(f"Error generating content: {str(e)}")
        return None

def parse_schedule(text):
    """Parse the schedule text into a DataFrame"""
    if not text:
        return None
        
    try:
        lines = [line.strip() for line in text.split('\n') if '|' in line]
        data = []
        
        for line in lines:
            cells = [cell.strip() for cell in line.split('|')]
            if len(cells) == 4:
                data.append(cells)
                
        if data:
            return pd.DataFrame(
                data,
                columns=['Season', 'Watering Frequency', 'Water Amount', 'Special Care Notes']
            )
        return None
        
    except Exception as e:
        st.error(f"Error parsing schedule: {str(e)}")
        return None

def main():
    st.markdown('<h1 class="title">Water Schedule Generator</h1>', unsafe_allow_html=True)
    
    plant_name = st.text_input("Enter plant name:", placeholder="e.g., Peace Lily")
    
    if st.button("Generate Schedule"):
        if not plant_name:
            st.warning("Please enter a plant name.")
            return
            
        if not model:
            st.error("API configuration error. Please try again later.")
            return
            
        with st.spinner("Generating watering schedule..."):
            schedule_text = get_watering_schedule(plant_name)
            if schedule_text:
                df = parse_schedule(schedule_text)
                
                if df is not None:
                    st.markdown(f"### Watering Schedule for {plant_name}", unsafe_allow_html=True)
                    
                    # Display styled table
                    st.dataframe(
                        df,
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Add download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Schedule (CSV)",
                        data=csv,
                        file_name=f"{plant_name}_watering_schedule.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("This is the schedule for the plant you entered")
            else:
                st.error("Could not generate schedule. Please try again.")

    # Add helpful tips
    with st.expander("Tips for better results"):
        st.markdown("""
        - Use common names (e.g., 'Peace Lily') or scientific names (e.g., 'Spathiphyllum')
        - Be specific about the plant variety
        - The schedule is a general guide and may need adjustment based on your environment
        - Consider factors like humidity, temperature, and season
        """)

if __name__ == "__main__":
    main()
