from django.core.management.base import BaseCommand
from app.models import Period, Cycle, Category, FinancialRecord, FinancialSummary
from django.db.models import Sum

class Command(BaseCommand):
    help = "Populate the FinancialSummary table with aggregated data."

    def handle(self, *args, **kwargs):
        for period in Period.objects.all():
            for cycle in period.cycles.all():
                for category in period.user.categories.all():
                    # Sum incomes and expenses for this category, cycle, and period
                    total_incomes = FinancialRecord.objects.filter(
                        cycle=cycle, category=category, type_choice="income"
                    ).aggregate(Sum("current_amount"))["current_amount__sum"] or 0

                    total_expenses = FinancialRecord.objects.filter(
                        cycle=cycle, category=category, type_choice="expenses"
                    ).aggregate(Sum("current_amount"))["current_amount__sum"] or 0

                    net_income = total_incomes - total_expenses

                    # Update or create the summary record
                    FinancialSummary.objects.update_or_create(
                        period=period,
                        cycle=cycle,
                        category=category,
                        defaults={
                            "total_incomes": total_incomes,
                            "total_expenses": total_expenses,
                            "net_income": net_income,
                        },
                    )

                # Handle the "All" category (null category field)
                total_incomes = FinancialRecord.objects.filter(
                    cycle=cycle, type_choice="income"
                ).aggregate(Sum("current_amount"))["current_amount__sum"] or 0

                total_expenses = FinancialRecord.objects.filter(
                    cycle=cycle, type_choice="expenses"
                ).aggregate(Sum("current_amount"))["current_amount__sum"] or 0

                net_income = total_incomes - total_expenses

                FinancialSummary.objects.update_or_create(
                    period=period,
                    cycle=cycle,
                    category=None,  # Null for "All" category
                    defaults={
                        "total_incomes": total_incomes,
                        "total_expenses": total_expenses,
                        "net_income": net_income,
                    },
                )

        self.stdout.write(self.style.SUCCESS("FinancialSummary table populated successfully."))
