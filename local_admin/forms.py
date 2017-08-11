from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.forms.formsets import BaseFormSet

from loads.models import KeyOwner, Cistern


class EditKeyOwnerForm(ModelForm):
    class Meta:
        model = KeyOwner
        fields = {'name', 'car', 'keys', 'comment'}
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 40}),
                   'car': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 40}),
                   'keys': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 16}),
                   'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'cols': 50})}


class AddSystemUserForm(forms.Form):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                               'required': True, 'maxlength': 30}),
                                 max_length=30)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                              'required': True, 'maxlength': 30}),
                                max_length=30)
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'required': True}))


class EditDjangoUserForm(ModelForm):
    class Meta:
        model = User
        fields = {'first_name', 'last_name', 'email'}
        widgets = {'first_name': forms.TextInput(attrs={'class': 'form-control'}),
                   'last_name': forms.TextInput(attrs={'class': 'form-control'}),
                   'email': forms.EmailInput(attrs={'class': 'form-control'})}


class CisternForm(ModelForm):
    class Meta:
        model = Cistern
        fields = {'start_volume', 'max_volume', 'cistern_type', 'name'}
        widgets = {'start_volume': forms.NumberInput(attrs={'class': 'form-control'}),
                   'max_volume': forms.NumberInput(attrs={'class': 'form-control'}),
                   'cistern_type': forms.Select(attrs={'class': 'form-control'}),
                   'name': forms.TextInput(attrs={'class': 'form-control'})}


class AddUpDosedForm(forms.Form):
    volume = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control', 'required': True}),
                                max_digits=7, decimal_places=2, min_value=0.0)
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}), required=False)


class FuelForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': 40,
                                                         'placeholder': 'Тип'}),
                           max_length=40)
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Комментарий', 'rows': 2}),
                              required=False)


class BaseFuelFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        types = []
        duplicates = False
        for form in self.forms:
            if form.cleaned_data:
                name = form.cleaned_data['name']
                if name in types:
                    duplicates = True
                types.append(name)
                if duplicates:
                    raise forms.ValidationError(
                        'Типы топлива должны быть уникальны',
                        code='duplicate_types'
                    )