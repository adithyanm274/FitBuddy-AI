from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncDate
from django.utils import timezone
from Fitness.rnn_model.rnn import WorkoutRNN
from .forms import FeedbackForm, UserProfileForm
from .models import UserProfile, GeneratedWorkout, ChatMessage, FoodRecommendation
from .ml.workout_model import EnhancedWorkoutClassifier
from Fitness.rnn_model.rnn import predict_next_day, workout_to_idx, diff_to_idx
import torch
import json
import os
import re
import logging
import random
import pandas as pd
from datetime import datetime
import traceback
import difflib
from django.conf import settings
from google import genai
from google.genai import types
from fuzzywuzzy import fuzz, process   # <-- new import

# ------------------------------
# Exercise video links 
# ------------------------------
exercise_video_links = {
    "pushups": "https://www.youtube.com/watch?v=_l3ySVKYVJ8",
    "shoulder press (machine)": "https://www.youtube.com/watch?v=B-aVuyhvLHU",
    "bench press (machine)": "https://www.youtube.com/watch?v=4Y2ZdHCOXok",
    "walking": "https://www.youtube.com/watch?v=Z3YVTgzeYZY",
    "step-ups": "https://www.youtube.com/watch?v=dQqApCGd5Ss",
    "leg press": "https://www.youtube.com/watch?v=IZxyjW7MPJQ",
    "bodyweight squats": "https://www.youtube.com/watch?v=YaXPRqUwItQ",
    "leg curls": "https://www.youtube.com/watch?v=t9sTSr-JYSs&pp=ygUIbGVnIGN1cmw%3D",
    "barbell squats": "https://www.youtube.com/watch?v=-bJIpOq-LWk&pp=ygUNYmFyYmVsbCBzcXVhdNIHCQm-CgGHKiGM7w%3D%3D",
    "dips": "https://www.youtube.com/watch?v=0326dy_-CzM&pp=ygUEZGlwcw%3D%3D",
    "bench press (barbell)": "https://www.youtube.com/watch?v=lWFknlOTbyM&pp=ygULYmVuY2ggcHJlc3M%3D",
    "barbell rows": "https://www.youtube.com/watch?v=qXrTDQG1oUQ&pp=ygUNIGJhcmJlbGwgcm93cw%3D%3D",
    "chin-ups": "https://www.youtube.com/watch?v=mRy9m2Q9_1I&pp=ygUIY2hpbi11cHM%3D",
    "face pulls": "https://www.youtube.com/watch?v=0Po47vvj9g4&pp=ygUKZmFjZSBwdWxscw%3D%3D",
    "seated row": "https://www.youtube.com/watch?v=UCXxvVItLoM&pp=ygUKc2VhdGVkIHJvdw%3D%3D",
}

# ------------------------------
# Workout history
# ------------------------------
@login_required
def workout_history(request):
    workouts = GeneratedWorkout.objects.filter(user=request.user).order_by('day_number')
    data = []
    for w in workouts:
        try:
            exercises = json.loads(w.exercise) if w.exercise else []
        except Exception as e:
            print(f"[DEBUG] Failed to parse JSON for day {w.day_number}: {e}")
            exercises = []
        data.append({
            'day_number': w.day_number,
            'workout_type': w.workout_type,
            'exercise_difficulty': w.exercise_difficulty,
            'exercise': exercises,
        })
    return JsonResponse(data, safe=False)

# ------------------------------
# Exercise recommender view
# ------------------------------
@login_required
def exercise_recommender(request):
    user_data = get_user_profile(request)
    return render(request, 'common/exercise_recommender.html', {'user_data': user_data})

