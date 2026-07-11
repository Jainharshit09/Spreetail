from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GroupViewSet, ExpenseViewSet, SettlementViewSet,
    register_user, login_user, current_user,
    import_preview, import_confirm
)

router = DefaultRouter()
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'settlements', SettlementViewSet, basename='settlement')

urlpatterns = [
    # Auth endpoints
    path('auth/register/', register_user, name='auth_register'),
    path('auth/login/', login_user, name='auth_login'),
    path('auth/me/', current_user, name='auth_me'),
    
    # Import endpoints
    path('import/preview/', import_preview, name='import_preview'),
    path('import/confirm/', import_confirm, name='import_confirm'),
    
    # Rest Framework Router
    path('', include(router.urls)),
]
