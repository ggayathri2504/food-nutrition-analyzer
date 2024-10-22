import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io


def resize_image(image, max_size=800):
    """Resize image while maintaining aspect ratio"""
    ratio = max_size / max(image.size)
    if ratio < 1:  # Only resize if the image is larger than max_size
        new_size = tuple([int(dim * ratio) for dim in image.size])
        return image.resize(new_size, Image.Resampling.LANCZOS)
    return image


def compress_image(image, quality=85):
    """Compress image to reduce file size"""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)
    return buffer


def encode_image(image_file):
    """Convert image to base64 with resizing and compression"""
    # Open image
    image = Image.open(image_file)

    # Convert to RGB if necessary
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Resize image
    resized_image = resize_image(image)

    # Compress image
    compressed_buffer = compress_image(resized_image)

    # Convert to base64
    return base64.b64encode(compressed_buffer.getvalue()).decode("utf-8")


def analyze_food_image(client, image_base64):
    system_prompt = """You are a nutrition expert. When presented with a food image, provide detailed nutritional information in the following format:

Calories: [number] kcal
Protein: [number] g
Fiber: [number] g
Carbohydrates: [number] g
Fat: [number] g
Main Ingredients: [list main ingredients]
Allergens: [list potential allergens]
Additional Notes: [any other relevant nutritional information]

Please be as precise as possible with the measurements."""

    #     content = f"""Here is a food image (in base64 format): {image_base64}

    # Please analyze this image and provide detailed nutritional information about the food item(s) shown."""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                },
                {
                    "type": "text",
                    "text": """Analyze this food image and provide detailed nutritional information in the following format:

            Calories: [number] kcal
            Protein: [number] g
            Fiber: [number] g
            Carbohydrates: [number] g
            Fat: [number] g
            Main Ingredients: [list main ingredients]
            Allergens: [list potential allergens]
            Additional Notes: [any other relevant nutritional information]

            Please be as precise as possible with the measurements.""",
                },
            ],
        }
    ]

    try:
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=messages,
            temperature=0.1,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing image: {str(e)}"


def main():
    st.set_page_config(page_title="Food Nutrition Analyzer", page_icon="🍽️")
    # Load and display the Groq logo
    logo_image = Image.open("groq-logo.png")  # Replace with your logo file path
    st.image(logo_image, width=200)

    st.title("🍽️ Food Nutrition Analyzer")
    st.write("Upload a photo of your food to get detailed nutritional information!")

    # Add custom CSS for better styling
    st.markdown(
        """
        <style>
        .stButton>button {
            width: 100%;
            height: 3em;
            margin-top: 1em;
        }
        .image-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 1em 0;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # API Key input with improved instructions
    with st.expander("ℹ️ API Key Instructions", expanded=False):
        st.markdown(
            """
        1. Go to [Groq's website](https://groq.com) and sign up for an account
        2. Generate an API key from your dashboard
        3. Copy and paste the key below
        """
        )

    api_key = st.text_input("Enter your Groq API Key", type="password")

    if api_key:
        client = Groq(api_key=api_key)

        # Add image settings
        st.sidebar.markdown("### Image Settings")
        max_size = st.sidebar.slider("Max Image Size (pixels)", 400, 1200, 800, 100)
        quality = st.sidebar.slider("Image Quality", 50, 100, 85, 5)

        # File uploader with clear instructions
        uploaded_file = st.file_uploader(
            "Choose a food image...",
            type=["jpg", "jpeg", "png"],
            help="Upload a clear, well-lit photo of your food",
        )

        if uploaded_file is not None:
            # Process and display images
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("### Original Image")
                original_image = Image.open(uploaded_file)
                st.image(original_image, use_column_width=True)
                st.info(f"Original Size: {original_image.size}")

            with col2:
                st.markdown("### Processed Image")
                # Process image with current settings
                processed_image = resize_image(original_image, max_size)
                st.image(processed_image, use_column_width=True)
                st.info(f"Processed Size: {processed_image.size}")

            # Analyze button and results
            if st.button("🔍 Analyze Nutrition"):
                with st.spinner("Analyzing your food..."):
                    # Convert image to base64 with current settings
                    processed_buffer = compress_image(processed_image, quality)
                    image_base64 = base64.b64encode(processed_buffer.getvalue()).decode(
                        "utf-8"
                    )

                    # Get analysis
                    analysis = analyze_food_image(client, image_base64)

                    # Display results in a nice format
                    st.markdown("### 📊 Nutritional Analysis")
                    st.write(analysis)

                    # Add disclaimer in a warning box
                    st.warning(
                        "⚠️ Note: These are estimated values and may vary from actual nutritional content. Please consult a professional nutritionist for accurate information."
                    )

    else:
        st.info("👆 Please enter your Groq API key to get started.")

    # Add footer with instructions in an expander
    with st.expander("📝 Tips for Best Results", expanded=False):
        st.markdown(
            """
        ### Image Guidelines:
        - Use well-lit, clear photos
        - Include the entire food item in the frame
        - Avoid blurry or dark images
        - Place food items on a plain background if possible
        - Include size reference when possible (e.g., plate, utensils)
        
        ### Image Settings:
        - Adjust the Max Image Size to balance quality and processing speed
        - Higher Image Quality means better detail but larger file size
        - For most food photos, the default settings work well
        """
        )

    # Add version info and credits
    st.markdown(
        """
    ---
    Made with ❤️ using Streamlit and Groq API | v1.1.0
    """
    )


if __name__ == "__main__":
    main()
