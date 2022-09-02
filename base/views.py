from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q

from .models import Room, Topic, Message
from .forms import RoomForm, UserForm


# Create your views here.
def login_page(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        user_name = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=user_name)
        except:
            messages.error(request, 'User Does Not Exist.')

        user = authenticate(request, username=user_name, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR Password Does Not Exist.')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logout_user(request):
    logout(request)
    return redirect('home')


def register_page(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration.')

    context = {'form': form}
    return render(request, 'base/login_register.html', context)


def home(request):
    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_msgs = Message.objects.filter(
        Q(room__topic__name__icontains=q)
    )

    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count, 'room_msgs': room_msgs}
    return render(request, 'base/home.html', context)


def room(request, pk):
    room_ = Room.objects.get(id=pk)
    room_msgs = room_.message_set.all()
    participants = room_.participants.all()

    if request.method == 'POST':
        msg = Message.objects.create(
            user=request.user,
            room=room_,
            body=request.POST.get('body')
        )
        room_.participants.add(request.user)
        return redirect('room', pk=room_.id)

    context = {'room': room_, 'room_messages': room_msgs, 'participants': participants}
    return render(request, 'base/room.html', context)


def user_profile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_msgs = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms, 'room_msgs': room_msgs, 'topics': topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')
    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def update_room(request, pk):
    room_ = Room.objects.get(id=pk)
    form = RoomForm(instance=room_)
    topics = Topic.objects.all()

    if request.user != room_.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room_.name = request.POST.get('name')
        room_.topic = topic
        room_.description = request.POST.get('description')
        room_.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'room': room_}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def delete_room(request, pk):
    room_ = Room.objects.get(id=pk)

    if request.user != room_.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        room_.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def delete_message(request, pk):
    msg = Message.objects.get(id=pk)

    if request.user != msg.user:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        msg.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': msg})


@login_required(login_url='login')
def update_user(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    context = {'form': form}
    return render(request, 'base/update-user.html', context)


def topics_page(request):
    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics': topics}
    return render(request, 'base/topics.html', context)


def activity_page(request):
    room_msgs = Message.objects.all()
    context = {'room_msgs': room_msgs}
    return render(request, 'base/activity.html', context)
