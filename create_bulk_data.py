#!/usr/bin/env python
import os
import sys
import django
import random
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_space_management_system.settings')
django.setup()

from study_space_management.models import Student

print("\n" + "="*70)
print("  CREATING 5000 STUDENTS (SIMPLE VERSION)")
print("="*70 + "\n")

first_names = ['Aarav', 'Vihaan', 'Vivaan', 'Advik', 'Kabir', 'Reyansh', 'Sai', 'Arjun', 
               'Aadhya', 'Anaya', 'Ira', 'Sara', 'Myra', 'Aanya', 'Kiara', 'Riya']

last_names = ['Sharma', 'Verma', 'Gupta', 'Kumar', 'Singh', 'Patel', 'Yadav', 'Jain']

courses = ['B.Tech CSE', 'B.Tech ECE', 'MBA', 'MCA', 'BCA', 'B.Com']
institutes = ['IIT Delhi', 'IIT Bombay', 'NIT Trichy', 'Delhi University', 'BITS Pilani']
cities = ['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata']

existing_aadhaars = set()
existing_mobiles = set()

def generate_aadhaar():
    while True:
        aadhaar = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        if aadhaar not in existing_aadhaars:
            existing_aadhaars.add(aadhaar)
            return aadhaar

def generate_mobile():
    while True:
        mobile = '9' + ''.join([str(random.randint(0, 9)) for _ in range(9)])
        if mobile not in existing_mobiles:
            existing_mobiles.add(mobile)
            return mobile

total = 5000
batch_size = 100

for batch_start in range(0, total, batch_size):
    batch_end = min(batch_start + batch_size, total)
    students = []
    
    for i in range(batch_start, batch_end):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        mobile = generate_mobile()
        aadhaar = generate_aadhaar()
        
        student = Student(
            name=name,
            mobile=mobile,
            aadhaar_number=aadhaar,
            father_name=f"{random.choice(first_names)} {random.choice(last_names)}",
            father_mobile=generate_mobile(),
            course_name=random.choice(courses),
            institute_name=random.choice(institutes),
            date_of_joining=date.today() - timedelta(days=random.randint(0, 365*3)),
            permanent_address=f"{random.randint(1, 999)} Main St, {random.choice(cities)}",
            local_address=f"{random.randint(1, 999)} Local St, {random.choice(cities)}",
            active=random.random() < 0.9
        )
        students.append(student)
    
    Student.objects.bulk_create(students)
    print(f"  ✓ Created {batch_end}/{total} students")

print(f"\n✓ Total Students Created: {Student.objects.count()}")
print("\nSetup complete!")