from django import forms
from django.forms import inlineformset_factory

from .models import BusinessProfile, Client, Invoice, InvoiceItem


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


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "company", "email", "phone", "address"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Sarah Chen"}),
            "company": forms.TextInput(attrs={"placeholder": "Maple Bakery"}),
            "email": forms.EmailInput(attrs={"placeholder": "sarah@maplebakery.ca"}),
            "phone": forms.TextInput(attrs={"placeholder": "705-555-0142"}),
            "address": forms.Textarea(attrs={"rows": 2, "placeholder": "12 Dunlop St, Barrie, ON"}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["client", "issue_date", "terms", "notes"]
        widgets = {
            "issue_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Thanks for your business. E-transfer to billing@yourbusiness.ca"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].empty_label = "Choose a client"


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ["description", "quantity", "unit_price"]
        widgets = {
            "description": forms.TextInput(attrs={"placeholder": "Website design"}),
            "quantity": forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "class": "js-qty"}),
            "unit_price": forms.NumberInput(attrs={"step": "0.01", "min": "0", "class": "js-price", "placeholder": "0.00"}),
        }


# min_num=1 means an invoice can't be saved without at least one line item.
ItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=True,
)
