from django.db import models


class Employee(models.Model):
    emp_no = models.AutoField(primary_key=True)
    birth_date = models.DateField()
    first_name = models.CharField(max_length=14)
    last_name = models.CharField(max_length=16)
    gender = models.CharField(max_length=1, choices=[("M", "Male"), ("F", "Female")])
    hire_date = models.DateField()

    class Meta:
        db_table = "employees"

    def __str__(self):
        return f"{self.emp_no} - {self.first_name} {self.last_name}"


class Department(models.Model):
    dept_no = models.CharField(primary_key=True, max_length=4)
    dept_name = models.CharField(unique=True, max_length=40)

    class Meta:
        db_table = "departments"

    def __str__(self):
        return self.dept_name


class DeptEmp(models.Model):
    emp_no = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column="emp_no")
    dept_no = models.ForeignKey(Department, on_delete=models.CASCADE, db_column="dept_no")
    from_date = models.DateField()
    to_date = models.DateField()

    class Meta:
        db_table = "dept_emp"
        unique_together = (("emp_no", "dept_no"),)

    def __str__(self):
        return f"{self.emp_no} - {self.dept_no}"


class DeptManager(models.Model):
    emp_no = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column="emp_no")
    dept_no = models.ForeignKey(Department, on_delete=models.CASCADE, db_column="dept_no")
    from_date = models.DateField()
    to_date = models.DateField()

    class Meta:
        db_table = "dept_manager"
        unique_together = (("emp_no", "dept_no"),)

    def __str__(self):
        return f"Manager {self.emp_no} - {self.dept_no}"


class Salary(models.Model):
    emp_no = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column="emp_no")
    salary = models.IntegerField()
    from_date = models.DateField()
    to_date = models.DateField()

    class Meta:
        db_table = "salaries"
        unique_together = (("emp_no", "from_date"),)

    def __str__(self):
        return f"{self.emp_no} - {self.salary}"


class Title(models.Model):
    emp_no = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column="emp_no")
    title = models.CharField(max_length=50)
    from_date = models.DateField()
    to_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "titles"
        unique_together = (("emp_no", "title", "from_date"),)

    def __str__(self):
        return f"{self.emp_no} - {self.title}"
