# operations_management/models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, datetime, timedelta
from study_space_management.models import Student, StudySpace, Seat
from decimal import Decimal


class Pricing(models.Model):
    """
    Pricing template for enrollments.
    Changes to pricing don't affect existing enrollments.
    """
    PRICING_TYPES = [
        ('hourly', 'Per Hour'),
        ('daily', 'Per Day'),
        ('weekly', 'Per Week'),
        ('monthly', 'Per Month'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=100, help_text="e.g., 'Student Hourly', 'Premium Monthly'")
    pricing_type = models.CharField(max_length=10, choices=PRICING_TYPES)
    
    # Price values
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_week = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Applicability
    study_space = models.ForeignKey('study_space_management.StudySpace', on_delete=models.SET_NULL, null=True, blank=True)
    seat_type = models.CharField(max_length=20, choices=[('standard', 'Standard'), ('premium', 'Air Conditioned')], null=True, blank=True)
    
    # Validity period
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(auto_now_add=True)
    valid_to = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['pricing_type', 'price_per_hour']
        verbose_name = "Pricing"
        verbose_name_plural = "Pricing"
    
    def __str__(self):
        if self.pricing_type == 'hourly' and self.price_per_hour:
            return f"{self.name} - ₹{self.price_per_hour}/hour"
        elif self.pricing_type == 'daily' and self.price_per_day:
            return f"{self.name} - ₹{self.price_per_day}/day"
        elif self.pricing_type == 'weekly' and self.price_per_week:
            return f"{self.name} - ₹{self.price_per_week}/week"
        elif self.pricing_type == 'monthly' and self.price_per_month:
            return f"{self.name} - ₹{self.price_per_month}/month"
        elif self.pricing_type == 'custom' and self.custom_price:
            return f"{self.name} - ₹{self.custom_price} (Custom)"
        return f"{self.name} - {self.get_pricing_type_display()}"


class Enrollment(models.Model):
    """
    Enrollment links to a Pricing model at creation time.
    The price is fixed even if pricing changes later.
    """
    BOOKING_TYPES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]
    
    # ========== BASIC INFORMATION ==========
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='enrollments',
        help_text="Student enrolled"
    )
    study_space = models.ForeignKey(
        StudySpace, 
        on_delete=models.CASCADE, 
        related_name='enrollments',
        help_text="Study space selected"
    )
    seat = models.ForeignKey(
        Seat, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='enrollments',
        help_text="Assigned seat (auto-assigned if left blank)"
    )
    
    # ========== BOOKING DETAILS ==========
    booking_type = models.CharField(
        max_length=10, 
        choices=BOOKING_TYPES,
        help_text="Type of booking: hourly, daily, weekly, monthly, or custom"
    )
    
    # For hourly bookings - custom start and end times
    custom_start_time = models.TimeField(
        null=True, 
        blank=True,
        help_text="For hourly bookings: start time (e.g., 10:00:00)"
    )
    custom_end_time = models.TimeField(
        null=True, 
        blank=True,
        help_text="For hourly bookings: end time (e.g., 12:00:00)"
    )
    
    # For weekly/monthly bookings - hours per day commitment
    hours_per_day = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        null=True, 
        blank=True,
        help_text="Hours per day commitment (e.g., 1.5 for 1.5 hours)"
    )
    
    # Days of week for recurring bookings (0=Monday, 6=Sunday)
    days_of_week = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="Comma-separated days: 0=Mon,1=Tue,2=Wed,3=Thu,4=Fri,5=Sat,6=Sun"
    )
    
    # ========== DATE RANGE ==========
    start_date = models.DateField(
        help_text="Enrollment start date"
    )
    end_date = models.DateField(
        help_text="Enrollment end date"
    )
    
    # ========== PRICING LINK ==========
    # Link to Pricing model at enrollment time (snapshot)
    pricing = models.ForeignKey(
        Pricing, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='enrollments',
        help_text="Pricing plan used for this enrollment (locked at creation)"
    )
    
    # Stored price values (snapshot from pricing at enrollment time)
    price_per_hour = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Price per hour (locked at enrollment)"
    )
    price_per_day = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Price per day (locked at enrollment)"
    )
    price_per_week = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Price per week (locked at enrollment)"
    )
    price_per_month = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Price per month (locked at enrollment)"
    )
    custom_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Custom total price (overrides all calculations)"
    )
    
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Calculated total amount"
    )
    
    # ========== STATUS ==========
    is_active = models.BooleanField(
        default=True,
        help_text="Is this enrollment currently active?"
    )
    is_paid = models.BooleanField(
        default=False,
        help_text="Has the enrollment been fully paid?"
    )
    
    # ========== AUDIT ==========
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_enrollments',
        help_text="User who created this enrollment"
    )
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        
        constraints = [
            # Prevent double-booking same seat on same day (hourly)
            models.UniqueConstraint(
                fields=['seat', 'start_date', 'custom_start_time'],
                condition=models.Q(booking_type='hourly', is_active=True, custom_start_time__isnull=False),
                name='unique_hourly_booking'
            ),
            # Prevent double-booking same seat same day (daily)
            models.UniqueConstraint(
                fields=['seat', 'start_date'],
                condition=models.Q(booking_type='daily', is_active=True),
                name='unique_daily_booking'
            ),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.study_space.name} ({self.get_booking_type_display()})"
    
    # ========== HELPER METHODS ==========
    
    def get_total_days(self):
        """Calculate total number of days in enrollment period"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    def get_total_weeks(self):
        """Calculate total number of weeks"""
        return self.get_total_days() / 7
    
    def get_total_months(self):
        """Calculate total number of months"""
        if self.start_date and self.end_date:
            months = (self.end_date.year - self.start_date.year) * 12
            months += self.end_date.month - self.start_date.month
            return months + 1
        return 0
    
    def get_hours_per_booking(self):
        """Get hours for a single booking based on booking type"""
        if self.booking_type == 'hourly' and self.custom_start_time and self.custom_end_time:
            start_hour = self.custom_start_time.hour + self.custom_start_time.minute / 60
            end_hour = self.custom_end_time.hour + self.custom_end_time.minute / 60
            return end_hour - start_hour
        elif self.hours_per_day:
            return float(self.hours_per_day)
        return 0
    
    def get_total_hours(self):
        """Calculate total hours for the entire enrollment period"""
        if self.booking_type == 'hourly':
            # Single session
            return self.get_hours_per_booking()
        
        elif self.booking_type == 'daily':
            # Full day - hours per day times days
            return self.get_hours_per_booking() * self.get_total_days()
        
        elif self.booking_type == 'weekly':
            # Hours per day × days per week × weeks
            days_list = [int(d.strip()) for d in self.days_of_week.split(',')] if self.days_of_week else []
            days_per_week = len(days_list) if days_list else 5
            return self.get_hours_per_booking() * days_per_week * self.get_total_weeks()
        
        elif self.booking_type == 'monthly':
            # Hours per day × days per month (approx 22 working days)
            return self.get_hours_per_booking() * 22
        
        return 0
    
    def calculate_amount(self):
        """Calculate total amount based on booking type and stored price values"""
        # 1. If custom price is set, use it
        if self.custom_price:
            return self.custom_price
        
        # 2. Calculate based on booking type
        if self.booking_type == 'hourly':
            total_hours = self.get_total_hours()
            if self.price_per_hour:
                return Decimal(str(total_hours)) * self.price_per_hour
        
        elif self.booking_type == 'daily':
            days = self.get_total_days()
            if self.price_per_day:
                return self.price_per_day * Decimal(str(days))
        
        elif self.booking_type == 'weekly':
            weeks = self.get_total_weeks()
            if self.price_per_week:
                return self.price_per_week * Decimal(str(weeks))
        
        elif self.booking_type == 'monthly':
            months = self.get_total_months()
            if self.price_per_month:
                return self.price_per_month * Decimal(str(months))
        
        return None
    
    # ========== VALIDATION METHODS ==========
    
    def clean(self):
        """Validate enrollment data"""
        errors = {}
        
        # 1. Date validation
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors['end_date'] = 'End date must be after or equal to start date.'
        
        # 2. Booking type validations
        if self.booking_type == 'hourly':
            # Check that custom times are provided
            if not (self.custom_start_time and self.custom_end_time):
                errors['__all__'] = 'Both start and end times are required for hourly bookings.'
            elif self.custom_start_time and self.custom_end_time:
                if self.custom_start_time >= self.custom_end_time:
                    errors['__all__'] = 'End time must be after start time.'
        
        elif self.booking_type == 'weekly':
            if not self.hours_per_day:
                errors['hours_per_day'] = 'Hours per day is required for weekly bookings.'
            if not self.days_of_week:
                errors['days_of_week'] = 'Days of week is required for weekly bookings.'
        
        elif self.booking_type == 'monthly':
            if not self.hours_per_day:
                errors['hours_per_day'] = 'Hours per day is required for monthly bookings.'
        
        # 3. Study space active validation
        if self.study_space and not self.study_space.is_active:
            errors['study_space'] = f'Study space "{self.study_space.name}" is inactive.'
        
        # 4. Student active validation
        if self.student and not self.student.active:
            errors['student'] = f'Student "{self.student.name}" is inactive.'
        
        # 5. Seat validation
        if self.seat and self.seat.study_space != self.study_space:
            errors['seat'] = f'Seat "{self.seat.seat_number}" does not belong to {self.study_space.name}.'
        
        # 6. Pricing validation
        if self.pricing and not self.pricing.is_active:
            errors['pricing'] = f'Pricing plan "{self.pricing.name}" is inactive.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Copy pricing values from selected pricing plan and calculate total amount"""
        # Copy pricing values from linked pricing plan (only on creation)
        if self.pricing and not self.pk:
            if self.pricing.price_per_hour:
                self.price_per_hour = self.pricing.price_per_hour
            if self.pricing.price_per_day:
                self.price_per_day = self.pricing.price_per_day
            if self.pricing.price_per_week:
                self.price_per_week = self.pricing.price_per_week
            if self.pricing.price_per_month:
                self.price_per_month = self.pricing.price_per_month
            if self.pricing.custom_price:
                self.custom_price = self.pricing.custom_price
        
        # Calculate total amount
        if not self.total_amount:
            self.total_amount = self.calculate_amount()
        
        # Run validation
        self.full_clean()
        
        super().save(*args, **kwargs)

class Payment(models.Model):
    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('bank', 'Bank Transfer'),
        ('card', 'Credit/Debit Card'),
        ('other', 'Other'),
    ]
    
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=date.today)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
    
    def __str__(self):
        return f"Payment #{self.receipt_number} - ₹{self.amount} - {self.enrollment.student.name}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Generate receipt number: RCPT/YYYY/MM/XXXX
            year = self.payment_date.strftime('%Y')
            month = self.payment_date.strftime('%m')
            last_payment = Payment.objects.filter(
                receipt_number__startswith=f'RCPT/{year}/{month}/'
            ).order_by('-receipt_number').first()
            
            if last_payment:
                try:
                    last_num = int(last_payment.receipt_number.split('/')[-1])
                    next_num = last_num + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
            
            self.receipt_number = f'RCPT/{year}/{month}/{next_num:04d}'
        
        super().save(*args, **kwargs)