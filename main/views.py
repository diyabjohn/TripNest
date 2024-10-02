# views.py
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import requests

from .models import Hotel, Booking
from .forms import SignUpForm, LoginForm
import google.generativeai as genai
from hotel.settings import GEMINI_API_KEY
from django.core.serializers import serialize

# View for the home page
def home(request):
    # Fetch popular hotels or all hotels
    hotels = Hotel.objects.all()

    # If the user is authenticated, generate recommendations (placeholder for actual ML model)
    recommendations = []
    if request.user.is_authenticated:
        # For now, we can provide some random recommendations or use some placeholder logic
        recommendations = hotels[:5]  # Replace with actual recommendations from your model

    context = {
        'hotels': hotels,
        'recommendations': recommendations,
    }
    return render(request, 'home.html', context)

# View for user login
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Redirect to dashboard on successful login
            else:
                return HttpResponse('Invalid login details')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# View for user signup
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log in the user after sign-up
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

# View for user logout
def logout_view(request):
    logout(request)
    return redirect('home')

# Dashboard view, only accessible for logged-in users
@login_required
def dashboard(request):
    # Fetch user-specific preferences, bookings, and recommendations
    bookings = Booking.objects.filter(user=request.user)
    recommendations = Hotel.objects.all()[:5]  # Placeholder for actual recommendations
    hotels = Hotel.objects.all()
    hotel_data = [
        {
            'name': hotel.name,
            'latitude': hotel.latitude,
            'longitude': hotel.longitude
        }
        for hotel in hotels
    ]
    context = {
        'bookings': bookings,
        'recommendations': recommendations,
        'hotel_data': hotel_data,
    }
    return render(request, 'dashboard.html', context)


@login_required
def book_hotel(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)

    # Check if a booking already exists for this hotel and user
    existing_booking = Booking.objects.filter(user=request.user, hotel=hotel).first()
    if existing_booking:
        return HttpResponse("You have already booked this hotel.")  # Simple message; can be replaced with a better UI

    # Create a new booking for the logged-in user
    new_booking = Booking(user=request.user, hotel=hotel)
    new_booking.save()

    # Redirect to the dashboard after successful booking
    return redirect('dashboard')


genai.configure(api_key=GEMINI_API_KEY)
# Function to get recommendations using the Gemini API with location priority
# Function to get recommendations based on location (using text-based matching) and Gemini API
def get_hotel_recommendations(current_hotel, all_hotels):
    # Create a descriptive prompt using the current hotel details, emphasizing location
    prompt = f"I am currently looking at a hotel named '{current_hotel.name}' located at {current_hotel.location}. " \
             f"The hotel offers amenities like {current_hotel.amenities}. Please recommend hotels in the same or nearby location with similar amenities from the following list:\n"

    # Append all hotel details to the prompt for context
    for hotel in all_hotels:
        prompt += f"- {hotel.name} located at {hotel.location} with amenities: {hotel.amenities}\n"

    # Generate a response using the Gemini model
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content(prompt)

    # Parse the AI response to extract hotel names
    recommended_hotel_names = response.text.split("\n")

    # Filter recommended hotels based on location similarity (case-insensitive)
    recommended_hotels = [
        hotel for hotel in all_hotels 
        if hotel.name in recommended_hotel_names and hotel.location.lower() == current_hotel.location.lower()
    ]

    return recommended_hotels

# View to display detailed hotel information along with recommendations
def hotel_detail(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)
    all_hotels = Hotel.objects.all()  # Fetch all hotels for generating recommendations

    # Get AI-based recommendations for similar hotels based on location
    similar_hotels = get_hotel_recommendations(hotel, all_hotels)

    context = {
        'hotel': hotel,
        'similar_hotels': similar_hotels,  # Pass the recommendations to the template
    }
    return render(request, 'hotel_detail.html', context)


def search_view(request):
    query = request.GET.get('q')
    if query:
        hotels = Hotel.objects.filter(location__icontains=query)
    else:
        hotels = Hotel.objects.all()
    
    context = {
        'hotels': hotels,
        'query': query,
    }
    return render(request, 'search_results.html', context)


# Replace with your API key and URL
API_KEY = 'AIzaSyBUhZyUBuA7_vajddWHEqLQGrN8v2_MJFM'
API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent'

# Define predefined responses for the chatbot
PREDEFINED_RESPONSES = {
    'hello': 'Hi there! How can I assist you today?',
    'bye': 'Goodbye! Have a great day!',
    # Add more predefined responses as needed
}

def chatbot(request):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        conversation_history = request.session.get('conversation_history', [])

        # Append user message to the conversation history
        conversation_history.append(f"input: {user_message}")
        bot_reply = PREDEFINED_RESPONSES.get(user_message.lower(), None)  # Case insensitive match

        if not bot_reply:
            # Make a request to the Google API if the message is not predefined
            headers = {'Content-Type': 'application/json'}
            messages = [{'text': message} for message in conversation_history]

            data = {'contents': [{'parts': messages}]}

            try:
                response = requests.post(f'{API_URL}?key={API_KEY}', headers=headers, json=data)
                response.raise_for_status()
                api_response = response.json()
                bot_reply = api_response['candidates'][0]['content']['parts'][0]['text']
                bot_reply = '. '.join(bot_reply.split('. ')[:3])  # Limit response to 3 sentences
            except requests.RequestException as e:
                print(f"API request error: {e}")
                bot_reply = 'Sorry, there was an error processing your request.'

        # Append bot reply to conversation history
        conversation_history.append(f"output: {bot_reply}")
        request.session['conversation_history'] = conversation_history

        # Return the bot reply as a JSON response
        return JsonResponse({'reply': bot_reply})

    return render(request, 'chatbot.html')


# views.py
from django.shortcuts import render
from .models import Hotel

def hotel_map(request):
    hotels = Hotel.objects.all()
    hotel_data = [
        {
            'name': hotel.name,
            'latitude': hotel.latitude,
            'longitude': hotel.longitude
        }
        for hotel in hotels
    ]
    return render(request, 'map.html', {'hotels': hotel_data})
