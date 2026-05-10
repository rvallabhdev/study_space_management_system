# operations_management/forms.py

from django import forms
from .models import Enrollment
from study_space_management.models import Student, StudySpace, Seat
from datetime import date


class EnrollmentForm(forms.ModelForm):
    """
    Form for creating and editing enrollments.
    """
    
    class Meta:
        model = Enrollment
        fields = [
            'student', 'study_space', 'seat', 'booking_type',
            'start_date', 'end_date',
        ]
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control select2-search',
                'id': 'studentSelect',
                'required': True
            }),
            'study_space': forms.Select(attrs={
                'class': 'form-control',
                'id': 'studySpaceSelect',
                'required': True
            }),
            'seat': forms.Select(attrs={
                'class': 'form-control',
                'id': 'seatSelect'
            }),
            'booking_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'bookingTypeSelect',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control datepicker',
                'type': 'date',
                'required': True
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control datepicker',
                'type': 'date',
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter querysets
        self.fields['student'].queryset = Student.objects.filter(active=True).order_by('name')
        self.fields['study_space'].queryset = StudySpace.objects.filter(is_active=True).order_by('name')
        self.fields['seat'].queryset = Seat.objects.filter(is_active=True)
        self.fields['seat'].required = False
        
        # Add placeholders
        self.fields['start_date'].widget.attrs['placeholder'] = 'Select start date'
        self.fields['end_date'].widget.attrs['placeholder'] = 'Select end date'
    
    def clean(self):
        cleaned_data = super().clean()
        
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Date validation
        if start_date and end_date:
            if start_date > end_date:
                self.add_error('end_date', 'End date must be after start date.')
            
            if start_date < date.today():
                self.add_error('start_date', 'Start date cannot be in the past.')
        
        return cleaned_data


class EnrollmentFilterForm(forms.Form):
    """
    Form for filtering enrollments in the list view.
    """
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(active=True),
        required=False,
        empty_label="All Students",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    study_space = forms.ModelChoiceField(
        queryset=StudySpace.objects.filter(is_active=True),
        required=False,
        empty_label="All Spaces",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    booking_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Enrollment.BOOKING_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_status = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('paid', 'Paid'),
            ('unpaid', 'Unpaid')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by student name or mobile...'
        })
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'})
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'})
    )