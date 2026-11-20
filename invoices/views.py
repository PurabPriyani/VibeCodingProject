from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import BusinessProfileForm
from .models import BusinessProfile


def dashboard(request):
    return render(request, "invoices/dashboard.html")


def business_settings(request):
    profile = BusinessProfile.load()
    form = BusinessProfileForm(request.POST or None, instance=profile)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Business details saved")
        return redirect("settings")

    return render(request, "invoices/settings.html", {"form": form, "profile": profile})
