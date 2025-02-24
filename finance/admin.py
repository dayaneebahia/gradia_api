from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.db import models  # Import models to use Q and Sum
from django.utils.html import format_html  # For better display formatting
from .models import Period, Cycle, FinancialRecord, Category
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum, Q


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "description")
    search_fields = ("name", "code")


@admin.register(Cycle)
class CycleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "month",
        "period",
    )
    search_fields = ("name", "period__title")
    list_filter = ("period",)


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = (
        "type_choice",
        "category",
        "cycle",
        "created_at",
    )
    list_filter = ("type_choice", "cycle", "category")
    search_fields = ("category__name", "cycle__name")
    autocomplete_fields = ("category", "cycle")


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "is_archived",
        "total_incomes",
        "total_expenses",
        "net_income",
        "planned_total_incomes",
        "planned_total_expenses",
        "planned_net_income",
        "created_at",
    )
    readonly_fields = (
        "total_incomes",
        "total_expenses",
        "net_income",
        "planned_total_incomes",
        "planned_total_expenses",
        "planned_net_income",
    )
    search_fields = ("title", "user__username")
    list_filter = ("is_archived", "created_at")

    def total_incomes(self, obj):
        """Calculate total incomes for the period."""
        total_income = (
            obj.cycles.aggregate(total=Sum("financial_records__current_amount", filter=Q(financial_records__type_choice="income")))
            .get("total")
            or 0
        )
        return f"${total_income:.2f}"

    def total_expenses(self, obj):
        """Calculate total expenses for the period."""
        total_expenses = (
            obj.cycles.aggregate(total=Sum("financial_records__current_amount", filter=Q(financial_records__type_choice="expenses")))
            .get("total")
            or 0
        )
        return f"${total_expenses:.2f}"

    def net_income(self, obj):
        """Calculate net income for the period."""
        total_income = (
            obj.cycles.aggregate(total=Sum("financial_records__current_amount", filter=Q(financial_records__type_choice="income")))
            .get("total")
            or 0
        )
        total_expenses = (
            obj.cycles.aggregate(total=Sum("financial_records__current_amount", filter=Q(financial_records__type_choice="expenses")))
            .get("total")
            or 0
        )
        return f"${total_income - total_expenses:.2f}"

    def planned_total_incomes(self, obj):
        """Calculate planned incomes for the period."""
        planned_total_income = (
            obj.cycles.aggregate(total=Sum("financial_records__planned_amount", filter=Q(financial_records__type_choice="income")))
            .get("total")
            or 0
        )
        return f"${planned_total_income:.2f}"

    def planned_total_expenses(self, obj):
        """Calculate planned expenses for the period."""
        planned_total_expenses = (
            obj.cycles.aggregate(total=Sum("financial_records__planned_amount", filter=Q(financial_records__type_choice="expenses")))
            .get("total")
            or 0
        )
        return f"${planned_total_expenses:.2f}"

    def planned_net_income(self, obj):
        """Calculate planned net income for the period."""
        planned_total_income = (
            obj.cycles.aggregate(total=Sum("financial_records__planned_amount", filter=Q(financial_records__type_choice="income")))
            .get("total")
            or 0
        )
        planned_total_expenses = (
            obj.cycles.aggregate(total=Sum("financial_records__planned_amount", filter=Q(financial_records__type_choice="expenses")))
            .get("total")
            or 0
        )
        return f"${planned_total_income - planned_total_expenses:.2f}"

    total_incomes.short_description = "Total Incomes"
    total_expenses.short_description = "Total Expenses"
    net_income.short_description = "Net Income"
    planned_total_incomes.short_description = "Planned Total Incomes"
    planned_total_expenses.short_description = "Planned Total Expenses"
    planned_net_income.short_description = "Planned Net Income"

    # Adding the custom filters view
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('filters/', self.admin_site.admin_view(self.filter_view), name='filter_view'),
        ]
        return custom_urls + urls

    def filter_view(self, request):
        # Extract query parameters
        category_id = request.GET.get('category_id')
        period_ids = request.GET.getlist('period_ids')
        cycle_id = request.GET.get('cycle_id')

        # Base queryset
        records_queryset = FinancialRecord.objects.all()

        # Apply filters
        if category_id:
            records_queryset = records_queryset.filter(category_id=category_id)
        if period_ids:
            records_queryset = records_queryset.filter(period_id__in=period_ids)
        if cycle_id:
            records_queryset = records_queryset.filter(cycle_id=cycle_id)

        # Aggregations
        total_incomes = records_queryset.filter(type_choice="income").aggregate(Sum('current_amount'))['current_amount__sum'] or 0
        total_expenses = records_queryset.filter(type_choice="expenses").aggregate(Sum('current_amount'))['current_amount__sum'] or 0
        planned_incomes = records_queryset.filter(type_choice="income").aggregate(Sum('planned_amount'))['planned_amount__sum'] or 0
        planned_expenses = records_queryset.filter(type_choice="expenses").aggregate(Sum('planned_amount'))['planned_amount__sum'] or 0

        # Context for the template
        context = {
            'title': 'Filters',
            'total_incomes': total_incomes,
            'total_expenses': total_expenses,
            'net_income': total_incomes - total_expenses,
            'planned_incomes': planned_incomes,
            'planned_expenses': planned_expenses,
            'planned_net_income': planned_incomes - planned_expenses,
            'records': records_queryset,
        }
        return render(request, 'admin/filters.html', context)
