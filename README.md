AI Fitness Coach 🏋️‍♂️
An intelligent, open‑source fitness assistant built with Django. It provides personalized workout plans, diet recommendations, and an AI‑powered chatbot to answer all your fitness questions.

Python Django License: MIT

✨ Features
AI Chatbot – Ask fitness‑related questions and get instant, helpful answers powered by Google Gemini API (with optional local fallback using GGUF models).
Personalized Workout Plans – Based on your profile (age, weight, goal, etc.), the system generates daily workouts using a hybrid of rule‑based logic and a custom RNN model.
Food Recommender – Suggests healthy meals tailored to your goal (weight loss, muscle gain, maintenance) and allows you to include/exclude ingredients.
Workout History – Track past workouts with exercise details and video links.
User Profiles – Stores your physical data and fitness goals to personalise every interaction.
Responsive UI – Built with Bootstrap 5 and custom CSS, works on desktop and mobile.
🛠️ Tech Stack
Backend: Django 5.2, Python 3.12
Frontend: HTML, Bootstrap 5, JavaScript (vanilla)
Database: SQLite (default, easily switchable to PostgreSQL)
AI / ML:
Chatbot: Google Gemini API (google‑genai client)
Optional local LLM: ctransformers with GGUF models (Mistral, Phi‑2, TinyLlama)
Workout progression: Custom RNN model (PyTorch)
Exercise selection: Scikit‑learn classifier
Caching: Django cache framework (supports Redis, database, etc.)
Version Control: Git, hosted on GitHub
Model Hosting: Hugging Face (for large GGUF files)
📸 Screenshots
1) https://github.com/adithyanm274/FitBuddy-AI/blob/main/Screenshots/1.png
2) https://github.com/adithyanm274/FitBuddy-AI/blob/main/Screenshots/2.png
3) https://github.com/adithyanm274/FitBuddy-AI/blob/main/Screenshots/3.png
4) https://github.com/adithyanm274/FitBuddy-AI/blob/main/Screenshots/4.png

🚀 Getting Started
Prerequisites
Python 3.12 or higher
pip
Git
(Optional) Redis for caching
Installation
Clone the repository
git clone https://github.com/adithyanm274/fitness-ai-coach.git
cd fitness-ai-coach
2.Create and activate a virtual environment:
  python -m venv venv source venv/bin/activate

3.Install dependencies 
  pip install -r requirements.txt

4.Set up environment variables 
  Create a .env file in the project root (or copy .env.example) and add your configuration:

SECRET_KEY=your-django-secret-key DEBUG=True GEMINI_API_KEY=your-google-gemini-api-key

5.Run database migrations 
  python manage.py migrate

6.Start the development server 
  python manage.py runserver

7.Open your browser and go to
  http://127.0.0.1:8000

📖 Usage Guide

Registration / Login Create an account or log in.
Fill in your profile details (age, weight, height, goal) – this personalises all recommendations.

AI Chatbot Navigate to the Chatbot page.
Type any fitness‑related question (e.g., "Give me a bulking diet plan" or "How many sets for chest?").

The bot responds in seconds using Gemini. If you prefer local inference, download the GGUF models (see below) and switch the chatbot backend.

Exercise Recommender Go to Exercise.
The system generates a daily workout based on your profile and past history.

Each exercise includes sets, reps, and a link to a tutorial video.

Workout history is saved and can be viewed later.

Food Recommender Visit Food Recommender.
Select ingredients you want to include or exclude.

The app suggests meals that match your dietary preferences and fitness goal.

You can browse through multiple recommendations.

📦 Model Files Some machine learning models are too large for GitHub. They are hosted on Hugging Face. You need to download them and place them in the correct folders.

Required Files 

1)mistral-7b-instruct-v0.1.Q4_K_M.gguf

2)phi-2.Q6_K.gguf

3)tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf

Download Instructions Option 1: Using huggingface-cli (Recommended) Install the Hugging Face Hub CLI:

bash pip install huggingface_hub Download all files to the models/ directory:

bash huggingface-cli download adithyanm274/fitness-gguf-models --local-dir ./models --local-dir-use-symlinks False

🔧 Configuration Environment Variables Create a .env file (or set them in your environment) with the following:

Variable Description SECRET_KEY Django secret key (generate a random one) DEBUG Set to True for development, False in prod GEMINI_API_KEY Your Google Gemini API key Switching Chatbot Backend By default, the chatbot uses the Gemini API. To use a local GGUF model instead:

Download the desired model (e.g., Mistral 7B) as described above.

In user_module/views.py, replace the get_ai_response function with the local inference code (commented examples are provided).

Adjust the model path and parameters.

🤝 Contributing 

Contributions are welcome! Please follow these steps:

Fork the repository.

1)Create a new branch (git checkout -b feature/amazing-feature).

2)Commit your changes (git commit -m 'Add some amazing feature').

3)Push to the branch (git push origin feature/amazing-feature).

4)Open a Pull Request.

See CONTRIBUTING.md for more details.

📄 License
Distributed under the MIT License. See LICENSE for more information.

📧 Contact
Name:Adithyan M 
E-mail: adithyan.m.2742001@example.com
Project Link: (https://github.com/adithyanm274/FitBuddy-AI)

🙏 Acknowledgements

Google Gemini API
Django
Bootstrap
ctransformers (for local LLM support)

