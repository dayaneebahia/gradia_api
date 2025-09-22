# tests/test_models.py
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

from finance.models import Period, Cycle, Category, FinancialRecord  # adjust import to your app label


@pytest.mark.django_db
def test_period_start_new_period_creates_12_cycles_and_is_idempotent():
    User = get_user_model()
    user = User.objects.create_user(username="u1", password="x")

    period = Period.start_new_period(user)
    assert period.title == str(timezone.now().year)
    assert period.cycles.count() == 12

    # Calling again should NOT create duplicate cycles
    period_again = Period.start_new_period(user)
    assert period_again.pk == period.pk
    assert period_again.cycles.count() == 12


@pytest.mark.django_db
def test_cycle_aggregations_and_percentages():
    User = get_user_model()
    user = User.objects.create_user(username="u2", password="x")
    period = Period.objects.create(user=user, title=str(timezone.now().year))
    cycle = Cycle.objects.create(period=period, month=1)  # name auto-fills to January

    cat_income = Category.objects.create(user=user, name="Salary")
    cat_exp = Category.objects.create(user=user, name="Rent")

    # Planned vs current for both income and expense
    FinancialRecord.objects.create(
        cycle=cycle, category=cat_income, period=period,
        type_choice=FinancialRecord.INCOME,
        current_amount=Decimal("150.00"), planned_amount=Decimal("200.00")
    )
    FinancialRecord.objects.create(
        cycle=cycle, category=cat_exp, period=period,
        type_choice=FinancialRecord.EXPENSES,
        current_amount=Decimal("90.00"), planned_amount=Decimal("100.00")
    )

    # Aggregations
    assert cycle.calculate_total_incomes() == Decimal("150.00")
    assert cycle.calculate_total_expenses() == Decimal("90.00")
    assert cycle.calculate_net_income() == Decimal("60.00")

    assert cycle.planned_calculate_total_incomes() == Decimal("200.00")
    assert cycle.planned_calculate_total_expenses() == Decimal("100.00")
    assert cycle.planned_calculate_net_income() == Decimal("100.00")

    # Differences (values)
    assert cycle.income_difference_value() == Decimal("50.00")     # 200 - 150
    assert cycle.expense_difference_value() == Decimal("10.00")    # 100 - 90
    assert cycle.net_income_difference_value() == Decimal("40.00") # 100 - 60

    # Percentages
    # income diff % = (200-150)/200 * 100 = 25.00
    assert cycle.income_difference_percentage() == Decimal("25.00")
    # expense diff % = (100-90)/100 * 100 = 10.00
    assert cycle.expense_difference_percentage() == Decimal("10.00")
    # net diff % = (100-60)/100 * 100 = 40.00
    assert cycle.net_income_difference_percentage() == Decimal("40.00")


@pytest.mark.django_db
def test_category_name_unique_per_user_case_insensitive():
    User = get_user_model()
    user = User.objects.create_user(username="u3", password="x")

    Category.objects.create(user=user, name="Utilities")
    with pytest.raises(ValidationError):
        # Same user, same name ignoring case should fail
        Category.objects.create(user=user, name="utilities")

    # Different user can use same name
    other = User.objects.create_user(username="u4", password="x")
    Category.objects.create(user=other, name="UTILITIES")  # should succeed


@pytest.mark.django_db
def test_category_code_generation_increment_and_update_on_rename():
    User = get_user_model()
    user = User.objects.create_user(username="u5", password="x")

    # Names with same first 3 letters "FOO"
    c1 = Category.objects.create(user=user, name="Food")
    c2 = Category.objects.create(user=user, name="Foobar")
    c3 = Category.objects.create(user=user, name="Footwork")

    assert c1.code.startswith("FOO")
    assert c2.code.startswith("FOO")
    assert c3.code.startswith("FOO")
    # Suffixes should increment (01, 02, 03) for the same user
    assert c1.code.endswith("01")
    assert c2.code.endswith("02")
    assert c3.code.endswith("03")

    # Renaming should update code to new base and maintain uniqueness
    c1.name = "Fuel"  # base becomes FUE
    c1.save()
    assert c1.code.startswith("FUE")
    assert c1.code.endswith("01")


@pytest.mark.django_db
def test_period_aggregates_across_cycles_and_difference_methods():
    User = get_user_model()
    user = User.objects.create_user(username="u6", password="x")
    period = Period.objects.create(user=user, title=str(timezone.now().year))
    jan = Cycle.objects.create(period=period, month=1)
    feb = Cycle.objects.create(period=period, month=2)

    cat_income = Category.objects.create(user=user, name="Salary")
    cat_exp = Category.objects.create(user=user, name="Groceries")

    # January
    FinancialRecord.objects.create(
        cycle=jan, category=cat_income, period=period,
        type_choice=FinancialRecord.INCOME,
        current_amount=Decimal("1000.00"), planned_amount=Decimal("1200.00")
    )
    FinancialRecord.objects.create(
        cycle=jan, category=cat_exp, period=period,
        type_choice=FinancialRecord.EXPENSES,
        current_amount=Decimal("300.00"), planned_amount=Decimal("250.00")
    )

    # February
    FinancialRecord.objects.create(
        cycle=feb, category=cat_income, period=period,
        type_choice=FinancialRecord.INCOME,
        current_amount=Decimal("800.00"), planned_amount=Decimal("800.00")
    )
    FinancialRecord.objects.create(
        cycle=feb, category=cat_exp, period=period,
        type_choice=FinancialRecord.EXPENSES,
        current_amount=Decimal("200.00"), planned_amount=Decimal("220.00")
    )

    # Period totals
    incomes = period.calculate_total_incomes()           # 1000 + 800 = 1800
    expenses = period.calculate_total_expenses()         # 300 + 200 = 500
    planned_incomes = period.planned_calculate_total_incomes()   # 1200 + 800 = 2000
    planned_expenses = period.planned_calculate_total_expenses() # 250 + 220 = 470

    assert incomes == Decimal("1800.00")
    assert expenses == Decimal("500.00")
    assert period.calculate_net_income() == Decimal("1300.00")

    assert planned_incomes == Decimal("2000.00")
    assert planned_expenses == Decimal("470.00")
    assert period.planned_calculate_net_income() == Decimal("1530.00")

    # Differences (values) at period level
    assert period.income_difference_value() == Decimal("200.00")      # 2000 - 1800
    assert period.expense_difference_value() == Decimal("-30.00")     # 470 - 500
    assert period.net_income_difference_value() == Decimal("230.00")  # 1530 - 1300

    # Percentages at period level (note: model returns 0/float if planned == 0; here planned > 0)
    assert period.income_difference_percentage() == Decimal("10.00")  # (200/2000)*100
    # For expenses: (-30 / 470) * 100 ≈ -6.382...
    assert round(period.expense_difference_percentage(), 2) == Decimal("-6.38")
    # Net income: (230 / 1530) * 100 ≈ 15.03
    assert round(period.net_income_difference_percentage(), 2) == Decimal("15.03")
