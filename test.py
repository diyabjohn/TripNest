import google.generativeai as genai

genai.configure(api_key='AIzaSyAqr_xu6CcOPnTtt3Art-H1hT-jHBb2EFM')

def yo():
    # Create a descriptive prompt using the current hotel details
    prompt = f"Hello"

    # Generate a response using the Gemini model
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")
    response = model.generate_content(prompt)

    return response.text

print(yo())