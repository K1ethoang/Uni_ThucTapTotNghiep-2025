from django.contrib import admin

from applications.employee.models import Employee, Department, DeptManager, Title, Salary, DeptEmp

# Register your models here.
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('emp_no', 'first_name', 'last_name', 'gender',)
    search_fields = ('emp_no', 'first_name', 'last_name', 'gender',)
    list_filter = ('gender',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('dept_no', 'dept_name', )
    search_fields = ('dept_name',)


@admin.register(DeptManager)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('emp_no', 'dept_no',)
    search_fields = ('emp_no',)


@admin.register(Title)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'emp_no', 'from_date', 'to_date',)
    search_fields = ('dept_name',)


@admin.register(DeptEmp)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('emp_no', 'dept_no',)
    search_fields = ('emp_no',)
    list_filter = ('dept_no',)


@admin.register(Salary)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('emp_no', 'salary', 'from_date', 'to_date',)
    search_fields = ('emp_no',)
