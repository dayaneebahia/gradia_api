
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from finance import views
from finance.views import PeriodSummaryView, VerifyTokenView, ReportDataView, CopyFinancialRecordsView
# Set up the router for viewsets
router = DefaultRouter()
router.register('cycles', views.CycleViewSet)
router.register('categories', views.CategoryViewSet)
router.register('periods', views.PeriodViewSet)
router.register('users', views.UserViewSet)
router.register('financial_records', views.FinancialRecordViewSet, basename='financial_records')
# Define URL patterns
urlpatterns = [
    path('', include(router.urls)),  # Include routes registered in the router
    path('periods/<uuid:period_id>/summary/', PeriodSummaryView.as_view(), name='period-summary'),
    path('verify-token/', VerifyTokenView.as_view(), name='verify-token'),
    path('report-data/', ReportDataView.as_view(), name='report_data'),
    path('app/copy/', CopyFinancialRecordsView.as_view(), name='copy-financial-records'),
   
]