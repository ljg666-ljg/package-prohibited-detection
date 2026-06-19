from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        return redirect("detection:dashboard")
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"欢迎回来, {user.username}!")
            next_url = request.GET.get("next", "detection:dashboard")
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect("detection:dashboard")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "注册成功, 欢迎使用包裹违禁物品检测系统!")
            return redirect("detection:dashboard")
    else:
        form = UserCreationForm()
    return render(request, "accounts/register.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.info(request, "您已成功退出登录。")
    return redirect("accounts:login")
