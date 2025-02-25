

from django.contrib import admin
from django.urls import path, include  # Make sure to import `include`

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include the URLs from the finance app
    path('finance/', include('finance.urls')),  # Include finance URLs here
]

