# serializers.py
from rest_framework import serializers
from .models import Period, Cycle, FinancialRecord, Category
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field
from decimal import Decimal


class VerifyTokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User"""

    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class PeriodForCycleSerializer(serializers.ModelSerializer):
    """Serializer to provide minimal period details within Cycle"""

    class Meta:
        model = Period
        fields = ['id', 'title']  # Only include the fields you need


class CycleSerializer(serializers.ModelSerializer):
    """Serializer for Cycle model, including period details and calculated fields."""

    period = PeriodForCycleSerializer(read_only=True)
    total_incomes = serializers.SerializerMethodField()
    total_expenses = serializers.SerializerMethodField()
    net_income = serializers.SerializerMethodField()
    planned_total_incomes = serializers.SerializerMethodField()
    planned_total_expenses = serializers.SerializerMethodField()
    planned_net_income = serializers.SerializerMethodField()
    income_difference_value = serializers.SerializerMethodField()
    income_difference_percentage = serializers.SerializerMethodField()
    expense_difference_value = serializers.SerializerMethodField()
    expense_difference_percentage = serializers.SerializerMethodField()
    net_income_difference_value = serializers.SerializerMethodField()
    net_income_difference_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Cycle
        fields = [
            'id', 'month', 'name', 'period',
            'total_incomes', 'total_expenses', 'net_income',
            'planned_total_incomes', 'planned_total_expenses', 'planned_net_income',
            'income_difference_value', 'income_difference_percentage',
            'expense_difference_value', 'expense_difference_percentage',
            'net_income_difference_value', 'net_income_difference_percentage',
        ]

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_total_incomes(self, obj):
        """Retrieve total incomes for the cycle."""
        return obj.calculate_total_incomes()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_total_expenses(self, obj):
        """Retrieve total expenses for the cycle."""
        return obj.calculate_total_expenses()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_net_income(self, obj):
        """Retrieve net income for the cycle."""
        return obj.calculate_net_income()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_planned_total_incomes(self, obj):
        """Retrieve planned total incomes for the cycle."""
        return obj.planned_calculate_total_incomes()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_planned_total_expenses(self, obj):
        """Retrieve planned total expenses for the cycle."""
        return obj.planned_calculate_total_expenses()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_planned_net_income(self, obj):
        """Retrieve planned net income for the cycle."""
        return obj.planned_calculate_net_income()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_income_difference_value(self, obj):
        """Retrieve the difference in value between planned and actual incomes."""
        return obj.income_difference_value()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_income_difference_percentage(self, obj):
        """Retrieve the percentage difference between planned and actual incomes."""
        return obj.income_difference_percentage()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_expense_difference_value(self, obj):
        """Retrieve the difference in value between planned and actual expenses."""
        return obj.expense_difference_value()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_expense_difference_percentage(self, obj):
        """Retrieve the percentage difference between planned and actual expenses."""
        return obj.expense_difference_percentage()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_net_income_difference_value(self, obj):
        """Retrieve the difference in value between planned and actual net income."""
        return obj.net_income_difference_value()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_net_income_difference_percentage(self, obj):
        """Retrieve the percentage difference between planned and actual net income."""
        return obj.net_income_difference_percentage()


class PeriodSerializer(serializers.ModelSerializer):
    """Serializer for Period model with summaries."""
    total_incomes = serializers.SerializerMethodField()
    total_expenses = serializers.SerializerMethodField()
    net_income = serializers.SerializerMethodField()
    planned_total_incomes = serializers.SerializerMethodField()
    planned_total_expenses = serializers.SerializerMethodField()
    planned_net_income = serializers.SerializerMethodField()
    expense_difference_value = serializers.SerializerMethodField()
    expense_difference_percentage = serializers.SerializerMethodField()
    income_difference_value = serializers.SerializerMethodField()
    income_difference_percentage = serializers.SerializerMethodField()
    net_income_difference_value = serializers.SerializerMethodField()
    net_income_difference_percentage = serializers.SerializerMethodField()
    cycles = CycleSerializer(many=True, read_only=True)

    class Meta:
        model = Period
        fields = [
            'id', 'title', 'user', 'is_archived', 'created_at',
            'total_incomes', 'total_expenses', 'net_income',
            'planned_total_incomes', 'planned_total_expenses', 'planned_net_income', 'cycles',
            'expense_difference_value', 'expense_difference_percentage',
            'income_difference_value', 'income_difference_percentage',
            'net_income_difference_value', 'net_income_difference_percentage'
        ]
        read_only_fields = ['id', 'user', 'created_at']

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_total_incomes(self, obj):
        """Retrieve total incomes for the period."""
        return obj.calculate_total_incomes()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_total_expenses(self, obj):
        """Retrieve total expenses for the period."""
        return obj.calculate_total_expenses()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_net_income(self, obj):
        """Retrieve net income for the period."""
        return obj.calculate_net_income()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_planned_total_incomes(self, obj):
        """Retrieve planned total incomes for the period."""
        return obj.planned_calculate_total_incomes()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_planned_total_expenses(self, obj):
        """Retrieve planned total expenses for the period."""
        return obj.planned_calculate_total_expenses()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_planned_net_income(self, obj):
        """Retrieve planned net income for the period."""
        return obj.planned_calculate_net_income()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_expense_difference_value(self, obj):
        """Calculate the difference between planned and current expenses in value."""
        return obj.planned_calculate_total_expenses() - obj.calculate_total_expenses()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_expense_difference_percentage(self, obj):
        """Calculate the percentage difference between planned and current expenses."""
        planned_expenses = obj.planned_calculate_total_expenses()
        if planned_expenses == 0:
            return 0  # Avoid division by zero
        return ((planned_expenses - obj.calculate_total_expenses()) / planned_expenses) * 100

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_income_difference_value(self, obj):
        """Calculate the difference between planned and current incomes in value."""
        return obj.planned_calculate_total_incomes() - obj.calculate_total_incomes()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_income_difference_percentage(self, obj):
        """Calculate the percentage difference between planned and current incomes."""
        planned_incomes = obj.planned_calculate_total_incomes()
        if planned_incomes == 0:
            return 0  # Avoid division by zero
        return ((planned_incomes - obj.calculate_total_incomes()) / planned_incomes) * 100

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_net_income_difference_value(self, obj):
        """Calculate the difference between planned and current net incomes in value."""
        return obj.planned_calculate_net_income() - obj.calculate_net_income()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_net_income_difference_percentage(self, obj):
        """Calculate the percentage difference between planned and current net incomes."""
        planned_net_income = obj.planned_calculate_net_income()
        if planned_net_income == 0:
            return 0  # Avoid division by zero
        return ((planned_net_income - obj.calculate_net_income()) / planned_net_income) * 100


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "code", "description"]
        read_only_fields = ["id", "code"]  # `name` is editable only during creation

    def validate_name(self, value):
        """Validate that the category name is unique for the user, but only during creation."""
        if self.instance is None:  # `self.instance` is None when creating a new category
            user = self.context["request"].user
            if Category.objects.filter(user=user, name__iexact=value).exists():
                raise serializers.ValidationError(f"A category with the name '{value}' already exists.")
        return value


class FinancialRecordSerializer(serializers.ModelSerializer):
    cycle = serializers.PrimaryKeyRelatedField(queryset=Cycle.objects.all())
    period = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all())
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    diff_planned_actual = serializers.SerializerMethodField()  # Explicit calculation

    class Meta:
        model = FinancialRecord
        fields = [
            "id",
            "period",
            "cycle",
            "category",  # Provides the category ID
            "category_name",  # Provides the category name
            "category_code",
            "current_amount",
            "planned_amount",
            "type_choice",
            "created_at",
            "updated_at",
            "diff_planned_actual",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_diff_planned_actual(self, obj):
        """Calculate the difference between planned and actual amounts."""
        return obj.planned_amount - obj.current_amount


class PeriodSummarySerializer(serializers.Serializer):
    period = serializers.CharField()
    total_incomes = serializers.DecimalField(max_digits=13, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=13, decimal_places=2)
    net_income = serializers.DecimalField(max_digits=13, decimal_places=2)
    planned_total_incomes = serializers.DecimalField(max_digits=13, decimal_places=2)
    planned_total_expenses = serializers.DecimalField(max_digits=13, decimal_places=2)
    planned_net_income = serializers.DecimalField(max_digits=13, decimal_places=2)


class CopyFinancialRecordsSerializer(serializers.Serializer):
    current_cycle_id = serializers.PrimaryKeyRelatedField(queryset=Cycle.objects.all())
    previous_cycle_id = serializers.PrimaryKeyRelatedField(queryset=Cycle.objects.all())

    def validate(self, data):
        """Validate that the cycles exist and belong to the same period."""
        if data['current_cycle_id'] == data['previous_cycle_id']:
            raise serializers.ValidationError("Current and previous cycles cannot be the same.")

        if data['current_cycle_id'].period != data['previous_cycle_id'].period:
            raise serializers.ValidationError("Both cycles must belong to the same period.")

        return data