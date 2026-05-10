from django import forms
from django.forms import ModelForm
from .models import Student
from datetime import date  # Keep this import

# study_space_management/forms.py
from .models import StudySpace, Seat
import re

# study_space_management/forms.py
from .models import TimeSlot

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'
        widgets = {
            # Text inputs with placeholders
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name',
                'required': True,
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10-digit mobile number',
                'pattern': '[0-9]{10}',
                'title': 'Enter 10 digits only',
                'required': True,
            }),
            'aadhaar_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12-digit Aadhaar number',
                'pattern': '[0-9]{12}',
                'title': 'Enter 12 digits without spaces',
                'required': True,
            }),
            
            # Text inputs for names
            'father_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Father's full name"
            }),
            'father_mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Father's mobile number",
                'pattern': '[0-9]{10}'
            }),
            
            # Text inputs for education
            'course_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., B.Tech, MBA, etc.'
            }),
            'institute_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'College/Institute name'
            }),
            
            # Date picker
            'date_of_joining': forms.DateInput(attrs={
                'class': 'form-control flatpickr',
                'placeholder': 'Select date',
                'required': True
            }),
            
            # File inputs
            'student_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'aadhaar_front': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'aadhaar_back': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            
            # Textareas
            'permanent_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Complete permanent address with PIN code'
            }),
            'local_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Current/local address'
            }),
            
            # Checkbox
            'active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    # Custom validation methods
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if mobile and not mobile.isdigit():
            raise forms.ValidationError('Mobile number should contain only digits.')
        if mobile and len(mobile) != 10:
            raise forms.ValidationError('Mobile number must be exactly 10 digits.')
        return mobile
    
    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get('aadhaar_number')
        if aadhaar and not aadhaar.isdigit():
            raise forms.ValidationError('Aadhaar number should contain only digits.')
        if aadhaar and len(aadhaar) != 12:
            raise forms.ValidationError('Aadhaar number must be exactly 12 digits.')
        return aadhaar
    
    def clean_date_of_joining(self):
        # ✅ FIXED: Changed variable name from 'date' to 'joining_date'
        joining_date = self.cleaned_data.get('date_of_joining')
        if joining_date and joining_date > date.today():
            raise forms.ValidationError('Date of joining cannot be in the future.')
        return joining_date

# study_space_management/forms.py
# ============== STUDY SPACE FORM ==============
class StudySpaceForm(forms.ModelForm):
    """
    Form for creating and editing study spaces
    """
    class Meta:
        model = StudySpace
        fields = ['name', 'location', 'capacity', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Main Hall, Computer Lab'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Ground Floor, Building A'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Number of seats'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_capacity(self):
        """Validate capacity is positive"""
        capacity = self.cleaned_data.get('capacity')
        if capacity and capacity <= 0:
            raise forms.ValidationError('Capacity must be greater than 0.')
        return capacity

# ============== SEAT FORM ==============
# study_space_management/forms.py

class SeatForm(forms.ModelForm):
    """
    Form for creating and editing individual seats
    """
    
    class Meta:
        model = Seat
        fields = ['study_space', 'seat_number', 'seat_type', 'is_active']
        widgets = {
            'study_space': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_study_space'
            }),
            'seat_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., A1, B12, Desk-5',
                'id': 'id_seat_number'
            }),
            'seat_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_seat_type'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_active'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active study spaces
        self.fields['study_space'].queryset = StudySpace.objects.filter(is_active=True)
        
        # CRITICAL FIX: Ensure boolean field is properly initialized
        # This ensures the checkbox shows the current value correctly
        if self.instance and self.instance.pk:
            self.initial['is_active'] = self.instance.is_active
    
    def clean_seat_number(self):
        """Validate seat number format and uniqueness"""
        seat_number = self.cleaned_data.get('seat_number')
        
        if not seat_number:
            raise forms.ValidationError('Seat number is required.')
        
        if len(seat_number) > 20:
            raise forms.ValidationError('Seat number cannot exceed 20 characters.')
        
        # Check for valid characters
        cleaned = seat_number.replace('-', '').replace('_', '')
        if not cleaned.isalnum():
            raise forms.ValidationError(
                'Seat number can only contain letters, numbers, hyphens, and underscores.'
            )
        
        return seat_number.strip()
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        study_space = cleaned_data.get('study_space')
        seat_number = cleaned_data.get('seat_number')
        
        if not study_space or not seat_number:
            return cleaned_data
        
        # Check uniqueness
        existing_seat = Seat.objects.filter(
            study_space=study_space,
            seat_number=seat_number
        )
        
        if self.instance and self.instance.pk:
            existing_seat = existing_seat.exclude(pk=self.instance.pk)
        
        if existing_seat.exists():
            raise forms.ValidationError(
                f'Seat "{seat_number}" already exists in {study_space.name}.'
            )
        
        # Check capacity for new seats
        if not self.instance.pk:
            current_seats = Seat.objects.filter(study_space=study_space).count()
            if current_seats >= study_space.capacity:
                raise forms.ValidationError(
                    f'Cannot add new seat. {study_space.name} is full ({current_seats}/{study_space.capacity} seats).'
                )
        
        return cleaned_data

