import streamlit as st
from PIL import Image
import io
from dotenv import load_dotenv
import os
import requests
import json
import google.generativeai as genai
import pandas as pd

# Set page configuration with desired title and layout
st.set_page_config(page_title="Cultivate.me", page_icon="🌱", layout='wide')

# Custom CSS with dark green background and centered main heading
st.markdown("""
<style>
/* Main background - solid dark green */
.stApp {
    background-color: #1a331a;  /* Dark green */
}

/* Style for main heading */
.main-heading {
    color: white;
    font-family: 'Garamond', serif;
    text-align: center;
    padding: 20px;
    margin: 20px auto;
    border: 2px solid white;
    border-radius: 10px;
    width: fit-content;
    background-color: rgba(255, 255, 255, 0.1);
}

/* Style for other headers */
h2, h3, h4, h5, h6 {
    color: white;
    font-family: 'Garamond', serif;
    text-align: left;
}

/* Style for text elements */
p, li {
    color: white !important;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

/* Style for buttons */
.stButton>button {
    color: white;
    background-color: #2d5a2d;
    border: none;
    border-radius: 5px;
    padding: 10px 24px;
    margin: 10px 0;
    cursor: pointer;
    font-weight: bold;
}

/* Left-align text in disease details */
.stMarkdown {
    text-align: left;
    color: white;
}

</style>
""", unsafe_allow_html=True)

# Main heading with custom styling
st.markdown('<h1 class="main-heading">Cultivate.me</h1>', unsafe_allow_html=True)

# Load environment variables and configure APIs
load_dotenv()
PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY", "2b10jKEmElxFcLX83qFegLPxf")
PLANTID_API_KEY = "LN0VDf6CqrSrhsZitOfTmBLtbik2bJi96op6bLlJY7WSrWCS77"
PLANTNET_API_URL = "https://my-api.plantnet.org/v2/identify/all"
PLANTID_API_URL = "https://plant.id/api/v3/identification"

# Initialize session state
if 'identified_species' not in st.session_state:
    st.session_state.identified_species = None
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'show_disease_button' not in st.session_state:
    st.session_state.show_disease_button = False

def process_image(image):
    # Convert the image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # Prepare the API request
    params = {
        'api-key': PLANTNET_API_KEY,
    }

    files = [
        ('images', ('image.png', img_byte_arr, 'image/png'))
    ]

    try:
        response = requests.post(PLANTNET_API_URL, params=params, files=files)
        if response.status_code == 200:
            result = response.json()
            st.session_state.show_disease_button = True
            return result
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def display_results(results):
    if results and 'results' in results:
        st.success("Image processed successfully!")
        st.subheader("Species Identification Results:")
        
        # Store the first result for disease identification
        if results['results']:
            st.session_state.identified_species = results['results'][0]['species']['scientificName']
        
        for idx, result in enumerate(results['results'][:3], 1):
            species = result['species']
            score = result['score']
            common_names = species.get('commonNames', ['No common name available'])
            
            with st.expander(f"Match {idx}: {species['scientificName']} ({score:.2%} confidence)"):
                st.write(f"Common Names: {', '.join(common_names)}")
                if 'genus' in species:
                    st.write(f"Genus: {species['genus']['scientificName']}")
                if 'family' in species:
                    st.write(f"Family: {species['family']['scientificName']}")

def process_image_health(image):
    """Process image for health/disease detection using Plant.id API"""
    # Convert the image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # Prepare the request data
    files = {
        'images': ('image.png', img_byte_arr, 'image/png')
    }

    data = {
        'api_key': PLANTID_API_KEY,
        'health': 'only'  # Only get health assessment
    }

    try:
        response = requests.post(PLANTID_API_URL, files=files, data=data)
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        else:
            st.error(f"Health API Error: {response.status_code}")
            st.error(f"Error message: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error processing health check: {str(e)}")
        return None

