from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm

import hashlib
from datetime import datetime

from loads.models import Licenced


def login_user(request):
    if request.user.is_authenticated():
        if request.user.is_superuser:
            return HttpResponseRedirect('/admin/')
        else:
            return HttpResponseRedirect('/user/')
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        cur_user = authenticate(username=username, password=password)
        if cur_user is not None:
            if cur_user.is_active:
                login(request, cur_user)
                if cur_user.is_superuser:
                    return HttpResponseRedirect('/admin/')
                else:
                    return HttpResponseRedirect('/user/')
            else:
                messages.add_message(request, messages.ERROR, 'Пользователь неактивен.')
        else:
            messages.add_message(request, messages.ERROR, 'Неверный логин/пароль.')
    return render(request, 'main/index.html')


def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')


# Смена пароля
@login_required
def change_user_passwd(request):
    if request.method == 'POST':
        change_passwd = PasswordChangeForm(user=request.user, data=request.POST)
        if change_passwd.is_valid():
            change_passwd.save()
            messages.add_message(request, messages.SUCCESS, 'Ваш пароль успешно изменен.')
            return HttpResponseRedirect('/')
    else:
        change_passwd = PasswordChangeForm(user=request.user)
    return render(request, 'main/edit_pw.html', {'change_passwd': change_passwd})


@login_required
def licence_key(request):
    if request.method == 'POST':
        key_ch = request.POST['key_ch']
        dt = datetime.today().date()
        h = hashlib.sha1(dt.strftime("%Y-%m-%d").encode())
        print(h.hexdigest())
        print(key_ch)
        if h.hexdigest() == key_ch:
            if Licenced.objects.exists():
                lic = Licenced.objects.all()[0]
                lic.trial = False
                lic.save()
            else:
                Licenced.objects.create(date_time=dt, trial=False)
            messages.add_message(request, messages.SUCCESS, 'Лицензия успешно продлена.')
            return HttpResponseRedirect('/admin/')
        else:
            messages.add_message(request, messages.ERROR, 'Неверный лицензионный ключ.')
    return render(request, 'main/licence_key.html')