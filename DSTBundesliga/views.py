from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.shortcuts import render


def login(request):
    return render(request, 'login.html')


def authenticate(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        response = redirect('/')
    else:
        response = redirect('/login')
    return response

