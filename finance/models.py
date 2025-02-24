import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal


class Period(models.Model):
    """Represents a financial year with 12 monthly cycles for a user."""
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='periods'
    )
    title = models.CharField(max_length=4)  # Year as a string, e.g., "2024"
    is_archived = models.BooleanField(default=False)  # Marks the period as archived or active
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Period {self.title}"

    def calculate_total_incomes(self):
        """Calculate total incomes for the period."""
        return (self.cycles.aggregate(total=Sum("financial_records__current_amount",
                                                filter=Q(financial_records__type_choice="income"))).get("total") or 0)

    def calculate_total_expenses(self):
        """Calculate total expenses for the period."""
        return (self.cycles.aggregate(total=Sum("financial_records__current_amount",
                                                filter=Q(financial_records__type_choice="expenses"))).get("total") or 0)

    def calculate_net_income(self):
        """Calculate net income for the period."""
        return self.calculate_total_incomes() - self.calculate_total_expenses()

    def planned_calculate_total_incomes(self):
        """Calculate total planned incomes for the period."""
        return (self.cycles.aggregate(total=Sum("financial_records__planned_amount",
                                                filter=Q(financial_records__type_choice="income"))).get("total") or 0)

    def planned_calculate_total_expenses(self):
        """Calculate total planned expenses for the period."""
        return (self.cycles.aggregate(total=Sum("financial_records__planned_amount",
                                                filter=Q(financial_records__type_choice="expenses"))).get("total") or 0)

    def planned_calculate_net_income(self):
        """Calculate planned net income for the period."""
        return self.planned_calculate_total_incomes() - self.planned_calculate_total_expenses()

    def income_difference_value(self):
        """Calculate the difference in dollars between planned and current incomes."""
        return self.planned_calculate_total_incomes() - self.calculate_total_incomes()

    def income_difference_percentage(self):
        """Calculate the percentage difference between planned and current incomes."""
        planned = self.planned_calculate_total_incomes()
        if planned == 0:
            return 0  # Avoid division by zero
        return ((self.planned_calculate_total_incomes() - self.calculate_total_incomes()) / planned) * 100

    def expense_difference_value(self):
        """Calculate the difference in dollars between planned and current expenses."""
        return self.planned_calculate_total_expenses() - self.calculate_total_expenses()

    def expense_difference_percentage(self):
        """Calculate the percentage difference between planned and current expenses."""
        planned = self.planned_calculate_total_expenses()
        if planned == 0:
            return 0  # Avoid division by zero
        return ((self.planned_calculate_total_expenses() - self.calculate_total_expenses()) / planned) * 100

    def net_income_difference_value(self):
        """Calculate the difference in dollars between planned and actual net income."""
        return self.planned_calculate_net_income() - self.calculate_net_income()

    def net_income_difference_percentage(self):
        """Calculate the percentage difference between planned and actual net income."""
        planned_net_income = self.planned_calculate_net_income()
        if planned_net_income == 0:
            return 0  # Avoid division by zero
        return ((self.planned_calculate_net_income() - self.calculate_net_income()) / planned_net_income) * 100

    def create_cycles(self):
        """Create 12 monthly cycles for this period."""
        MONTH_NAMES = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        for month in range(1, 13):  # Months 1 to 12
            if not self.cycles.filter(month=month).exists():  # Avoid duplicates
                self.cycles.create(month=month, name=MONTH_NAMES[month - 1])

    @classmethod
    def start_new_period(cls, user):
        """Create a new period for the current year and archive the previous active period."""
        current_year = str(timezone.now().year)

        # Create or retrieve the current year's period
        period, created = cls.objects.get_or_create(
            user=user,
            title=current_year,
            defaults={'is_archived': False}
        )

        if created:
            print(f"Creating cycles for the new period: {current_year}")
            period.create_cycles()  # Automatically create cycles for the new period

        return period


