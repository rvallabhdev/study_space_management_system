from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.db import IntegrityError
from django.http import JsonResponse
from datetime import datetime, timedelta, time
from django.utils import timezone
from .models import Student, StudySpace, Seat, TimeSlot
from .forms import StudentForm, StudySpaceForm, SeatForm, BulkSeatForm, TimeSlotForm
from operations_management.models import Enrollment


# ============== HOME & STUDENT VIEWS ==============

def home(request):
    """Display all active students"""
    students = Student.objects.filter(active=True).order_by('-date_of_joining')
    return render(request, 'study_space_management/student_list.html', {'students': students})


def student_list(request):
    """Alternative student list view"""
    students = Student.objects.filter(active=True).order_by('-date_of_joining')
    return render(request, 'study_space_management/student_list.html', {'students': students})


def student_detail(request, pk):
    """Show detailed information for a single student"""
    student = get_object_or_404(Student, pk=pk, active=True)
    return render(request, 'study_space_management/student_detail.html', {'student': student})


@login_required
def student_create(request):
    """Create a new student record"""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student "{student.name}" created successfully!')
            return redirect('study_space_management:student_detail', pk=student.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm()
    
    return render(request, 'study_space_management/student_form.html', {'form': form})


@login_required
def student_update(request, pk):
    """Update an existing student record"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student "{student.name}" updated successfully!')
            return redirect('study_space_management:student_detail', pk=student.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'study_space_management/student_form.html', {
        'form': form,
        'student': student
    })


@login_required
def student_delete(request, pk):
    """Soft delete a student (set active=False)"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        student.active = False
        student.save()
        messages.success(request, f'Student "{student.name}" deactivated successfully!')
        return redirect('study_space_management:student_list')
    
    return render(request, 'study_space_management/student_confirm_delete.html', {'student': student})


# ============== STUDY SPACE VIEWS ==============

@login_required
def study_space_list(request):
    """Display all study spaces with search and filter"""
    study_spaces = StudySpace.objects.all()
    
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    
    if search_query:
        study_spaces = study_spaces.filter(
            Q(name__icontains=search_query) | 
            Q(location__icontains=search_query)
        )
    
    if status_filter == 'active':
        study_spaces = study_spaces.filter(is_active=True)
    elif status_filter == 'inactive':
        study_spaces = study_spaces.filter(is_active=False)
    
    if category_filter == 'standard':
        study_spaces = study_spaces.filter(seats__seat_type='standard').distinct()
    elif category_filter == 'air_conditioned':
        study_spaces = study_spaces.filter(seats__seat_type='premium').distinct()
    
    study_spaces = study_spaces.annotate(
        total_seats=Count('seats'),
        active_seats=Count('seats', filter=Q(seats__is_active=True)),
        standard_seats=Count('seats', filter=Q(seats__seat_type='standard')),
        ac_seats=Count('seats', filter=Q(seats__seat_type='premium'))
    ).order_by('name')
    
    total_spaces = study_spaces.count()
    active_spaces = study_spaces.filter(is_active=True).count()
    total_seats = sum(space.total_seats for space in study_spaces)
    active_seats = sum(space.active_seats for space in study_spaces)
    
    avg_active_seats = (active_seats // total_spaces) if total_spaces > 0 else 0
    avg_capacity = (sum(space.capacity for space in study_spaces) // total_spaces) if total_spaces > 0 else 0
    
    context = {
        'study_spaces': study_spaces,
        'total_spaces': total_spaces,
        'active_spaces': active_spaces,
        'total_seats': total_seats,
        'active_seats': active_seats,
        'avg_active_seats': avg_active_seats,
        'avg_capacity': avg_capacity,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
    }
    return render(request, 'study_space_management/study_space_list.html', context)


@login_required
def study_space_detail(request, pk):
    """Display details of a specific study space with its seats"""
    study_space = get_object_or_404(StudySpace, pk=pk)
    seats = study_space.seats.all().order_by('seat_number')
    
    active_seats = seats.filter(is_active=True).count()
    inactive_seats = seats.filter(is_active=False).count()
    
    context = {
        'study_space': study_space,
        'seats': seats,
        'active_seats': active_seats,
        'inactive_seats': inactive_seats,
        'total_seats': seats.count(),
    }
    return render(request, 'study_space_management/study_space_detail.html', context)


@login_required
def study_space_create(request):
    """Create a new study space"""
    if request.method == 'POST':
        form = StudySpaceForm(request.POST)
        if form.is_valid():
            study_space = form.save()
            messages.success(request, f'Study space "{study_space.name}" created successfully!')
            return redirect('study_space_management:study_space_detail', pk=study_space.pk)
    else:
        form = StudySpaceForm()
    
    return render(request, 'study_space_management/study_space_form.html', {
        'form': form,
        'title': 'Add Study Space'
    })


@login_required
def study_space_update(request, pk):
    """Update an existing study space"""
    study_space = get_object_or_404(StudySpace, pk=pk)
    
    if request.method == 'POST':
        form = StudySpaceForm(request.POST, instance=study_space)
        if form.is_valid():
            study_space = form.save()
            messages.success(request, f'Study space "{study_space.name}" updated successfully!')
            return redirect('study_space_management:study_space_detail', pk=study_space.pk)
    else:
        form = StudySpaceForm(instance=study_space)
    
    return render(request, 'study_space_management/study_space_form.html', {
        'form': form,
        'study_space': study_space,
        'title': 'Edit Study Space'
    })


@login_required
def study_space_delete(request, pk):
    """Delete a study space (with confirmation)"""
    study_space = get_object_or_404(StudySpace, pk=pk)
    has_active_enrollments = False
    
    if has_active_enrollments:
        messages.error(request, f'Cannot delete "{study_space.name}" because it has active enrollments.')
        return redirect('study_space_management:study_space_detail', pk=study_space.pk)
    
    if request.method == 'POST':
        name = study_space.name
        study_space.delete()
        messages.success(request, f'Study space "{name}" deleted successfully!')
        return redirect('study_space_management:study_space_list')
    
    return render(request, 'study_space_management/study_space_confirm_delete.html', {
        'study_space': study_space
    })


# ============== SEAT VIEWS ==============

@login_required
def seat_list(request, study_space_id=None):
    """Display all seats with advanced search and filtering"""
    if study_space_id:
        study_space = get_object_or_404(StudySpace, pk=study_space_id)
        seats = Seat.objects.filter(study_space=study_space)
        title = f"Seats in {study_space.name}"
    else:
        seats = Seat.objects.all()
        title = "All Seats"
        study_space = None
    
    seat_number_filter = request.GET.get('seat_number', '')
    study_space_filter = request.GET.get('study_space', '')
    seat_type_filter = request.GET.get('seat_type', '')
    status_filter = request.GET.get('status', '')
    occupancy_filter = request.GET.get('occupancy', '')
    sort_by = request.GET.get('sort', 'seat_number')
    
    if seat_number_filter:
        seats = seats.filter(seat_number__icontains=seat_number_filter)
    
    if study_space_filter:
        seats = seats.filter(study_space_id=study_space_filter)
        filtered_space = StudySpace.objects.filter(id=study_space_filter).first()
        study_space_name = filtered_space.name if filtered_space else ''
    else:
        study_space_name = ''
    
    if seat_type_filter:
        seats = seats.filter(seat_type=seat_type_filter)
    
    if status_filter == 'active':
        seats = seats.filter(is_active=True)
    elif status_filter == 'inactive':
        seats = seats.filter(is_active=False)
    
    if sort_by:
        sort_options = {
            'seat_number': 'seat_number',
            '-seat_number': '-seat_number',
            'study_space__name': 'study_space__name',
            '-study_space__name': '-study_space__name',
            'seat_type': 'seat_type',
            'is_active': 'is_active',
            '-is_active': '-is_active',
            'created_at': 'created_at',
            '-created_at': '-created_at',
        }
        seats = seats.order_by(sort_options.get(sort_by, 'seat_number'))
    else:
        seats = seats.order_by('seat_number')
    
    total_seats = seats.count()
    active_seats = seats.filter(is_active=True).count()
    standard_seats = seats.filter(seat_type='standard').count()
    premium_seats = seats.filter(seat_type='premium').count()
    
    all_study_spaces = StudySpace.objects.filter(is_active=True).order_by('name')
    
    context = {
        'seats': seats,
        'title': title,
        'study_space': study_space,
        'total_seats': total_seats,
        'active_seats': active_seats,
        'standard_seats': standard_seats,
        'premium_seats': premium_seats,
        'all_study_spaces': all_study_spaces,
        'seat_number_filter': seat_number_filter,
        'study_space_filter': study_space_filter,
        'study_space_name': study_space_name,
        'seat_type_filter': seat_type_filter,
        'status_filter': status_filter,
        'occupancy_filter': occupancy_filter,
        'sort_by': sort_by,
    }
    return render(request, 'study_space_management/seat_list.html', context)


@login_required
def seat_create(request):
    """Create a new seat"""
    if request.method == 'POST':
        form = SeatForm(request.POST)
        
        if form.is_valid():
            study_space = form.cleaned_data['study_space']
            seat_number = form.cleaned_data['seat_number']
            
            if Seat.objects.filter(study_space=study_space, seat_number=seat_number).exists():
                messages.error(request, f'Seat "{seat_number}" already exists in {study_space.name}.')
                return render(request, 'study_space_management/seat_form.html', {'form': form, 'title': 'Add Seat'})
            
            current_seats = Seat.objects.filter(study_space=study_space).count()
            if current_seats >= study_space.capacity:
                messages.error(request, f'Cannot add seat. {study_space.name} is full ({current_seats}/{study_space.capacity} seats).')
                return render(request, 'study_space_management/seat_form.html', {'form': form, 'title': 'Add Seat'})
            
            try:
                seat = form.save()
                messages.success(request, f'Seat "{seat.seat_number}" created in {seat.study_space.name}! ({current_seats + 1}/{study_space.capacity} seats)')
                return redirect('study_space_management:study_space_detail', pk=seat.study_space.pk)
            except IntegrityError:
                messages.error(request, f'Seat "{seat_number}" already exists in {study_space.name}.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SeatForm()
    
    return render(request, 'study_space_management/seat_form.html', {
        'form': form,
        'title': 'Add Seat'
    })


@login_required
def seat_update(request, pk):
    """Update an existing seat"""
    seat = get_object_or_404(Seat, pk=pk)
    old_study_space = seat.study_space
    old_seat_number = seat.seat_number
    old_is_active = seat.is_active
    
    if request.method == 'POST':
        form = SeatForm(request.POST, instance=seat)
        
        if form.is_valid():
            new_study_space = form.cleaned_data['study_space']
            new_seat_number = form.cleaned_data['seat_number']
            new_is_active = form.cleaned_data['is_active']
            
            if (new_study_space == old_study_space and 
                new_seat_number == old_seat_number and 
                new_is_active == old_is_active):
                messages.info(request, 'No changes were made.')
                return redirect('study_space_management:study_space_detail', pk=seat.study_space.pk)
            
            if new_study_space == old_study_space and new_seat_number != old_seat_number:
                if Seat.objects.filter(study_space=new_study_space, seat_number=new_seat_number).exists():
                    messages.error(request, f'Seat "{new_seat_number}" already exists in {new_study_space.name}.')
                    return render(request, 'study_space_management/seat_form.html', {
                        'form': form, 'seat': seat, 'title': 'Edit Seat'
                    })
            
            if new_study_space != old_study_space:
                if not new_study_space.is_active:
                    messages.error(request, f'Cannot move seat to {new_study_space.name} because it is inactive.')
                    return render(request, 'study_space_management/seat_form.html', {
                        'form': form, 'seat': seat, 'title': 'Edit Seat'
                    })
                
                target_seats = Seat.objects.filter(study_space=new_study_space).count()
                if target_seats >= new_study_space.capacity:
                    messages.error(request, f'Cannot move seat. {new_study_space.name} is full ({target_seats}/{new_study_space.capacity} seats).')
                    return render(request, 'study_space_management/seat_form.html', {
                        'form': form, 'seat': seat, 'title': 'Edit Seat'
                    })
                
                if Seat.objects.filter(study_space=new_study_space, seat_number=new_seat_number).exists():
                    messages.error(request, f'Seat "{new_seat_number}" already exists in {new_study_space.name}.')
                    return render(request, 'study_space_management/seat_form.html', {
                        'form': form, 'seat': seat, 'title': 'Edit Seat'
                    })
            
            try:
                seat = form.save()
                changes = []
                if new_study_space != old_study_space:
                    changes.append(f'moved to {new_study_space.name}')
                if new_seat_number != old_seat_number:
                    changes.append(f'renumbered to {new_seat_number}')
                if new_is_active != old_is_active:
                    status = "activated" if new_is_active else "deactivated"
                    changes.append(f'{status}')
                
                if changes:
                    messages.success(request, f'Seat updated: {", ".join(changes)}.')
                else:
                    messages.success(request, f'Seat "{seat.seat_number}" updated successfully!')
                
                return redirect('study_space_management:study_space_detail', pk=seat.study_space.pk)
            except IntegrityError:
                messages.error(request, f'Seat "{new_seat_number}" already exists in {new_study_space.name}.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SeatForm(instance=seat)
        form.initial['is_active'] = seat.is_active
    
    return render(request, 'study_space_management/seat_form.html', {
        'form': form,
        'seat': seat,
        'title': 'Edit Seat'
    })


@login_required
def seat_delete(request, pk):
    """Delete a seat"""
    seat = get_object_or_404(Seat, pk=pk)
    seat_number = seat.seat_number
    study_space_pk = seat.study_space.pk
    study_space_name = seat.study_space.name
    
    if request.method == 'POST':
        try:
            seat.delete()
            messages.success(request, f'Seat "{seat_number}" in {study_space_name} deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting seat: {str(e)}')
        return redirect('study_space_management:study_space_detail', pk=study_space_pk)
    
    return render(request, 'study_space_management/seat_confirm_delete.html', {'seat': seat})


@login_required
def bulk_seat_create(request):
    """Create multiple seats at once"""
    if request.method == 'POST':
        form = BulkSeatForm(request.POST)
        
        if form.is_valid():
            study_space = form.cleaned_data['study_space']
            prefix = form.cleaned_data['seat_prefix']
            start = form.cleaned_data['start_number']
            end = form.cleaned_data['end_number']
            seat_type = form.cleaned_data['seat_type']
            
            num_to_create = end - start + 1
            current_seats = Seat.objects.filter(study_space=study_space).count()
            
            if current_seats + num_to_create > study_space.capacity:
                messages.error(request, f'Cannot add {num_to_create} seats. {study_space.name} has {current_seats}/{study_space.capacity} seats. You can only add {study_space.capacity - current_seats} more.')
                return render(request, 'study_space_management/bulk_seat_form.html', {'form': form})
            
            seats_to_create = []
            existing_seats = []
            
            for num in range(start, end + 1):
                seat_number = f"{prefix}{num}"
                if Seat.objects.filter(study_space=study_space, seat_number=seat_number).exists():
                    existing_seats.append(seat_number)
                else:
                    seats_to_create.append(
                        Seat(
                            study_space=study_space,
                            seat_number=seat_number,
                            seat_type=seat_type,
                            is_active=True
                        )
                    )
            
            created_count = 0
            if seats_to_create:
                try:
                    Seat.objects.bulk_create(seats_to_create)
                    created_count = len(seats_to_create)
                except IntegrityError:
                    messages.error(request, 'Database error occurred while creating seats.')
                    return render(request, 'study_space_management/bulk_seat_form.html', {'form': form})
            
            if created_count > 0:
                messages.success(request, f'Created {created_count} seat(s) in {study_space.name}. ({current_seats + created_count}/{study_space.capacity} seats)')
            
            if existing_seats:
                messages.warning(request, f'These seats already exist and were not created: {", ".join(existing_seats)}')
            
            if created_count == 0 and not existing_seats:
                messages.info(request, 'No seats were created. Please check your input.')
                return render(request, 'study_space_management/bulk_seat_form.html', {'form': form})
            
            return redirect('study_space_management:study_space_detail', pk=study_space.pk)
    else:
        form = BulkSeatForm()
    
    return render(request, 'study_space_management/bulk_seat_form.html', {'form': form})


# ============== TIME SLOT VIEWS ==============

@login_required
def time_slot_list(request):
    """List all time slots, grouped by study space."""
    time_slots = TimeSlot.objects.select_related('study_space').order_by('study_space', 'start_time')
    
    slots_by_space = {}
    for slot in time_slots:
        space_name = slot.study_space.name
        slots_by_space.setdefault(space_name, []).append(slot)
    
    context = {
        'slots_by_space': slots_by_space,
        'total_slots': time_slots.count(),
        'active_slots': time_slots.filter(is_active=True).count(),
        'inactive_slots': time_slots.filter(is_active=False).count(),
    }
    return render(request, 'study_space_management/time_slot_list.html', context)


@login_required
def time_slot_create(request):
    """Create a new time slot."""
    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            slot = form.save()
            messages.success(request, f'Time slot for "{slot.study_space.name}" at {slot.get_start_time_display()} created successfully!')
            return redirect('study_space_management:time_slot_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TimeSlotForm()
    
    return render(request, 'study_space_management/time_slot_form.html', {
        'form': form,
        'title': 'Add Time Slot'
    })


@login_required
def time_slot_update(request, pk):
    """Update an existing time slot."""
    slot = get_object_or_404(TimeSlot, pk=pk)
    
    if request.method == 'POST':
        form = TimeSlotForm(request.POST, instance=slot)
        if form.is_valid():
            slot = form.save()
            messages.success(request, f'Time slot for "{slot.study_space.name}" updated successfully!')
            return redirect('study_space_management:time_slot_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TimeSlotForm(instance=slot)
    
    return render(request, 'study_space_management/time_slot_form.html', {
        'form': form,
        'time_slot': slot,
        'title': 'Edit Time Slot'
    })


@login_required
def time_slot_delete(request, pk):
    """Delete a time slot (with confirmation)."""
    slot = get_object_or_404(TimeSlot, pk=pk)
    
    if Enrollment.objects.filter(time_slot=slot, is_active=True).exists():
        messages.error(request, f'Cannot delete time slot for "{slot.study_space.name}" at {slot.get_start_time_display()} because it has active enrollments.')
        return redirect('study_space_management:time_slot_list')
    
    if request.method == 'POST':
        space_name = slot.study_space.name
        slot.delete()
        messages.success(request, f'Time slot for "{space_name}" deleted successfully!')
        return redirect('study_space_management:time_slot_list')
    
    return render(request, 'study_space_management/time_slot_confirm_delete.html', {'time_slot': slot})


@login_required
def time_slot_toggle_status(request, pk):
    """Toggle active/inactive status of a time slot."""
    slot = get_object_or_404(TimeSlot, pk=pk)
    
    if slot.is_active:
        if Enrollment.objects.filter(time_slot=slot, is_active=True).exists():
            messages.error(request, f'Cannot deactivate time slot for "{slot.study_space.name}" at {slot.get_start_time_display()} because it has active enrollments.')
            return redirect('study_space_management:time_slot_list')
    
    slot.is_active = not slot.is_active
    slot.save()
    
    status = "activated" if slot.is_active else "deactivated"
    messages.success(request, f'Time slot for "{slot.study_space.name}" {status}.')
    return redirect('study_space_management:time_slot_list')


@login_required
def api_time_slots(request):
    """Return time slots for a given study space as JSON (for dynamic dropdowns)."""
    study_space_id = request.GET.get('study_space')
    if study_space_id:
        slots = TimeSlot.objects.filter(study_space_id=study_space_id, is_active=True).order_by('start_time')
        data = [{
            'id': slot.id,
            'start_time_display': slot.get_start_time_display(),
            'end_time_display': slot.get_end_time_display(),
        } for slot in slots]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


# ============== OCCUPANCY VIEWS ==============

@login_required
def api_occupancy_data(request):
    """
    API endpoint to get occupancy data for a specific study space and date.
    Returns JSON data for the AJAX-powered occupancy Gantt chart.
    """
    # Get parameters
    study_space_id = request.GET.get('study_space')
    date_str = request.GET.get('date')
    booking_type_filter = request.GET.get('booking_type', '')
    payment_status_filter = request.GET.get('payment_status', '')
    
    # Validate required parameters
    if not study_space_id or not date_str:
        return JsonResponse({'error': 'Missing required parameters'}, status=400)
    
    try:
        space = StudySpace.objects.get(id=study_space_id, is_active=True)
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (StudySpace.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid study space or date'}, status=400)
    
    # Generate 30-minute time slots from 9:00 to 21:00
    start_time = time(9, 0)
    end_time = time(21, 0)
    time_slots = []
    current = datetime.combine(selected_date, start_time)
    end = datetime.combine(selected_date, end_time)
    
    while current < end:
        time_slots.append({'time_label': current.strftime('%H:%M')})
        current += timedelta(minutes=30)
    
    # Get all active seats for this space
    seats = Seat.objects.filter(study_space=space, is_active=True).order_by('seat_number')
    
    # Get enrollments for this date
    enrollments = Enrollment.objects.filter(
        study_space=space,
        is_active=True,
        start_date__lte=selected_date,
        end_date__gte=selected_date
    ).select_related('student', 'seat')
    
    # Apply filters
    if booking_type_filter:
        enrollments = enrollments.filter(booking_type=booking_type_filter)
    if payment_status_filter == 'paid':
        enrollments = enrollments.filter(is_paid=True)
    elif payment_status_filter == 'unpaid':
        enrollments = enrollments.filter(is_paid=False)
    
    # Build seat data
    seat_data = []
    occupied_total = 0
    
    for seat in seats:
        seat_enrollments = enrollments.filter(seat=seat)
        
        # Determine occupied slots
        occupied_slots = [False] * len(time_slots)
        occupied_count = 0
        
        for enrollment in seat_enrollments:
            if enrollment.booking_type == 'hourly':
                if enrollment.custom_start_time and enrollment.custom_end_time:
                    start_dt = datetime.combine(selected_date, enrollment.custom_start_time)
                    end_dt = datetime.combine(selected_date, enrollment.custom_end_time)
                    for idx, slot in enumerate(time_slots):
                        slot_time = datetime.strptime(slot['time_label'], '%H:%M').time()
                        slot_dt = datetime.combine(selected_date, slot_time)
                        if start_dt <= slot_dt < end_dt:
                            occupied_slots[idx] = True
            else:
                # Daily, weekly, monthly, custom - occupy all slots
                for idx in range(len(time_slots)):
                    occupied_slots[idx] = True
        
        # Count occupied slots
        occupied_count = sum(1 for occupied in occupied_slots if occupied)
        if occupied_count > 0:
            occupied_total += 1
        
        # Build slots data
        slots_data = []
        for idx, slot in enumerate(time_slots):
            occupied = occupied_slots[idx]
            student_name = ''
            booking_type_name = ''
            
            if occupied:
                # Get first enrollment that occupies this slot
                for enrollment in seat_enrollments:
                    if enrollment.booking_type == 'hourly':
                        if enrollment.custom_start_time and enrollment.custom_end_time:
                            start_dt = datetime.combine(selected_date, enrollment.custom_start_time)
                            end_dt = datetime.combine(selected_date, enrollment.custom_end_time)
                            slot_time = datetime.strptime(slot['time_label'], '%H:%M').time()
                            slot_dt = datetime.combine(selected_date, slot_time)
                            if start_dt <= slot_dt < end_dt:
                                student_name = enrollment.student.name
                                booking_type_name = enrollment.get_booking_type_display()
                                break
                    else:
                        student_name = enrollment.student.name
                        booking_type_name = enrollment.get_booking_type_display()
                        break
            
            slots_data.append({
                'occupied': occupied,
                'student': student_name,
                'type': booking_type_name,
                'time_label': slot['time_label']
            })
        
        seat_data.append({
            'id': seat.id,
            'seat_number': seat.seat_number,
            'seat_type_display': seat.get_seat_type_display(),
            'occupied_count': occupied_count,
            'slots': slots_data,
        })
    
    total_seats = len(seat_data)
    occupied_seats = occupied_total
    available_seats = total_seats - occupied_seats
    
    response_data = {
        'space_name': space.name,
        'location': space.location or '',
        'date': selected_date.strftime('%A, %d %B %Y'),
        'time_slots': time_slots,
        'seats': seat_data,
        'total_seats': total_seats,
        'occupied_seats': occupied_seats,
        'available_seats': available_seats,
        'occupancy_percentage': (occupied_seats / total_seats * 100) if total_seats else 0,
    }
    
    return JsonResponse(response_data)


@login_required
def occupancy_gantt(request, study_space_id=None):
    """
    Display Gantt chart showing seat occupancy for a study space.
    Uses AJAX to load data per space for better performance.
    """
    # Get all study spaces for the filter dropdown
    all_study_spaces = StudySpace.objects.filter(is_active=True).order_by('name')
    
    # Default to first active space if available
    default_space_id = None
    if study_space_id:
        default_space_id = study_space_id
    elif all_study_spaces.exists():
        default_space_id = all_study_spaces.first().id
    
    today = timezone.now().date()
    
    context = {
        'study_spaces': all_study_spaces,
        'default_space_id': default_space_id,
        'today': today,
        'booking_types': Enrollment.BOOKING_TYPES,
    }
    return render(request, 'study_space_management/occupancy_gantt.html', context)


# ============== API AVAILABLE SEATS ==============

@login_required
def api_available_seats(request):
    """
    API endpoint to get available seats based on criteria.
    Returns JSON list of available seats for dropdown.
    """
    study_space_id = request.GET.get('study_space')
    booking_type = request.GET.get('booking_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    seat_type = request.GET.get('seat_type')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    
    if not study_space_id or not booking_type or not start_date or not end_date:
        return JsonResponse({'seats': [], 'available_count': 0, 'error': 'Missing required parameters'})
    
    try:
        study_space = StudySpace.objects.get(id=study_space_id, is_active=True)
        
        seats = Seat.objects.filter(study_space=study_space, is_active=True)
        
        if seat_type:
            seats = seats.filter(seat_type=seat_type)
        
        if seats.count() == 0:
            return JsonResponse({
                'seats': [],
                'available_count': 0,
                'total_count': 0,
                'occupied_count': 0,
                'message': f'No {seat_type if seat_type else "active"} seats found in {study_space.name}'
            })
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        start_time_obj = None
        end_time_obj = None
        if start_time and end_time:
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
        
        enrollments = Enrollment.objects.filter(
            study_space=study_space,
            is_active=True,
            start_date__lte=end_date_obj,
            end_date__gte=start_date_obj
        ).select_related('seat')
        
        occupied_seat_ids = set()
        
        for enrollment in enrollments:
            if not enrollment.seat:
                continue
            
            if booking_type == 'hourly' and start_time_obj and end_time_obj:
                if enrollment.booking_type == 'hourly':
                    if enrollment.custom_start_time and enrollment.custom_end_time:
                        if (enrollment.custom_start_time < end_time_obj and 
                            enrollment.custom_end_time > start_time_obj):
                            occupied_seat_ids.add(enrollment.seat_id)
                elif enrollment.booking_type in ['daily', 'weekly', 'monthly']:
                    occupied_seat_ids.add(enrollment.seat_id)
            elif booking_type in ['daily', 'weekly', 'monthly', 'custom']:
                occupied_seat_ids.add(enrollment.seat_id)
        
        available_seats = seats.exclude(id__in=occupied_seat_ids)
        
        seat_data = [{
            'id': seat.id,
            'seat_number': seat.seat_number,
            'seat_type': seat.get_seat_type_display(),
        } for seat in available_seats[:50]]
        
        return JsonResponse({
            'seats': seat_data,
            'available_count': available_seats.count(),
            'total_count': seats.count(),
            'occupied_count': len(occupied_seat_ids)
        })
        
    except StudySpace.DoesNotExist:
        return JsonResponse({'seats': [], 'available_count': 0, 'error': 'Study space not found'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'seats': [], 'available_count': 0, 'error': str(e)})