def display_health_results(results):
    """Display health/disease analysis results from Plant.id API in a readable format"""
    if results and 'result' in results:
        st.markdown("## Plant Health Analysis Results", unsafe_allow_html=True)
        
        # Display if it's a plant
        is_plant = results['result'].get('is_plant', {}).get('binary', False)
        plant_confidence = results['result'].get('is_plant', {}).get('probability', 0) * 100
        st.markdown(f"**Image contains a plant:** True ({plant_confidence:.2f}% confidence)", unsafe_allow_html=True)
        
        # Modified health status logic
        has_diseases = False
        if 'disease' in results['result'] and 'suggestions' in results['result']['disease']:
            for suggestion in results['result']['disease']['suggestions']:
                if suggestion.get('probability', 0) > 0.3:  # 30% threshold for considering it a disease
                    has_diseases = True
                    break
        
        health_status = "Unhealthy" if has_diseases else "Healthy"
        status_color = "🔴" if has_diseases else "🟢"
        st.write(f"### Overall Status: {status_color} {health_status}")
        
        # Display disease/issue information
        if 'disease' in results['result']:
            st.write("### Detected Issues:")
            
            for suggestion in results['result']['disease']['suggestions']:
                confidence = suggestion.get('probability', 0) * 100
                name = suggestion.get('name', 'Unknown').title()
                
                if confidence > 10:  # Only show issues with >10% probability
                    with st.expander(f"{name} ({confidence:.2f}% probability)"):
                        # Add recommendations based on the issue type
                        st.write("#### Recommendations:")
                        if 'water' in name.lower():
                            if 'excess' in name.lower():
                                st.write("- Reduce watering frequency")
                                st.write("- Improve drainage")
                                st.write("- Check for proper soil mixture")
                            else:
                                st.write("- Increase watering frequency")
                                st.write("- Check soil moisture regularly")
                                st.write("- Consider humidity levels")
                        
                        elif 'light' in name.lower():
                            if 'excess' in name.lower():
                                st.write("- Move plant to a more shaded area")
                                st.write("- Use sheer curtains or blinds")
                                st.write("- Monitor leaf burn")
                            else:
                                st.write("- Move plant to a brighter location")
                                st.write("- Consider artificial lighting")
                                st.write("- Rotate plant regularly")
                        
                        elif 'mechanical' in name.lower():
                            st.write("- Protect plant from physical damage")
                            st.write("- Trim damaged areas carefully")
                            st.write("- Support stems if needed")
                            st.write("- Keep away from high traffic areas")
                        
                        elif 'fungi' in name.lower():
                            st.write("- Improve air circulation")
                            st.write("- Reduce humidity")
                            st.write("- Consider fungicide treatment")
                            st.write("- Remove affected leaves")

        # Add a summary of actions
        st.write("### Summary of Actions Needed:")
        top_issues = sorted(
            results['result']['disease']['suggestions'], 
            key=lambda x: x['probability'], 
            reverse=True
        )[:3]
        
        for issue in top_issues:
            if issue['probability'] > 0.3:  # Only show significant issues
                st.write(f"**Priority Issue: {issue['name']}**")
                st.write("Take immediate action to address this concern.")
                
        # Display analysis metadata in collapsible section
        with st.expander("Analysis Details"):
            st.write(f"Analysis Status: {results.get('status', 'N/A')}")
            st.write(f"Model Version: {results.get('model_version', 'N/A')}")
            if 'completed' in results and 'created' in results:
                analysis_time = results['completed'] - results['created']
                st.write(f"Analysis Time: {analysis_time:.2f} seconds")
    else:
        st.warning("No health analysis results available.")

def main():
    st.title("Cultivate.me")
    st.markdown('<p class="subheader">Upload a plant image for identification and health analysis</p>', 
                unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.session_state.current_image = image
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Identify Plant"):
                with st.spinner("Processing image..."):
                    results = process_image(image)
                    if results:
                        display_results(results)
                        st.session_state.show_disease_button = True
        
        with col2:
            if st.session_state.show_disease_button:
                if st.button("Check Plant Health"):
                    with st.spinner("Analyzing plant health..."):
                        health_results = process_image_health(image)
                        if health_results:
                            display_health_results(health_results)
                            
                            # Add chatbot redirect section after health results
                            st.markdown("---")
                            st.markdown("""
                            <div style="text-align: center; background-color: rgba(255, 255, 255, 0.1); 
                                      padding: 20px; border-radius: 10px; margin-top: 20px;">
                                <h3 style="color: white;">Have more questions about your plant?</h3>
                                <a href="http://localhost:8502" target="_blank" style="
                                    display: inline-block;
                                    text-decoration: none;
                                    color: white;
                                    background-color: #2d5a2d;
                                    padding: 10px 20px;
                                    border-radius: 5px;
                                    font-weight: bold;
                                    margin-top: 10px;
                                    transition: background-color 0.3s;">
                                    Chat with our Plant Expert Bot 🌿
                                </a>
                            </div>
                            """, unsafe_allow_html=True)

    # Link to the Watering Schedule App
    st.markdown(
        f'<a href="http://localhost:8503" target="_blank"><button style="color: white; background-color: #4CAF50; border: none; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer;">Open Watering Schedule App</button></a>', 
        unsafe_allow_html=True
    )

    st.markdown("### How to use:")
    st.markdown("1. Upload a clear plant image using the file uploader above.")
    st.markdown("2. Click the 'Identify Plant' button to analyze the species.")
    st.markdown("3. After species identification, click 'Check Plant Health' to detect any health issues.")
    st.markdown("4. For best results, use well-lit, focused images of plant organs (leaves, flowers, fruits, etc.)")
    st.markdown("5. Have more questions? Try our Plant Expert Chatbot for detailed information!")

if __name__ == "__main__":
    main()
