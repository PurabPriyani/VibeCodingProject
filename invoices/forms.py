from django import forms

from .models import BusinessProfile


class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = ["name", "email", "phone", "address", "hst_number", "tax_rate", "charge_tax"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "tax_rate": forms.NumberInput(attrs={"step": "0.01", "min": "0", "max": "100"}),
        }

    def clean_tax_rate(self):
        rate = self.cleaned_data["tax_rate"]
        if rate > 100:
            raise forms.ValidationError("A tax rate can't be more than 100%.")
        return rate
