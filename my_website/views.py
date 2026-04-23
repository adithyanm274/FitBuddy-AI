from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login,logout



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_homepage')  # Redirect to admin page
            else:
                return redirect('user_home')   # Redirect to user homepage
        else:
            return render(request, 'common/login.html', {'error': 'Invalid credentials'})

    return render(request, 'common/login.html')



def logout_view(request):
    logout(request)  # Logs out the user
    return redirect('landing_page')  # Redirects to your landing page


def landing_page(request):
    return render(request, 'common/index.html')


from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK", content_type="text/plain")

