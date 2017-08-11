from django import forms


class DateFilter(forms.Form):
    start_date = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker form-control',
                                                               'placeholder': 'с даты'}),
                                 input_formats=('%d.%m.%Y', '%Y-%m-%d'), required=False)
    end_date = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker form-control',
                                                             'placeholder': 'по дату'}),
                               input_formats=('%d.%m.%Y', '%Y-%m-%d'), required=False)


class UserFilter(forms.Form):
    filter_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': 30,
                                                                'placeholder': 'имя'}),
                                  max_length=30, required=False)
    filter_car = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': 40,
                                                               'placeholder': 'машина'}),
                                 max_length=40, required=False)


class FuelFilter(forms.Form):
    filter_fuel = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': 30,
                                                                'placeholder': 'топливо'}),
                                  max_length=30, required=False)


class AddKeysForm(forms.Form):
    key_file = forms.FileField(label='', widget=forms.ClearableFileInput(attrs={'required': True}))
