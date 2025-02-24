from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed, APIException, NotFound
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import get_authorization_header
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch
from django.db import IntegrityError
from firebase_admin import auth as firebase_auth
from .authentication import FirebaseAuthentication
from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from .models import Cycle, Period, FinancialRecord, Category
from django.db.models import Sum, Q
import matplotlib.pyplot as plt
from io import BytesIO
from django.http import HttpResponse
from .models import Period
from .serializers import (
    CycleSerializer,
    PeriodSerializer,
    UserSerializer,
    FinancialRecordSerializer,
    CategorySerializer,
    VerifyTokenSerializer,
    PeriodSummarySerializer, 
    CopyFinancialRecordsSerializer,

    
)
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import permissions
from decimal import Decimal
from rest_framework.decorators import action
from django.db import transaction




# Firebase Token Verification

class VerifyTokenView(GenericAPIView):
    serializer_class = VerifyTokenSerializer

    def post(self, request, *args, **kwargs):
        auth_header = get_authorization_header(request).split()
        if not auth_header or auth_header[0].lower() != b'bearer':
            return Response(
                {"detail": "Authorization header is missing or malformed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        id_token = auth_header[1].decode()

        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            return Response({"uid": uid, "message": "Token is valid."}, status=status.HTTP_200_OK)
        except Exception as e:
            raise AuthenticationFailed(f"Token verification failed: {str(e)}")

# User Management
class UserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Manage user registration in the database.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                },
                "message": "User created successfully. Use Firebase token for authentication.",
            },
            status=status.HTTP_201_CREATED,
        )

   
    def list(self, request, *args, **kwargs):
        return Response({"detail": "Listing all users is not allowed."}, status=status.HTTP_403_FORBIDDEN)


def health_check(request):
    return JsonResponse({"status": "ok"}, status=200)
# Cycle Management

class CycleViewSet(viewsets.ModelViewSet):
    """
    Manage cycles in the database.
    """
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CycleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['period']
    queryset = Cycle.objects.all()  # Explicitly define the queryset

    def get_queryset(self):
        """
        Override to filter cycles for the authenticated user.
        """
        if not self.request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to view this resource.")
        return Cycle.objects.filter(period__user=self.request.user)

    @action(detail=True, methods=['get'])
    def last_5_cycles(self, request, pk=None):
        """Get the last 5 cycles for the selected cycle."""
        cycle = self.get_object()
        serializer = self.get_serializer(cycle)
        return Response(serializer.data.get('last_5_cycles'))

