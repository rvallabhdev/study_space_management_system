# operations_management/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from datetime import date
from decimal import Decimal, InvalidOperation
from .models import Enrollment, Pricing, Payment
from .forms import EnrollmentForm
from study_space_management.models import Student, StudySpace, Seat


@login_required
def enrollment_list(request):
    """
    List all active enrollments with optional filters.
    Supports filtering by student, study space, and booking type.
    """
    # Base queryset with select_related for performance
    enrollments = Enrollment.objects.filter(is_active=True).select_related(
        'student', 'study_space', 'seat', 'pricing'
    )
    
    # Get filter parameters
    student_id = request.GET.get('student')
    space_id = request.GET.get('space')
    booking_type = request.GET.get('booking_type')
    search_query = request.GET.get('search', '')
    
    # Apply filters
    if student_id:
        enrollments = enrollments.filter(student__id=student_id)
    
    if space_id:
        enrollments = enrollments.filter(study_space__id=space_id)
    
    if booking_type:
        enrollments = enrollments.filter(booking_type=booking_type)
    
    # Search by student name or mobile
    if search_query:
        enrollments = enrollments.filter(
            Q(student__name__icontains=search_query) |
            Q(student__mobile__icontains=search_query)
        )
    
    # Get data for filter dropdowns
    students = Student.objects.filter(active=True).order_by('name')[:100]
    study_spaces = StudySpace.objects.filter(is_active=True).order_by('name')
    
    context = {
        'enrollments': enrollments,
        'students': students,
        'study_spaces': study_spaces,
        'booking_types': Enrollment.BOOKING_TYPES,
        'selected_student': student_id,
        'selected_space': space_id,
        'selected_booking_type': booking_type,
        'search_query': search_query,
    }
    return render(request, 'operations_management/enrollment_list.html', context)


