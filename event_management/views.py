from django.shortcuts import render

def homepage(request):
    return render(request, "home.html")

def faq_view(request):
    return render(request, "faq.html")