# Category Management
class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    Manage categories in the database.
    """
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to view this resource.")
        return self.queryset.filter(user=self.request.user).order_by("-name")

    def perform_create(self, serializer):
        user = self.request.user

        # Generate and save category, retrying on duplicates
        for attempt in range(5):
            try:
                serializer.save(user=user)
                return
            except IntegrityError as e:
                if "duplicate key value violates unique constraint" in str(e) and attempt < 4:
                    continue
                raise APIException("Failed to create category due to a conflict. Please retry.")


    def perform_destroy(self, instance):
        if instance.code == "DEFAULT":
            raise APIException("Cannot delete the DEFAULT category.")

        # Ensure the default category exists for the user
        default_category, created = Category.objects.get_or_create(
            user=instance.user,
            code="DEFAULT",
            defaults={
                "name": "Default",
                "description": "Default category for reassigned financial records.",
            },
        )

        # Reassign financial records linked to the category being deleted
        instance.financial_records.update(category=default_category)

        # Proceed to delete the category
        instance.delete()


# Period Management
class PeriodViewSet(viewsets.ModelViewSet):
    """
    Manage periods in the database.
    """
    queryset = Period.objects.all()
    serializer_class = PeriodSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_archived']

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        categories = self.request.query_params.getlist('category')
        periods = self.request.query_params.getlist('period')

        if categories:
            # Filter by categories in related financial records
            queryset = queryset.filter(cycles__financial_records__category__id__in=categories).distinct()
        if periods:
            # Filter by specific periods
            queryset = queryset.filter(id__in=periods)

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Override the create method to handle cycle creation.
        """
        user = request.user
        title = request.data.get('title')  # e.g., 2024

        if not title:
            return Response({"error": "Year (title) is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the period already exists
        if Period.objects.filter(user=user, title=title).exists():
            return Response({"error": "Period for this year already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the new period
        period = Period.objects.create(user=user, title=title)
        period.create_cycles()  # Automatically create the 12 monthly cycles

        serializer = self.get_serializer(period)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
class FinancialRecordViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Override to filter records by cycle, period, and optionally by category.
        """
        queryset = FinancialRecord.objects.filter(category__user=self.request.user)
        cycle_id = self.request.query_params.get("cycle")
        period_id = self.request.query_params.get("period")
        category_id = self.request.query_params.get("category")

        if cycle_id:
            queryset = queryset.filter(cycle_id=cycle_id)
        if period_id:
            queryset = queryset.filter(cycle__period_id=period_id)  # Filtering via related Cycle's Period
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    def perform_create(self, serializer):
        category = serializer.validated_data.get("category")
        cycle = serializer.validated_data.get("cycle")

        # Ensure the category belongs to the authenticated user
        if category.user != self.request.user:
            raise PermissionDenied("You cannot create a record with a category that does not belong to you.")

        # Validate cycle and period consistency
        if cycle.period.user != self.request.user:
            raise PermissionDenied("The selected cycle's period does not belong to you.")

        # Save the financial record
        file = self.request.FILES.get('file')
        financial_record = serializer.save()

        # Save the uploaded file if provided
        if file:
            FileUpload.objects.create(
                file=file,
                financial_record=financial_record
            )
    @action(detail=False, methods=["post"], url_path="copy-previous-month")
    def copy_previous_month(self, request):
        user = request.user
        current_cycle_id = request.data.get("current_cycle_id")
        previous_cycle_id = request.data.get("previous_cycle_id")

        if not current_cycle_id or not previous_cycle_id:
            return Response({"detail": "Current and previous cycle IDs are required."}, status=400)

        try:
            with transaction.atomic():
                previous_records = FinancialRecord.objects.filter(
                    cycle_id=previous_cycle_id, cycle__user=user
                )
                new_records = []
                for record in previous_records:
                    new_records.append(FinancialRecord(
                        cycle_id=current_cycle_id,
                        category=record.category,
                        period=record.period,
                        type_choice=record.type_choice,
                        current_amount=record.current_amount,
                        planned_amount=record.planned_amount,
                        firebase_uid=request.data.get("firebase_uid")  # Add if needed
                    ))
                FinancialRecord.objects.bulk_create(new_records)
                return Response({"detail": "Records copied successfully."})
        except Exception as e:
            return Response({"detail": str(e)}, status=500)

class PeriodSummaryView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            period_id = kwargs.get('period_id')
            period = Period.objects.get(id=period_id)

            # Perform calculations
            total_incomes = Decimal(period.calculate_total_incomes() or 0)
            total_expenses = Decimal(period.calculate_total_expenses() or 0)
            net_income = total_incomes - total_expenses

            planned_total_incomes = Decimal(period.planned_calculate_total_incomes() or 0)
            planned_total_expenses = Decimal(period.planned_calculate_total_expenses() or 0)
            planned_net_income = planned_total_incomes - planned_total_expenses

            # Prepare data
            data = {
                "period": period.title,
                "total_incomes": total_incomes,
                "total_expenses": total_expenses,
                "net_income": net_income,
                "planned_total_incomes": planned_total_incomes,
                "planned_total_expenses": planned_total_expenses,
                "planned_net_income": planned_net_income,
            }

            serializer = PeriodSummarySerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Period.DoesNotExist:
            return Response({"error": "Period not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error fetching period summary: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


import matplotlib.pyplot as plt
from io import BytesIO
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from .models import Period, Cycle, Category
from django.utils import timezone
from rest_framework.exceptions import ValidationError


class ReportDataView(APIView):
    """
    Provides aggregated report data for the authenticated user.
    """
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get(self, request, *args, **kwargs):
        user = request.user

        # Aggregate period data
        periods = Period.objects.filter(user=user)
        period_data = []
        for period in periods:
            period_data.append({
                "title": period.title,
                "total_incomes": period.calculate_total_incomes(),
                "total_expenses": period.calculate_total_expenses(),
                "net_income": period.calculate_net_income(),
                "planned_incomes": period.planned_calculate_total_incomes(),
                "planned_expenses": period.planned_calculate_total_expenses(),
                "planned_net_income": period.planned_calculate_net_income(),
                "expense_difference_value": period.expense_difference_value(),
                "expense_difference_percentage": period.expense_difference_percentage(),
                "income_difference_value": period.income_difference_value(),
                "income_difference_percentage": period.income_difference_percentage(),
                "net_income_difference_value": period.net_income_difference_value(),
                "net_income_difference_percentage": period.net_income_difference_percentage(),
            })

        # Aggregate cycle data
        cycles = Cycle.objects.filter(period__user=user)
        cycle_data = []
        for cycle in cycles:
            # Fetch associated categories for this cycle
            categories = FinancialRecord.objects.filter(cycle=cycle).values(
                'category__name'
            ).annotate(
                total_income=Sum('current_amount', filter=Q(type_choice="income")),
                total_expense=Sum('current_amount', filter=Q(type_choice="expenses"))
            )

            cycle_data.append({
                "id": cycle.id,
                "name": cycle.name,
                "period_title": cycle.period.title,
                "total_incomes": cycle.calculate_total_incomes(),
                "total_expenses": cycle.calculate_total_expenses(),
                "net_income": cycle.calculate_net_income(),
                "planned_incomes": cycle.planned_calculate_total_incomes(),
                "planned_expenses": cycle.planned_calculate_total_expenses(),
                "planned_net_income": cycle.planned_calculate_net_income(),
                "income_difference_value": cycle.income_difference_value(),
                "income_difference_percentage": cycle.income_difference_percentage(),
                "expense_difference_value": cycle.expense_difference_value(),
                "expense_difference_percentage": cycle.expense_difference_percentage(),
                "net_income_difference_value": cycle.net_income_difference_value(),
                "net_income_difference_percentage": cycle.net_income_difference_percentage(),
                "categories": list(categories),  # Include category data
            })

        # Aggregate category data
        category_data = Category.objects.filter(user=user).annotate(
            total_income=Sum("financial_records__current_amount", filter=Q(financial_records__type_choice="income")),
            total_expense=Sum("financial_records__current_amount", filter=Q(financial_records__type_choice="expenses"))
        ).values("name", "code", "total_income", "total_expense")

        return Response({
            "period_data": period_data,
            "cycle_data": cycle_data,
            "category_data": list(category_data),
        })

class CopyFinancialRecordsView(APIView):
    """API endpoint to copy financial records from one cycle to another."""
    
    def post(self, request, *args, **kwargs):
        serializer = CopyFinancialRecordsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_cycle = serializer.validated_data['current_cycle_id']
        previous_cycle = serializer.validated_data['previous_cycle_id']

        # Fetch financial records from the previous cycle
        previous_records = FinancialRecord.objects.filter(cycle=previous_cycle)
        if not previous_records.exists():
            return Response({"detail": "No financial records found in the previous cycle."}, status=status.HTTP_404_NOT_FOUND)

        # Create copies of financial records for the current cycle
        new_records = []
        for record in previous_records:
            new_record = FinancialRecord(
                cycle=current_cycle,
                period=record.period,
                category=record.category,
                type_choice=record.type_choice,
                planned_amount=record.planned_amount,
                current_amount=0,  # Reset the current amount for the new cycle
            )
            new_records.append(new_record)

        # Bulk create the new financial records in an atomic transaction
        with transaction.atomic():
            FinancialRecord.objects.bulk_create(new_records)

        # Serialize the new records to return as response
        new_records_serialized = FinancialRecordSerializer(new_records, many=True)
        return Response(new_records_serialized.data, status=status.HTTP_201_CREATED)