@login_required
def enrollment_create(request):
    """Create a new enrollment with live price calculation."""
    # Get data for dropdowns
    students = Student.objects.filter(active=True).order_by('name')
    study_spaces = StudySpace.objects.filter(is_active=True).order_by('name')
    
    # Get pricing plans as a list of dictionaries (JSON serializable)
    pricing_plans = Pricing.objects.filter(is_active=True).values(
        'id', 'name', 'pricing_type', 'seat_type',
        'price_per_hour', 'price_per_day', 'price_per_week', 'price_per_month', 'custom_price'
    )
    pricing_plans_list = list(pricing_plans)
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            context = {
                'form': form,
                'students': students,
                'study_spaces': study_spaces,
                'pricing_plans': pricing_plans_list,
                'booking_types': Enrollment.BOOKING_TYPES,
            }
            return render(request, 'operations_management/enrollment_form.html', context)
        
        try:
            with transaction.atomic():
                enrollment = form.save(commit=False)
                enrollment.created_by = request.user
                
                # ========== HANDLE HOURLY BOOKING ==========
                if enrollment.booking_type == 'hourly':
                    custom_start = request.POST.get('custom_start_time')
                    custom_end = request.POST.get('custom_end_time')
                    
                    if custom_start and custom_end:
                        enrollment.custom_start_time = custom_start + ':00'
                        enrollment.custom_end_time = custom_end + ':00'
                    else:
                        messages.error(request, 'Please select both start and end times for hourly booking.')
                        context = {
                            'form': form,
                            'students': students,
                            'study_spaces': study_spaces,
                            'pricing_plans': pricing_plans_list,
                            'booking_types': Enrollment.BOOKING_TYPES,
                        }
                        return render(request, 'operations_management/enrollment_form.html', context)
                
                # ========== HANDLE WEEKLY BOOKING ==========
                elif enrollment.booking_type == 'weekly':
                    enrollment.hours_per_day = request.POST.get('hours_per_day')
                    enrollment.days_of_week = request.POST.get('days_of_week')
                    
                    if not enrollment.hours_per_day or not enrollment.days_of_week:
                        messages.error(request, 'Please enter hours per day and select days for weekly booking.')
                        context = {
                            'form': form,
                            'students': students,
                            'study_spaces': study_spaces,
                            'pricing_plans': pricing_plans_list,
                            'booking_types': Enrollment.BOOKING_TYPES,
                        }
                        return render(request, 'operations_management/enrollment_form.html', context)
                
                # ========== HANDLE MONTHLY BOOKING ==========
                elif enrollment.booking_type == 'monthly':
                    enrollment.hours_per_day = request.POST.get('hours_per_day_monthly')
                    
                    if not enrollment.hours_per_day:
                        messages.error(request, 'Please enter hours per day for monthly booking.')
                        context = {
                            'form': form,
                            'students': students,
                            'study_spaces': study_spaces,
                            'pricing_plans': pricing_plans_list,
                            'booking_types': Enrollment.BOOKING_TYPES,
                        }
                        return render(request, 'operations_management/enrollment_form.html', context)
                
                # ========== HANDLE CUSTOM PRICE ==========
                custom_price = request.POST.get('custom_price')
                if custom_price and float(custom_price) > 0:
                    enrollment.custom_price = custom_price
                    enrollment.total_amount = custom_price
                else:
                    total_amount = request.POST.get('total_amount')
                    if total_amount:
                        enrollment.total_amount = total_amount
                
                # ========== SET SEAT ==========
                seat_id = request.POST.get('seat')
                if seat_id:
                    enrollment.seat_id = seat_id
                
                enrollment.save()
                
            messages.success(request, f'Enrollment created for {enrollment.student.name}')
            return redirect('operations_management:enrollment_detail', pk=enrollment.pk)
            
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        if field == '__all__':
                            messages.error(request, error)
                        else:
                            messages.error(request, f'{field}: {error}')
            else:
                messages.error(request, str(e))
            context = {
                'form': form,
                'students': students,
                'study_spaces': study_spaces,
                'pricing_plans': pricing_plans_list,
                'booking_types': Enrollment.BOOKING_TYPES,
            }
            return render(request, 'operations_management/enrollment_form.html', context)
        except Exception as e:
            messages.error(request, f'Error creating enrollment: {str(e)}')
            context = {
                'form': form,
                'students': students,
                'study_spaces': study_spaces,
                'pricing_plans': pricing_plans_list,
                'booking_types': Enrollment.BOOKING_TYPES,
            }
            return render(request, 'operations_management/enrollment_form.html', context)
    else:
        form = EnrollmentForm()
    
    context = {
        'form': form,
        'students': students,
        'study_spaces': study_spaces,
        'pricing_plans': pricing_plans_list,
        'booking_types': Enrollment.BOOKING_TYPES,
    }
    return render(request, 'operations_management/enrollment_form.html', context)


@login_required
def enrollment_detail(request, pk):
    """
    Show detailed information for a single enrollment.
    Includes student details, space details, pricing breakdown, and payment status.
    """
    enrollment = get_object_or_404(
        Enrollment.objects.select_related(
            'student', 'study_space', 'seat', 'pricing', 'created_by'
        ),
        pk=pk
    )
    
    # Calculate total paid from payments
    total_paid = Payment.objects.filter(enrollment=enrollment).aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = (enrollment.total_amount - total_paid) if enrollment.total_amount else 0
    
    context = {
        'enrollment': enrollment,
        'total_days': enrollment.get_total_days(),
        'total_weeks': enrollment.get_total_weeks(),
        'total_months': enrollment.get_total_months(),
        'total_hours': enrollment.get_total_hours(),
        'payment_status': 'Paid' if enrollment.is_paid else 'Pending',
        'status_badge_class': 'success' if enrollment.is_active else 'secondary',
        'payment_badge_class': 'success' if enrollment.is_paid else 'warning',
        'total_paid': total_paid,
        'pending_amount': pending_amount,
    }
    return render(request, 'operations_management/enrollment_detail.html', context)


