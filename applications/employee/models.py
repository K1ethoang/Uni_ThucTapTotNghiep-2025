from django.db import models


class Department(models.Model):
    dept_no = models.CharField(primary_key=True, max_length=4)
    dept_name = models.CharField(unique=True, max_length=40)

    class Meta:
        managed = False
        db_table = 'departments'

    def __str__(self):
        return f'{self.dept_name}'


class DeptEmp(models.Model):
    emp_no = models.OneToOneField('Employee', models.DO_NOTHING, db_column='emp_no', primary_key=True)  # The composite primary key (emp_no, dept_no) found, that is not supported. The first column is selected.
    dept_no = models.ForeignKey(Department, models.DO_NOTHING, db_column='dept_no')
    from_date = models.DateField()
    to_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'dept_emp'
        unique_together = (('emp_no', 'dept_no'),)

    def __str__(self):
        return f'{self.emp_no} - {self.dept_no}'


class DeptManager(models.Model):
    emp_no = models.OneToOneField('Employee', models.DO_NOTHING, db_column='emp_no', primary_key=True)  # The composite primary key (emp_no, dept_no) found, that is not supported. The first column is selected.
    dept_no = models.ForeignKey(Department, models.DO_NOTHING, db_column='dept_no')
    from_date = models.DateField()
    to_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'dept_manager'
        unique_together = (('emp_no', 'dept_no'),)

    def __str__(self):
        return f'{self.emp_no} - {self.dept_no}'


class Employee(models.Model):
    emp_no = models.IntegerField(primary_key=True)
    birth_date = models.DateField()
    first_name = models.CharField(max_length=14)
    last_name = models.CharField(max_length=16)
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    hire_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'employees'

    def __str__(self):
        return f'{self.emp_no} - {self.first_name} {self.last_name}'


class Salary(models.Model):
    emp_no = models.OneToOneField(Employee, models.DO_NOTHING, db_column='emp_no', primary_key=True)  # The composite primary key (emp_no, from_date) found, that is not supported. The first column is selected.
    salary = models.IntegerField()
    from_date = models.DateField()
    to_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'salaries'
        unique_together = (('emp_no', 'from_date'),)

    def __str__(self):
        return f'{self.emp_no} - from {self.from_date} to {self.to_date}'


class Title(models.Model):
    emp_no = models.OneToOneField(Employee, models.DO_NOTHING, db_column='emp_no', primary_key=True)  # The composite primary key (emp_no, title, from_date) found, that is not supported. The first column is selected.
    title = models.CharField(max_length=50)
    from_date = models.DateField()
    to_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'titles'
        unique_together = (('emp_no', 'title', 'from_date'),)

    def __str__(self):
        return f'{self.emp_no} - {self.title}'