from rest_framework import serializers
from app.models import Employee
 
 
class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
 
 
'''class PerformanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)  # Add employee_id
 
    class Meta:
        model = Performance
        fields = ['id', 'employee', 'employee_name', 'performance_score', 'date', 'employee_id']'''