@login_required
def enrollment_cancel(request, pk):
    """
    Cancel an active enrollment (soft delete).
    Shows confirmation page with enrollment details before cancellation.
    """
    enrollment = get_object_or_404(Enrollment, pk=pk)
    
    # Check if enrollment is already cancelled
    if not enrollment.is_active:
        messages.info(request, 'This enrollment is already cancelled.')
        return redirect('operations_management:enrollment_detail', pk=enrollment.pk)
    
    if request.method == 'POST':
        # Confirm cancellation
        student_name = enrollment.student.name
        enrollment.is_active = False
        enrollment.save()
        
        messages.success(
            request, 
            f'Enrollment for {student_name} in {enrollment.study_space.name} has been cancelled.'
        )
        return redirect('operations_management:enrollment_list')
    
    # GET request - show confirmation page
    context = {
        'enrollment': enrollment,
        'total_days': enrollment.get_total_days(),
        'total_amount': enrollment.total_amount,
    }
    return render(request, 'operations_management/enrollment_confirm_cancel.html', context)


@login_required
def enrollment_payment(request, pk):
    """
    Record a payment for an enrollment.
    """
    enrollment = get_object_or_404(Enrollment, pk=pk)
    
    # Calculate total paid and pending amount
    total_paid = Payment.objects.filter(enrollment=enrollment).aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = (enrollment.total_amount - total_paid) if enrollment.total_amount else 0
    
    # Check if enrollment is already fully paid
    if enrollment.is_paid:
        messages.info(request, 'This enrollment is already fully paid.')
        return redirect('operations_management:enrollment_detail', pk=enrollment.pk)
    
    if request.method == 'POST':
        # Get payment details from form
        amount = request.POST.get('amount')
        payment_date = request.POST.get('payment_date')
        payment_mode = request.POST.get('payment_mode')
        receipt_number = request.POST.get('receipt_number')
        notes = request.POST.get('notes', '')
        
        # Validate amount
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, 'Payment amount must be greater than zero.')
                return redirect('operations_management:enrollment_payment', pk=enrollment.pk)
            
            # Check if payment exceeds pending amount
            if amount > pending_amount:
                messages.error(request, f'Payment amount cannot exceed pending amount of ₹{pending_amount:,.2f}.')
                return redirect('operations_management:enrollment_payment', pk=enrollment.pk)
                
        except (InvalidOperation, TypeError, ValueError):
            messages.error(request, 'Invalid payment amount.')
            return redirect('operations_management:enrollment_payment', pk=enrollment.pk)
        
        # Validate payment date
        try:
            payment_date_obj = date.fromisoformat(payment_date) if payment_date else date.today()
        except ValueError:
            messages.error(request, 'Invalid payment date.')
            return redirect('operations_management:enrollment_payment', pk=enrollment.pk)

        # Validate payment mode
        if not payment_mode:
            messages.error(request, 'Please select a payment mode.')
            return redirect('operations_management:enrollment_payment', pk=enrollment.pk)
        
        # Create payment record
        try:
            with transaction.atomic():
                payment = Payment.objects.create(
                    enrollment=enrollment,
                    amount=amount,
                    payment_date=payment_date_obj,
                    payment_mode=payment_mode,
                    receipt_number=receipt_number if receipt_number else None,
                    notes=notes,
                    created_by=request.user
                )
                
                # Update enrollment paid status
                new_total_paid = total_paid + amount
                enrollment.is_paid = new_total_paid >= enrollment.total_amount
                enrollment.save()
                
            messages.success(
                request, 
                f'Payment of ₹{amount:,.2f} recorded successfully. '
                f'Receipt No: {payment.receipt_number}'
            )
            return redirect('operations_management:enrollment_detail', pk=enrollment.pk)
            
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
            return redirect('operations_management:enrollment_payment', pk=enrollment.pk)
    
    # GET request - show payment form
    context = {
        'enrollment': enrollment,
        'total_paid': total_paid,
        'pending_amount': pending_amount,
        'half_pending_amount': pending_amount / Decimal('2') if pending_amount else Decimal('0'),
        'today': date.today(),
        'payment_modes': Payment.PAYMENT_MODES,
    }
    return render(request, 'operations_management/enrollment_payment.html', context)