def get_user_profile(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        bmi = profile.bmi_category() if hasattr(profile, 'bmi_category') else 'N/A'
        return {
            "age": profile.age,
            "gender": profile.gender,
            "height": profile.height,
            "weight": profile.weight,
            "bmi": bmi,
            "goal": profile.goal,
            "workout_type": getattr(profile, 'workout_type', 'N/A'),
            "exercise_difficulty": getattr(profile, 'exercise_difficulty', 'N/A')
        }
    except UserProfile.DoesNotExist:
        return {
            "age": "N/A",
            "gender": "N/A",
            "height": "N/A",
            "weight": "N/A",
            "bmi": "N/A",
            "goal": "N/A",
            "workout_type": "N/A",
            "exercise_difficulty": "N/A"
        }

# ------------------------------
# Workout generation (RNN + classifier)
# ------------------------------
workout_types = ['push', 'pull', 'legs', 'cardio']
difficulty_levels = ['beginner', 'intermediate', 'advanced']
workout_to_idx = {'push': 0, 'pull': 1, 'legs': 2, 'cardio': 3}
diff_to_idx = {'beginner': 0, 'intermediate': 1, 'advanced': 2}

def load_trained_model():
    model = WorkoutRNN(
        workout_vocab_size=len(workout_types),
        diff_vocab_size=len(difficulty_levels),
        embed_dim=8,
        hidden_dim=16,
        extra_feat_dim=4
    )
    model.load_state_dict(torch.load("Fitness/data_creation/workout_rnn_model.pth"))
    model.eval()
    return model

def parse_exercise_string(exercise_str):
    match = re.match(r"(.+?)\s*-\s*(\d+)x(\d+)", exercise_str.strip(), re.IGNORECASE)
    if match:
        name = match.group(1).strip().lower()
        sets = int(match.group(2))
        reps = int(match.group(3))
        return {
            "name": name,
            "sets": sets,
            "reps": reps,
            "video_url": exercise_video_links.get(name, "")
        }
    return {
        "name": exercise_str.strip().lower(),
        "sets": "",
        "reps": "",
        "video_url": ""
    }

@csrf_exempt
@require_POST
@login_required
def generate_exercise(request):
    data = pd.read_csv(r'Fitness/data_creation/workout_data_day1.csv')
    classifier = EnhancedWorkoutClassifier()
    classifier.fit(data)
    profile = UserProfile.objects.get(user=request.user)

    try:
        body = json.loads(request.body)
        day_number = body.get('day_number')
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not day_number:
        return JsonResponse({"error": "day_number not provided"}, status=400)

    workout_types_wp = ['pull', 'legs', 'cardio']  
    difficulty_type = ['beginner', 'intermediate', 'advanced']
    difficulty_map = {'beginner': 1, 'intermediate': 2, 'advanced': 3}
    bmi = profile.weight / ((profile.height / 100) ** 2)
    goal_mapping = {'weight loss': 0, 'muscle gain': 1, 'fitness': 2}

    if day_number == 1:
        workout_type = 'push'
        difficulty_label = 'beginner'
    elif day_number == 2:
        workout_type = random.choice(workout_types_wp)
        difficulty_label = random.choice(difficulty_type)
    else:
        prev_day1 = GeneratedWorkout.objects.filter(user=request.user, day_number=day_number-1).first()
        prev_day2 = GeneratedWorkout.objects.filter(user=request.user, day_number=day_number-2).first()
        if prev_day1 and prev_day2:
            seq = [
                (workout_to_idx[prev_day2.workout_type], diff_to_idx[reverse_difficulty(prev_day2.exercise_difficulty)]),
                (workout_to_idx[prev_day1.workout_type], diff_to_idx[reverse_difficulty(prev_day1.exercise_difficulty)])
            ]
            extra_feat = [
                profile.age / 100,
                0 if profile.gender.lower() == 'male' else 1,
                goal_mapping.get(profile.goal.lower(), 0),
                bmi / 50
            ]
            model = load_trained_model()
            workout_type, difficulty_label = predict_next_day(model, seq, extra_feat)
        else:
            workout_type = random.choice(workout_types_wp)
            difficulty_label = random.choice(difficulty_type)

    difficulty = difficulty_map[difficulty_label]

    exercise = classifier.predict({
        'age': profile.age,
        'gender': 0 if profile.gender.lower() == 'male' else 1,
        'goal': goal_mapping.get(profile.goal.lower(), 0),
        'bmi': classifier.bmi_categories.index(profile.bmi_category()),
        'workout_type': workout_type,
        'day1_exercise_difficulty': difficulty
    })

    exercise_list = []
    for key in exercise:
        if exercise[key]:
            parsed = parse_exercise_string(exercise[key])
            exercise_list.append({
                "name": parsed["name"],
                "sets": parsed["sets"],
                "reps": parsed["reps"],
                "category": parsed.get("category", ""),
                "duration": parsed.get("duration", ""),
                "difficulty": difficulty_label,
                "video_url": exercise_video_links.get(parsed["name"].lower(), "")
            })

    workout, created = GeneratedWorkout.objects.get_or_create(
        user=request.user,
        day_number=day_number,
        defaults={
            'workout_type': workout_type,
            'exercise_difficulty': difficulty,
            'exercise': json.dumps(exercise_list)
        }
    )
    if not created:
        workout.workout_type = workout_type
        workout.exercise_difficulty = difficulty
        workout.exercise = json.dumps(exercise_list)
        workout.save()

    return JsonResponse({
        "day": day_number,
        "exercise": exercise_list,
        "workout_type": workout_type,
        "difficulty": difficulty_label
    })

def reverse_difficulty(value):
    reverse_map = {1: 'beginner', 2: 'intermediate', 3: 'advanced'}
    return reverse_map[value]

# ------------------------------
# AI Chatbot (with truncation handling)
# ------------------------------
logger = logging.getLogger(__name__)
client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_CANDIDATES = [
    'models/gemini-2.5-flash',
    'models/gemini-flash-latest',
    'models/gemini-2.0-flash',
    'models/gemini-pro-latest',
]

def get_ai_response(prompt, max_attempts=3):
    full_response = ""
    current_prompt = prompt
    finish_reason = None
    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=MODEL_CANDIDATES[0],
                contents=current_prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=8192,
                    temperature=0.7,
                )
            )
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason
            partial_text = candidate.content.parts[0].text.strip()
            full_response += partial_text
            if finish_reason != "MAX_TOKENS":
                break
            current_prompt = f"Continue exactly from where you left off. Do not repeat anything. Previous text:\n{full_response}\n\nContinue:"
        except Exception as e:
            logger.error(f"AI generation attempt {attempt+1} failed: {e}")
            if attempt == max_attempts - 1:
                raise
            continue
    if finish_reason == "MAX_TOKENS":
        logger.warning("AI response was truncated even after continuation attempts.")
    return full_response.strip()

