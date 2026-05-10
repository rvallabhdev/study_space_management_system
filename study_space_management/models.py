from django.db import models
import os
import re
import logging
from django.core.exceptions import ValidationError

# Optional: Setup logging for debugging file operations
logger = logging.getLogger(__name__)


class Student(models.Model):
    """
    Student Model - Stores all information about a student including personal,
    educational, and document details.
    
    Features:
    - Automatic folder organization for uploaded images
    - Automatic cleanup of old images when updated
    - Soft delete using active flag
    - Unique Aadhaar number validation
    """
    
    # ========== PERSONAL INFORMATION ==========
    name = models.CharField(
        max_length=100,
        help_text="Full name of the student"
    )
    
    mobile = models.CharField(
        max_length=15, 
        db_index=True,  # Index for faster search
        help_text="10-digit mobile number"
    )
    
    aadhaar_number = models.CharField(
        max_length=20, 
        unique=True,  # Prevent duplicate Aadhaar numbers
        help_text="12-digit Aadhaar number (unique)"
    )

    # ========== FAMILY DETAILS ==========
    father_name = models.CharField(
        max_length=100,
        help_text="Student's father's full name"
    )
    
    father_mobile = models.CharField(
        max_length=15,
        help_text="Father's contact number"
    )

    # ========== EDUCATIONAL DETAILS ==========
    course_name = models.CharField(
        max_length=100,
        help_text="Course enrolled in (e.g., B.Tech, MBA)"
    )
    
    institute_name = models.CharField(
        max_length=150,
        help_text="College/Institute name"
    )

    # ========== DATES ==========
    date_of_joining = models.DateField(
        help_text="Date when student joined the study space"
    )

    # ========== DOCUMENTS (IMAGES) ==========
    student_image = models.ImageField(
        upload_to='students/', 
        null=True, 
        blank=True,
        help_text="Student's photograph"
    )
    
    aadhaar_front = models.ImageField(
        upload_to='students/', 
        null=True, 
        blank=True,
        help_text="Aadhaar card front side"
    )
    
    aadhaar_back = models.ImageField(
        upload_to='students/', 
        null=True, 
        blank=True,
        help_text="Aadhaar card back side"
    )

    # ========== ADDRESSES ==========
    permanent_address = models.TextField(
        help_text="Permanent home address"
    )
    
    local_address = models.TextField(
        help_text="Current/local address"
    )

    # ========== STATUS ==========
    active = models.BooleanField(
        default=True,
        help_text="Soft delete flag - set False to deactivate student"
    )

    def __str__(self):
        """String representation of the student"""
        return f"{self.name} ({self.mobile})"

    def _organize_file_path(self, field_name, field):
        """
        Organize uploaded files into structured folders.
        
        Structure: students/StudentName_YYYYMMDD/filename.jpg
        
        Args:
            field_name (str): Name of the field ('student_image', etc.)
            field: The field object containing the file
        
        Returns:
            str: New file path or None if no file
        """
        # Skip if no file or if file already organized
        if not field or not hasattr(field, 'name') or not field.name:
            return None
        
        # Skip if already in organized folder structure
        if field.name.startswith('students/'):
            return None
        
        # Create folder name: StudentName_YYYYMMDD
        student_name = re.sub(r'\W+', '_', self.name)  # Replace special chars with _
        date_str = self.date_of_joining.strftime('%Y%m%d')
        folder_name = f"{student_name}_{date_str}"
        
        # Get file extension
        file_ext = os.path.splitext(field.name)[1]
        
        # Create standardized filename based on field type
        if field_name == 'student_image':
            new_filename = f"{student_name}_image{file_ext}"
        elif field_name == 'aadhaar_front':
            new_filename = f"{student_name}_aadhaar_front{file_ext}"
        elif field_name == 'aadhaar_back':
            new_filename = f"{student_name}_aadhaar_back{file_ext}"
        else:
            new_filename = f"{student_name}_{field_name}{file_ext}"
        
        # Construct new path
        new_path = os.path.join('students', folder_name, new_filename)
        
        return new_path

    def _get_old_files(self):
        """
        Get old file references before update.
        
        Returns:
            dict: Dictionary of old files with field names as keys
        """
        old_files = {}
        
        # Only fetch if this is an existing record (has primary key)
        if self.pk:
            try:
                old_instance = Student.objects.get(pk=self.pk)
                
                # Check each image field
                if old_instance.student_image:
                    old_files['student_image'] = old_instance.student_image
                if old_instance.aadhaar_front:
                    old_files['aadhaar_front'] = old_instance.aadhaar_front
                if old_instance.aadhaar_back:
                    old_files['aadhaar_back'] = old_instance.aadhaar_back
                    
            except Student.DoesNotExist:
                # This should not happen if self.pk exists, but handle gracefully
                pass
        
        return old_files

    def _safe_delete_file(self, file_field):
        """
        Safely delete a file from the filesystem.
        
        Handles errors gracefully without crashing the application.
        
        Args:
            file_field: The file field containing the file to delete
        """
        if file_field and hasattr(file_field, 'path'):
            try:
                if os.path.isfile(file_field.path):
                    os.remove(file_field.path)
                    logger.info(f"Deleted file: {file_field.path}")
            except (OSError, IOError, PermissionError) as e:
                # Log error but don't crash - file may already be deleted
                logger.warning(f"Could not delete file {file_field.path}: {e}")

    def save(self, *args, **kwargs):
        """
        Override save() to:
        1. Organize uploaded files into structured folders
        2. Delete old files when replaced with new ones
        3. Handle file cleanup on update
        """
        # Step 1: Get old files BEFORE making any changes
        old_files = self._get_old_files()
        
        # Step 2: Organize file paths for new uploads
        for field_name in ['student_image', 'aadhaar_front', 'aadhaar_back']:
            field = getattr(self, field_name)
            
            # Check if there's a new file to organize
            if field and hasattr(field, 'name') and field.name:
                new_path = self._organize_file_path(field_name, field)
                if new_path:
                    field.name = new_path
        
        # Step 3: Save the instance to database
        super().save(*args, **kwargs)
        
        # Step 4: Delete old files that were replaced
        # Do this AFTER save to ensure new file is saved successfully
        for field_name, old_file in old_files.items():
            new_file = getattr(self, field_name)
            
            # Delete if old file exists and new file is different
            if old_file and (not new_file or old_file != new_file):
                self._safe_delete_file(old_file)

    def delete(self, *args, **kwargs):
        """
        Override delete() to:
        1. Remove associated files from filesystem
        2. Then delete the database record
        """
        # Step 1: Collect files before deleting the instance
        files_to_delete = []
        
        if self.student_image:
            files_to_delete.append(self.student_image)
        if self.aadhaar_front:
            files_to_delete.append(self.aadhaar_front)
        if self.aadhaar_back:
            files_to_delete.append(self.aadhaar_back)
        
        # Step 2: Delete the instance from database
        super().delete(*args, **kwargs)
        
        # Step 3: Delete files from filesystem
        # Do this AFTER database deletion to ensure data is gone
        for file_field in files_to_delete:
            self._safe_delete_file(file_field)
    
    class Meta:
        """Model metadata"""
        ordering = ['-date_of_joining']  # Newest first
        indexes = [
            models.Index(fields=['mobile']),  # Already set via db_index=True
            models.Index(fields=['name']),
            models.Index(fields=['active']),
        ]
        verbose_name = "Student"
        verbose_name_plural = "Students"

