from django.db import models
from django.contrib.auth.models import User


class FoodRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal_name = models.CharField(max_length=200)
    description = models.TextField()
    ingredients = models.TextField()
    category = models.CharField(max_length=100)  # e.g., "Weight Loss", "Muscle Gain"
    included_ingredients = models.TextField(blank=True, null=True)
    excluded_ingredients = models.TextField(blank=True, null=True)
    recommended_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.meal_name} for {self.user.username}"

    class Meta:
        db_table = "food_recommendation"


class GeneratedWorkout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    day_number = models.IntegerField()  # Day 1, 2, 3 etc.
    workout_type = models.CharField(max_length=50)
    exercise_difficulty = models.IntegerField()
    exercise = models.TextField()

    def __str__(self):
        return f"{self.user.username} - Day {self.day_number} - {self.workout_type} - Difficulty {self.exercise_difficulty}"

    class Meta:
        db_table = "generated_workout"


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_ai = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = "AI" if self.is_ai else "User"
        return f"{self.user.username} - {who} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        db_table = "chat_message"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    height = models.FloatField()
    weight = models.FloatField()
    goal = models.CharField(max_length=50)
    activity_level = models.CharField(max_length=50)

    def bmi_category(self):
        bmi = self.weight / ((self.height / 100) ** 2)
        if bmi < 18.5:
            return 'Underweight'
        elif bmi < 25:
            return 'Normal'
        elif bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'

    def __str__(self):
        return self.user.username

    class Meta:
        db_table = "user_profile"


class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.name}"

    class Meta:
        db_table = "feedback"
