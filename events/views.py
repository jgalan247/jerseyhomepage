from django.shortcuts import render

def home(request):
    """Homepage view - Hello Jersey!"""
    context = {
        'title': 'Welcome to Jersey Homepage',
        'message': 'Your gateway to discovering amazing events in Jersey!'
    }
    return render(request, 'home.html', context)