# ============== STUDY SPACE MODEL ==============
class StudySpace(models.Model):
    """
    Model representing a physical study space/location.
    Each study space can have multiple seats.
    
    Example: "Main Hall", "Computer Lab", "Silent Zone"
    """
    
    # Basic Information
    name = models.CharField(
        max_length=100,
        unique=True,  # No two spaces can have same name
        help_text="Name of the study space (e.g., 'Main Hall', 'Computer Lab')"
    )
    
    location = models.CharField(
        max_length=200,
        blank=True,  # Optional field
        help_text="Physical location or building details"
    )
    
    # Capacity Management
    capacity = models.PositiveIntegerField(
        help_text="Total number of seats available in this space"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Is this study space currently available for enrollment?"
    )
    
    # Timestamps (optional but good practice)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']  # Sort by name in admin and queries
        verbose_name = "Study Space"
        verbose_name_plural = "Study Spaces"
    
    def __str__(self):
        """String representation for admin and dropdowns"""
        return f"{self.name} (Capacity: {self.capacity})"
    
    def get_available_seats_count(self):
        """
        Get number of currently available seats
        This is a helper method that will be used later in enrollment
        """
        occupied_seats = Seat.objects.filter(
            study_space=self,
            is_active=True,
            enrollments__is_active=True  # Will work when Enrollment model is created
        ).count()
        
        return self.capacity - occupied_seats