# ============== BULK SEAT CREATION FORM ==============
class BulkSeatForm(forms.Form):
    """
    Form for creating multiple seats at once
    Handles:
    - Range validation
    - Capacity checks
    - Duplicate detection
    - Seat number format validation
    """
    
    study_space = forms.ModelChoiceField(
        queryset=StudySpace.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_bulk_study_space'
        }),
        label="Study Space",
        help_text="Select the study space where seats will be added"
    )
    
    seat_prefix = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., A, B, Desk',
            'id': 'id_seat_prefix'
        }),
        label="Seat Prefix",
        help_text="Prefix for seat numbers (e.g., 'A' will create A1, A2, A3...)"
    )
    
    start_number = forms.IntegerField(
        min_value=1,
        max_value=9999,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1',
            'id': 'id_start_number'
        }),
        label="Start Number",
        help_text="Starting number for seats (minimum: 1)"
    )
    
    end_number = forms.IntegerField(
        min_value=1,
        max_value=9999,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10',
            'id': 'id_end_number'
        }),
        label="End Number",
        help_text="Ending number for seats (inclusive, maximum: 9999)"
    )
    
    seat_type = forms.ChoiceField(
        choices=Seat.SEAT_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_bulk_seat_type'
        }),
        label="Seat Type",
        help_text="Standard: Non-AC, Premium: Air Conditioned"
    )
    
    def clean_seat_prefix(self):
        """
        Validate seat prefix format
        """
        prefix = self.cleaned_data.get('seat_prefix')
        
        if not prefix:
            raise forms.ValidationError('Seat prefix is required.')
        
        # Check for valid characters
        if not prefix.replace('-', '').replace('_', '').isalnum():
            raise forms.ValidationError(
                'Seat prefix can only contain letters, numbers, hyphens, and underscores.'
            )
        
        # Check length
        if len(prefix) > 10:
            raise forms.ValidationError('Seat prefix cannot exceed 10 characters.')
        
        # Check for reserved words
        reserved_words = ['test', 'demo', 'temp', 'delete', 'null']
        if prefix.lower() in reserved_words:
            raise forms.ValidationError(f'"{prefix}" is a reserved word. Please use a different prefix.')
        
        return prefix.strip()
    
    def clean(self):
        """
        Cross-field validation for bulk seat creation
        """
        cleaned_data = super().clean()
        study_space = cleaned_data.get('study_space')
        prefix = cleaned_data.get('seat_prefix')
        start = cleaned_data.get('start_number')
        end = cleaned_data.get('end_number')
        
        # Skip if any essential field is missing
        if not all([study_space, prefix, start, end]):
            return cleaned_data
        
        # ========== 1. CHECK RANGE VALIDITY ==========
        if start > end:
            raise forms.ValidationError(
                f'Start number ({start}) cannot be greater than end number ({end}).'
            )
        
        # ========== 2. CHECK NUMBER RANGE SIZE ==========
        num_seats = end - start + 1
        
        if num_seats > 100:
            raise forms.ValidationError(
                f'Cannot create {num_seats} seats at once. Maximum 100 seats per batch. '
                f'Please create in smaller batches.'
            )
        
        # ========== 3. CHECK CAPACITY ==========
        current_seats = Seat.objects.filter(study_space=study_space).count()
        
        if current_seats + num_seats > study_space.capacity:
            available = study_space.capacity - current_seats
            raise forms.ValidationError(
                f'Cannot create {num_seats} seats. {study_space.name} currently has '
                f'{current_seats} out of {study_space.capacity} seats. '
                f'You can only add {available} more seat(s).'
            )
        
        # ========== 4. CHECK FOR DUPLICATE SEAT NUMBERS ==========
        # Generate all seat numbers to check
        seat_numbers = [f"{prefix}{num}" for num in range(start, end + 1)]
        
        # Find existing seats
        existing_seats = Seat.objects.filter(
            study_space=study_space,
            seat_number__in=seat_numbers
        ).values_list('seat_number', flat=True)
        
        if existing_seats:
            existing_list = list(existing_seats)
            if len(existing_list) <= 5:
                # Show all if less than 5
                raise forms.ValidationError(
                    f'The following seat(s) already exist in {study_space.name}: '
                    f'{", ".join(existing_list)}. '
                    f'Please remove them from your range.'
                )
            else:
                # Show sample if many
                raise forms.ValidationError(
                    f'{len(existing_list)} seat(s) already exist in {study_space.name} '
                    f'(e.g., {", ".join(existing_list[:3])}...). '
                    f'Please adjust your range.'
                )
        
        # ========== 5. VALIDATE EACH SEAT NUMBER FORMAT ==========
        invalid_seats = []
        for seat_number in seat_numbers:
            # Check format for each seat
            cleaned = seat_number.replace('-', '').replace('_', '')
            if not cleaned.isalnum():
                invalid_seats.append(seat_number)
        
        if invalid_seats:
            raise forms.ValidationError(
                f'The following seat numbers have invalid format: {", ".join(invalid_seats[:5])}. '
                f'Seat numbers can only contain letters, numbers, hyphens, and underscores.'
            )
        
        return cleaned_data
    
    def get_seat_numbers(self):
        """
        Helper method to get the list of seat numbers to create
        """
        if self.is_valid():
            prefix = self.cleaned_data['seat_prefix']
            start = self.cleaned_data['start_number']
            end = self.cleaned_data['end_number']
            return [f"{prefix}{num}" for num in range(start, end + 1)]
        return []

# ============== TIME SLOT FORM ==============

# study_space_management/forms.py

class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['study_space', 'start_time', 'duration_hours', 'is_active']
        widgets = {
            'study_space': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0.5'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'duration_hours': 'In hours (e.g., 2.5 = 2 hours 30 minutes)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active study spaces
        self.fields['study_space'].queryset = StudySpace.objects.filter(is_active=True)