def get_recent_chat_history(user, max_exchanges=5):
    messages = ChatMessage.objects.filter(user=user).order_by('-timestamp')[:max_exchanges*2]
    messages = reversed(list(messages))
    history_lines = []
    for msg in messages:
        role = "User" if not msg.is_ai else "Coach"
        history_lines.append(f"{role}: {msg.message}")
    return "\n".join(history_lines)

@csrf_exempt
@login_required
def chatbot_response(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        user_message = data.get("message", "").strip()
        if not user_message:
            return JsonResponse({"error": "Empty message"}, status=400)

        try:
            user_profile = UserProfile.objects.get(user=request.user)
            user_goal = user_profile.goal
        except UserProfile.DoesNotExist:
            user_goal = "fitness"

        chat_history = get_recent_chat_history(request.user)
        prompt = f"""You are a friendly, knowledgeable fitness coach AI. 
The user's main fitness goal is: {user_goal}. 
Answer the user's question completely. Do not cut off mid‑sentence. 
Provide practical, evidence‑based advice.

Conversation history:
{chat_history}

User: {user_message}
Coach:"""

        ChatMessage.objects.create(user=request.user, message=user_message, is_ai=False)

        try:
            ai_response = get_ai_response(prompt)
        except Exception as e:
            logger.error(f"All Gemini models failed: {e}")
            return JsonResponse({"error": "AI service unavailable"}, status=503)

        ChatMessage.objects.create(user=request.user, message=ai_response, is_ai=True)
        return JsonResponse({"reply": ai_response})

    except Exception as e:
        logger.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@login_required
def load_chat_by_date(request, date):
    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
        chats = ChatMessage.objects.filter(user=request.user, timestamp__date=selected_date).order_by('timestamp')
        data = {
            "chats": [
                {"sender": "ai" if chat.is_ai else "user", "message": chat.message}
                for chat in chats
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

# ------------------------------
# Registration & Feedback
# ------------------------------
def register_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = make_password(request.POST['password'])
        user = User.objects.create(username=username, password=password)
        UserProfile.objects.create(
            user=user,
            age=request.POST['age'],
            gender=request.POST['gender'],
            height=request.POST['height'],
            weight=request.POST['weight'],
            goal=request.POST['goal'],
            activity_level=request.POST['activity_level']
        )
        return redirect('login')
    return render(request, 'common/register.html')

def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'user_module/thank_you.html')
    else:
        form = FeedbackForm()
    return render(request, 'user_module/feedback.html', {'form': form})

# ------------------------------
# Food Recommender (fully automatic misspelling handling)
# ------------------------------
def load_meals():
    file_path = os.path.join('data', 'healthy_meals_paragraphs_dataset.json')
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_ingredients(description):
    match = re.search(r'ingredients: (.+?)(?:\.|$)', description.lower())
    if match:
        ingredient_text = match.group(1)
        parts = re.split(r',|\sand\s', ingredient_text)
        return [ingredient.strip() for ingredient in parts if ingredient.strip()]
    return []

# ---------- Cached valid ingredients ----------
_VALID_INGREDIENTS_CACHE = None

def _get_all_ingredients():
    global _VALID_INGREDIENTS_CACHE
    if _VALID_INGREDIENTS_CACHE is None:
        meals = load_meals()
        ingredients_set = set()
        for meal in meals:
            ingredients_set.update(extract_ingredients(meal.get("description", "")))
        _VALID_INGREDIENTS_CACHE = ingredients_set
        print("[DEBUG] Loaded ingredients:", sorted(ingredients_set)[:50])
    return _VALID_INGREDIENTS_CACHE

def _normalize_ingredient(ingredient):
    return ingredient.strip().lower()

def _find_best_match(typed_ingredient, valid_ingredients, score_cutoff=70):
    """
    Automatically find the best matching ingredient using:
    1. Exact match (fast)
    2. FuzzyWuzzy ratio (handles typos like 'chikken' -> 'grilled chicken')
    3. Substring match (fallback)
    Returns (best_match, original_typed) or (None, None)
    """
    typed = _normalize_ingredient(typed_ingredient)
    
    # Exact match
    if typed in valid_ingredients:
        return typed, typed_ingredient
    
    # Fuzzy match: compare typed against all valid ingredients
    # Use process.extractOne from fuzzywuzzy
    match, score = process.extractOne(typed, valid_ingredients, scorer=fuzz.ratio)
    if score >= score_cutoff:
        print(f"[DEBUG] Fuzzy match: '{typed}' -> '{match}' (score {score})")
        return match, typed_ingredient
    
    # Substring match (typed inside ingredient or vice versa)
    for valid in valid_ingredients:
        if typed in valid or valid in typed:
            print(f"[DEBUG] Substring match: '{typed}' in/contains '{valid}'")
            return valid, typed_ingredient
    
    print(f"[DEBUG] No match found for '{typed}'")
    return None, None

def meal_matches_preferences(meal, include_ingredients=None, exclude_ingredients=None):
    meal_ingredients = extract_ingredients(meal.get("description", ""))
    meal_ingredients_lower = [i.lower() for i in meal_ingredients]

    include_ingredients = [i.strip().lower() for i in include_ingredients] if include_ingredients else []
    exclude_ingredients = [e.strip().lower() for e in exclude_ingredients] if exclude_ingredients else []

    if include_ingredients:
        found = False
        for inc in include_ingredients:
            for meal_ing in meal_ingredients_lower:
                if inc == meal_ing or inc in meal_ing or meal_ing in inc:
                    found = True
                    break
            if found:
                break
        if not found:
            return False

    if exclude_ingredients:
        for exc in exclude_ingredients:
            for meal_ing in meal_ingredients_lower:
                if exc == meal_ing or exc in meal_ing or meal_ing in exc:
                    return False
    return True

def get_meals_by_category(category, include_ingredients=None, exclude_ingredients=None):
    meals = load_meals()
    all_valid_ingredients = _get_all_ingredients()

    include_ingredients = [i.strip().lower() for i in include_ingredients] if include_ingredients else []
    exclude_ingredients = [e.strip().lower() for e in exclude_ingredients] if exclude_ingredients else []

    # Find the best match for each include ingredient (automatic)
    matched_includes = []
    invalid_includes = []
    for inc in include_ingredients:
        best_match, _ = _find_best_match(inc, all_valid_ingredients)
        if best_match:
            matched_includes.append(inc)   # Keep original for logging, but matching uses substring later
        else:
            invalid_includes.append(inc)

    if invalid_includes:
        print(f"[DEBUG] Invalid includes: {invalid_includes}")
        return [], invalid_includes

    # Use the original include_ingredients for substring matching (they will match via substring)
    matched_meals = [
        meal for meal in meals
        if meal.get("category", "").lower() == category.lower()
        and meal_matches_preferences(meal, include_ingredients, exclude_ingredients)
    ]
    print(f"[DEBUG] Found {len(matched_meals)} meals for includes {include_ingredients}")
    return matched_meals, []

def food_recommender_view(request):
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            goal_input = user_profile.goal.strip().lower().replace('_', ' ') if user_profile.goal else "maintain"
            goal_map = {
                "weight loss": "Weight Loss",
                "fat loss": "Weight Loss",
                "lose fat": "Weight Loss",
                "weight gain": "Weight Gain",
                "muscle gain": "Weight Gain",
                "build muscle": "Weight Gain",
                "maintain": "Maintain",
                "maintenance": "Maintain",
                "fitness": "Maintain",
                "stay fit": "Maintain"
            }
            USER_GOAL = goal_map.get(goal_input, "Maintain")
        except UserProfile.DoesNotExist:
            USER_GOAL = "Maintain"
    else:
        USER_GOAL = "Maintain"

    include = request.GET.get('include', '')
    exclude = request.GET.get('exclude', '')

    def parse_ingredients(raw_input):
        cleaned = re.sub(r'[;|/\\]+', ',', raw_input)
        tokens = [re.sub(r'[^\w\s]', '', item).strip().lower() for item in cleaned.split(',') if item.strip()]
        return tokens

    include_list = parse_ingredients(include) if include else []
    exclude_list = parse_ingredients(exclude) if exclude else []

    meals, invalid_includes = get_meals_by_category(USER_GOAL, include_list, exclude_list)

    if request.method == 'GET' and 'next' not in request.GET:
        request.session['meals'] = meals
        request.session['meal_index'] = 0

    if request.GET.get('next') == '1':
        if 'meal_index' in request.session:
            request.session['meal_index'] += 1

    meal_index = request.session.get('meal_index', 0)
    meal = None

    if meals and meal_index < len(meals):
        meal = meals[meal_index]
        if request.user.is_authenticated and meal:
            ingredients = extract_ingredients(meal.get("description", ""))
            FoodRecommendation.objects.create(
                user=request.user,
                meal_name=meal.get("meal_name", "Unknown Meal"),
                description=meal.get("description", ""),
                ingredients=", ".join(ingredients),
                category=meal.get("category", "Unknown"),
                included_ingredients=", ".join(include_list),
                excluded_ingredients=", ".join(exclude_list)
            )

    context = {
        'user_goal': USER_GOAL,
        'include': include,
        'exclude': exclude,
        'meal': meal,
        'invalid_includes': invalid_includes,
        'has_more': (meal_index + 1 < len(meals))
    }
    return render(request, 'common/food_recommender.html', context)

# ------------------------------
# Homepage
# ------------------------------

@csrf_exempt
@login_required
def homepage(request):
    user = request.user
    chat_dates = (
        ChatMessage.objects
        .filter(user=user)
        .annotate(date=TruncDate('timestamp'))
        .values_list('date', flat=True)
        .distinct()
        .order_by('-date')
    )
    latest_date = chat_dates[0] if chat_dates else None
    chat_history = (
        ChatMessage.objects
        .filter(user=user, timestamp__date=latest_date)
        .order_by('timestamp')
        if latest_date else []
    )
    return render(request, 'user_module/chatbot.html', {
        'chat_dates': chat_dates,
        'chat_history': chat_history
    })