# ============== SEAT MODEL ==============
class Seat(models.Model):
    """
    Model representing individual seats within a study space.
    Each seat belongs to one study space.
    
    Example: "A1", "A2", "B1", "B2" etc.
    """
    
    # Relationship
    study_space = models.ForeignKey(
        StudySpace,
        on_delete=models.CASCADE,  # If study space deleted, delete its seats
        related_name='seats',      # Allows study_space.seats.all() to get all seats
        help_text="Which study space this seat belongs to"
    )
    
    # Seat Identification
    seat_number = models.CharField(
        max_length=20,
        help_text="Seat identifier (e.g., 'A1', 'B12', 'Desk-5')"
    )
    
    # Optional: Seat Type (for future expansion)
    SEAT_TYPES = [
        ('standard', 'Standard Desk'),
        ('premium', 'Air Conditioned Desk'),
    ]
    
    seat_type = models.CharField(
        max_length=20,
        choices=SEAT_TYPES,
        default='standard',
        help_text="Type of seat (for pricing or preference)"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Is this seat available for enrollment?"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Ensure seat numbers are unique within a study space
        # This prevents: StudySpace A having two seats both numbered "A1"
        unique_together = ('study_space', 'seat_number')
        
        ordering = ['study_space', 'seat_number']  # Sort by space then seat number
        verbose_name = "Seat"
        verbose_name_plural = "Seats"
    
    def __str__(self):
        """String representation showing both space and seat"""
        return f"{self.study_space.name} - Seat {self.seat_number}"
    
    def clean(self):
        """
        Custom validation to ensure seat_number format is valid
        This runs before save when using forms
        """
        if self.seat_number and not self.seat_number.strip():
            raise ValidationError("Seat number cannot be empty")
        
        # Optional: Validate seat number format (e.g., must be alphanumeric)
        if self.seat_number and not self.seat_number.replace('-', '').replace('_', '').isalnum():
            raise ValidationError("Seat number should contain only letters, numbers, hyphens, and underscores")
    
    def save(self, *args, **kwargs):
        """
        Override save to run validation
        """
        self.full_clean()  # Calls clean() method
        super().save(*args, **kwargs)
    
    def is_currently_occupied(self):
        """
        Check if this seat is currently occupied by an active enrollment
        This will be used when checking availability
        """
        # Will be implemented when Enrollment model is created
        return False  # Placeholder for now
    

# ============== TIME SLOT MODEL ==============

# study_space_management/models.py

class TimeSlot(models.Model):
    """
    Time slots are specific to each study space.
    Each space can have its own schedule.
    """
    study_space = models.ForeignKey(
        'StudySpace',
        on_delete=models.CASCADE,
        related_name='time_slots',
        help_text="Which study space this time slot belongs to"
    )
    name = models.CharField(
        max_length=50,
        default="General Slot",
        help_text="e.g., 'Morning', 'Afternoon', 'Evening'"
    )
    start_time = models.TimeField(help_text="Start time (e.g., 09:00:00)")
    duration_hours = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        help_text="Duration in hours (e.g., 3.0 = 3 hours)"
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Order in Gantt chart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['study_space', 'display_order', 'start_time']
        # Prevent duplicate start times for the same study space
        unique_together = ['study_space', 'start_time']
        verbose_name = "Time Slot"
        verbose_name_plural = "Time Slots"

    def __str__(self):
        return f"{self.study_space.name}: {self.name} ({self.get_start_time_display()} - {self.get_end_time_display()})"

    def get_start_time_display(self):
        return self.start_time.strftime('%I:%M %p') if self.start_time else ""

    def get_end_time(self):
        """Calculate end time from start_time + duration_hours"""
        if not self.start_time or not self.duration_hours:
            return None
        from datetime import datetime, timedelta
        base = datetime.combine(datetime.today(), self.start_time)
        end = base + timedelta(hours=float(self.duration_hours))
        return end.time()

    def get_end_time_display(self):
        end = self.get_end_time()
        return end.strftime('%I:%M %p') if end else ""

    def get_duration_display(self):
        """Human-readable duration (e.g., '2 hours 30 minutes')"""
        if not self.duration_hours:
            return ""
        hours = int(self.duration_hours)
        minutes = int((self.duration_hours - hours) * 60)
        if hours == 0:
            return f"{minutes} min"
        if minutes == 0:
            return f"{hours} hr"
        return f"{hours} hr {minutes} min"

    def _check_overlap(self):
        """
        Check if this time slot overlaps with any existing slot in the same study space.
        Returns (has_overlap, overlapping_slot) tuple.
        """
        if not self.study_space or not self.start_time or not self.duration_hours:
            return False, None
        
        end_time = self.get_end_time()
        if not end_time:
            return False, None
        
        # Find overlapping slots (excluding current instance)
        overlapping = TimeSlot.objects.filter(
            study_space=self.study_space
        ).exclude(pk=self.pk)
        
        for slot in overlapping:
            slot_end = slot.get_end_time()
            if not slot_end:
                continue
            
            # Overlap condition: A.start < B.end AND A.end > B.start
            if self.start_time < slot_end and end_time > slot.start_time:
                return True, slot
        
        return False, None

    def clean(self):
        """Validate time slot data"""
        from django.core.exceptions import ValidationError
        
        # ========== BASIC VALIDATIONS ==========
        if not self.name:
            raise ValidationError({'name': 'Name is required.'})
        
        if not self.start_time:
            raise ValidationError({'start_time': 'Start time is required.'})
        
        if not self.duration_hours:
            raise ValidationError({'duration_hours': 'Duration is required.'})
        
        if self.duration_hours <= 0:
            raise ValidationError({'duration_hours': 'Duration must be positive.'})
        
        if self.duration_hours > 24:
            raise ValidationError({'duration_hours': 'Duration cannot exceed 24 hours.'})
        
        # ========== STUDY SPACE VALIDATION ==========
        if self.study_space and not self.study_space.is_active:
            raise ValidationError({
                'study_space': f'Cannot add/update time slot for inactive study space "{self.study_space.name}".'
            })
        
        # ========== OVERLAP VALIDATION ==========
        has_overlap, overlapping_slot = self._check_overlap()
        if has_overlap and overlapping_slot:
            raise ValidationError({
                'start_time': f'This time slot overlaps with "{overlapping_slot.name}" '
                              f'({overlapping_slot.get_start_time_display()} - {overlapping_slot.get_end_time_display()}). '
                              f'Please adjust the start time or duration.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)