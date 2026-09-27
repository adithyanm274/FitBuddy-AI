from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from user_module.models import Feedback
from django.shortcuts import get_object_or_404, redirect
from user_module.models import Feedback

def delete_feedback(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    feedback.delete()
    return redirect('admin_feedback_list')

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def homepage(request):
    total_users = User.objects.filter(is_superuser=False).count()
    total_feedbacks = Feedback.objects.count()
    return render(request, 'admin_module/homepage.html', {
        'total_users': total_users,
        'total_feedbacks': total_feedbacks,
    })

@user_passes_test(is_admin)
def admin_feedback_list(request):
    feedbacks = Feedback.objects.all().order_by('-submitted_at')
    return render(request, 'admin_module/admin_feedback_list.html', {'feedbacks': feedbacks})

@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.filter(is_superuser=False)
    return render(request, 'admin_module/manage_users.html', {'users': users})

@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_superuser=False)
    user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect('manage_users')


