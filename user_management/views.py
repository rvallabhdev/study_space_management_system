from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from . forms import RegisterUserForm

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to a success page.
            messages.success(request,("Login Successful!!"))
            # Get next parameter or redirect to home with namespace
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('study_space_management:home')  # ✅ Fixed!
        else:
            messages.success(request,("There was an error logging in. Please try again!!"))
            return redirect('user_management:login')
            # Return an 'invalid login' error message.
    else:
        return render(request,'authenticate/login.html')

def logout_user(request):
    logout(request)
    messages.success(request,("You were logged out!!"))
    # Redirect to a success page.
    return redirect('study_space_management:home')

def register_user(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            form.save()
            username=form.cleaned_data['username']
            password=form.cleaned_data['password1']

            # Log the user in after registration
            user = authenticate(username=username,password=password)
            login(request,user)

            messages.success(request,("Registration Successful!!"))
            return redirect('study_space_management:home')
    else:
        form = RegisterUserForm()
    return render(request,'authenticate/register_user.html',{'form':form})
