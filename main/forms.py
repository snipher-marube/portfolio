from django import forms
from .models import CoffeePurchase

class CoffeePurchaseForm(forms.ModelForm):
    AMOUNT_CHOICES = [
        ('3.00', '$3 - ☕ One Coffee'),
        ('5.00', '$5 - ☕☕ Two Coffees'),
        ('10.00', '$10 - ☕☕☕ Special Brew'),
    ]
    
    amount = forms.ChoiceField(
        choices=AMOUNT_CHOICES,
        widget=forms.RadioSelect,
        initial='5.00'
    )
    
    custom_amount = forms.DecimalField(
        max_digits=6, 
        decimal_places=2,
        required=False,
        label='Or enter custom amount ($)'
    )
    
    class Meta:
        model = CoffeePurchase
        fields = ['name', 'email', 'amount', 'custom_amount', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your name (optional)'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Your email (optional)'}),
            'message': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Leave a message (optional)'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        custom_amount = cleaned_data.get('custom_amount')
        amount = cleaned_data.get('amount')
        
        if custom_amount:
            cleaned_data['amount'] = custom_amount
        
        return cleaned_data