class Cycle(models.Model):
    """Represents a month (cycle) within a specific period."""
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    period = models.ForeignKey(
        Period,
        related_name='cycles',
        on_delete=models.CASCADE,
    )
    month = models.PositiveSmallIntegerField()  # 1 = January, 12 = December
    name = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ('period', 'month')

    def save(self, *args, **kwargs):
        MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        if not self.name:
            self.name = MONTH_NAMES[self.month - 1]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.period.title}"

    # Calculation Methods

    def calculate_total_incomes(self):
        """Calculate total incomes for the cycle."""
        return self.financial_records.aggregate(
            total=Sum("current_amount", filter=Q(type_choice=FinancialRecord.INCOME))
        ).get("total") or Decimal("0.00")

    def calculate_total_expenses(self):
        """Calculate total expenses for the cycle."""
        return self.financial_records.aggregate(
            total=Sum("current_amount", filter=Q(type_choice=FinancialRecord.EXPENSES))
        ).get("total") or Decimal("0.00")

    def calculate_net_income(self):
        """Calculate net income for the cycle."""
        return self.calculate_total_incomes() - self.calculate_total_expenses()

    def planned_calculate_total_incomes(self):
        """Calculate total planned incomes for the cycle."""
        return self.financial_records.aggregate(
            total=Sum("planned_amount", filter=Q(type_choice=FinancialRecord.INCOME))
        ).get("total") or Decimal("0.00")

    def planned_calculate_total_expenses(self):
        """Calculate total planned expenses for the cycle."""
        return self.financial_records.aggregate(
            total=Sum("planned_amount", filter=Q(type_choice=FinancialRecord.EXPENSES))
        ).get("total") or Decimal("0.00")

    def planned_calculate_net_income(self):
        """Calculate planned net income for the cycle."""
        return self.planned_calculate_total_incomes() - self.planned_calculate_total_expenses()

    def income_difference_value(self):
        """Calculate the difference in dollars between planned and current incomes."""
        return self.planned_calculate_total_incomes() - self.calculate_total_incomes()

    def income_difference_percentage(self):
        """Calculate the percentage difference between planned and current incomes."""
        planned = self.planned_calculate_total_incomes()
        if planned == 0:
            return Decimal("0.00")  # Avoid division by zero
        return ((self.planned_calculate_total_incomes() - self.calculate_total_incomes()) / planned) * Decimal("100.00")

    def expense_difference_value(self):
        """Calculate the difference in dollars between planned and current expenses."""
        return self.planned_calculate_total_expenses() - self.calculate_total_expenses()

    def expense_difference_percentage(self):
        """Calculate the percentage difference between planned and current expenses."""
        planned = self.planned_calculate_total_expenses()
        if planned == 0:
            return Decimal("0.00")  # Avoid division by zero
        return ((self.planned_calculate_total_expenses() - self.calculate_total_expenses()) / planned) * Decimal(
            "100.00")

    def net_income_difference_value(self):
        """Calculate the difference in dollars between planned and current net income."""
        return self.planned_calculate_net_income() - self.calculate_net_income()

    def net_income_difference_percentage(self):
        """Calculate the percentage difference between planned and current net income."""
        planned_net_income = self.planned_calculate_net_income()
        if planned_net_income == 0:
            return Decimal("0.00")  # Avoid division by zero
        return ((self.planned_calculate_net_income() - self.calculate_net_income()) / planned_net_income) * Decimal(
            "100.00")


class Category(models.Model):
    """Category model, now tied to a specific user."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories"
    )
    name = models.CharField(max_length=75)
    code = models.CharField(max_length=10, blank=True, editable=False)
    description = models.TextField(blank=True, default="")

    class Meta:
        # Enforce code uniqueness for each user
        constraints = [
            models.UniqueConstraint(fields=['user', 'code'], name='unique_user_category_code')
        ]

    def clean(self):
        """Validate that the category name is unique for the user (case-insensitive)."""
        if Category.objects.filter(user=self.user, name__iexact=self.name).exclude(pk=self.pk).exists():
            raise ValidationError(f"A category with the name '{self.name}' already exists for this user.")

    def save(self, *args, **kwargs):
        try:
            self.full_clean()  # Validate the instance
            if not self.code or self.has_name_changed():
                self.code = self.generate_code()
            super().save(*args, **kwargs)
        except IntegrityError as e:
            raise ValidationError(f"Integrity error: {e}")

    def has_name_changed(self):
        """Check if the name has changed to trigger a code update."""
        if self.pk is None:
            return False  # New instance
        old_name = Category.objects.get(pk=self.pk).name
        return old_name != self.name

    def generate_code(self):
        """Generate a unique code for the category for a specific user."""
        base_code = self.name[:3].upper()  # Take the first 3 letters of the name
        existing_codes = Category.objects.filter(
            user=self.user,
            code__startswith=base_code
        ).values_list("code", flat=True)

        suffix = 1
        while True:
            new_code = f"{base_code}{suffix:02d}"
            if new_code not in existing_codes:
                break
            suffix += 1

        return new_code


class FinancialRecord(models.Model):
    """Represents a financial record within a specific cycle."""
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    cycle = models.ForeignKey(
        Cycle,
        related_name='financial_records',
        on_delete=models.CASCADE,
    )
    INCOME = "income"
    EXPENSES = "expenses"
    TYPE_CHOICES = [(INCOME, "Income"), (EXPENSES, "Expenses")]

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="financial_records"
    )
    period = models.ForeignKey(
        Period,
        related_name='financial_records',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    type_choice = models.CharField(max_length=8, choices=TYPE_CHOICES, default=EXPENSES)
    current_amount = models.DecimalField(max_digits=13, decimal_places=2, default=Decimal("0.00"))
    planned_amount = models.DecimalField(max_digits=13, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    firebase_uid = models.CharField(max_length=255, blank=True, null=True)  # Firebase UID field

    def __str__(self):
        period_name = self.period.title if self.period else "No Period"
        return f"{self.type_choice.capitalize()} - {self.category.name} ({self.cycle.name}, {period_name}): Current={self.current_amount}, Planned={self.planned_amount}"

