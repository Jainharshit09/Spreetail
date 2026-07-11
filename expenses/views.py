import os
from datetime import datetime, date
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from decimal import Decimal

from .models import Group, Membership, Currency, Expense, ExpenseSplit, Settlement, ImportLog
from .serializers import (
    GroupSerializer, MembershipSerializer, CurrencySerializer, 
    ExpenseSerializer, SettlementSerializer, ImportLogSerializer, UserSerializer
)
from .import_engine import parse_import_file, get_membership_ranges
from .balance_calculator import calculate_group_balances, get_user_detailed_breakdown

# Auth Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    
    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
    user = User.objects.create_user(username=username, password=password, email=email)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'user': UserSerializer(user).data,
        'token': token.key
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)
        
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'user': UserSerializer(user).data,
        'token': token.key
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    return Response(UserSerializer(request.user).data)


# Group Views
class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_serializer = GroupSerializer
    
    def get_serializer_class(self):
        return GroupSerializer

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        group = self.get_object()
        memberships = group.memberships.all()
        return Response(MembershipSerializer(memberships, many=True).data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        group = self.get_object()
        username = request.data.get('username')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        if not username or not start_date:
            return Response({'error': 'Username and start_date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user, _ = User.objects.get_or_create(username=username)
        
        # Check if already a member
        membership, created = Membership.objects.get_or_create(
            user=user, 
            group=group,
            defaults={'start_date': start_date, 'end_date': end_date}
        )
        if not created:
            membership.start_date = start_date
            membership.end_date = end_date
            membership.save()

        return Response(MembershipSerializer(membership).data)

    @action(detail=True, methods=['get'])
    def balances(self, request, pk=None):
        group = self.get_object()
        balances_data = calculate_group_balances(group)
        return Response(balances_data)

    @action(detail=True, methods=['get'])
    def breakdown(self, request, pk=None):
        group = self.get_object()
        username = request.query_params.get('username')
        if not username:
            return Response({'error': 'username query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        breakdown_data = get_user_detailed_breakdown(group, user)
        return Response(breakdown_data)


# Expense Views
class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        group_id = self.request.query_params.get('group')
        if group_id:
            return self.queryset.filter(group_id=group_id)
        return self.queryset


# Settlement Views
class SettlementViewSet(viewsets.ModelViewSet):
    queryset = Settlement.objects.all()
    serializer_class = SettlementSerializer

    def get_queryset(self):
        group_id = self.request.query_params.get('group')
        if group_id:
            return self.queryset.filter(group_id=group_id)
        return self.queryset


# Import Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_preview(request):
    if 'file' not in request.FILES:
        return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
        
    uploaded_file = request.FILES['file']
    filename = uploaded_file.name
    
    # Create temp directory if not exists
    temp_dir = os.path.join(settings.BASE_DIR, 'tmp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, filename)
    
    with open(temp_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
            
    try:
        parsed_items, anomalies, summary = parse_import_file(temp_path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return Response({'error': f'Failed to parse file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
    # Remove temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    # Serialize items so they are JSON safe
    for item in parsed_items:
        # Convert date to string
        item['date'] = item['date'].strftime('%Y-%m-%d')
        if item['type'] == 'expense':
            item['amount'] = str(item['amount'])
            item['amount_in_base'] = str(item['amount_in_base'])
            for split in item['splits']:
                split['amount'] = str(split['amount'])
                split['amount_in_base'] = str(split['amount_in_base'])
                if split['share_value'] is not None:
                    split['share_value'] = str(split['share_value'])
        elif item['type'] == 'settlement':
            item['amount'] = str(item['amount'])
            
    # Save a pending ImportLog
    report = {
        'parsed_items': parsed_items,
        'anomalies': anomalies,
        'summary': summary
    }
    import_log = ImportLog.objects.create(
        filename=filename,
        status='pending',
        report=report
    )
    
    return Response({
        'import_log_id': import_log.id,
        'summary': summary,
        'anomalies': anomalies,
        'parsed_items_count': len(parsed_items)
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_confirm(request):
    import_log_id = request.data.get('import_log_id')
    group_name = request.data.get('group_name')
    
    if not import_log_id or not group_name:
        return Response({'error': 'import_log_id and group_name are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
    import_log = ImportLog.objects.filter(id=import_log_id, status='pending').first()
    if not import_log:
        return Response({'error': 'Pending import log not found.'}, status=status.HTTP_404_NOT_FOUND)
        
    report = import_log.report
    parsed_items = report.get('parsed_items', [])
    
    # Run the ingestion inside a database transaction
    try:
        with transaction.atomic():
            # 1. Create or get group
            group, _ = Group.objects.get_or_create(
                name=group_name,
                defaults={'description': f'Imported from {import_log.filename}'}
            )
            
            # 2. Setup Currencies
            inr, _ = Currency.objects.get_or_create(code='INR', name='Indian Rupee', defaults={'exchange_rate': Decimal('1.0000')})
            usd, _ = Currency.objects.get_or_create(code='USD', name='US Dollar', defaults={'exchange_rate': Decimal('83.0000')})
            
            # 3. Create Users and Memberships
            # Find all unique usernames in import data
            all_users = set()
            for item in parsed_items:
                if item.get('payer'): # settlement
                    all_users.add(item['payer'])
                    all_users.add(item['payee'])
                else: # expense
                    all_users.add(item['paid_by'])
                    for split in item['splits']:
                        all_users.add(split['user'])
                        
            # Get hardcoded membership dates
            ranges = get_membership_ranges()
            
            for username in all_users:
                # Create user in Django
                user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={'email': f'{username.lower()}@example.com'}
                )
                if not user.password:
                    user.set_password('default123')
                    user.save()
                    
                # Add membership
                start_date, end_date = ranges.get(username, (date(2026, 2, 1), None))
                Membership.objects.get_or_create(
                    user=user,
                    group=group,
                    defaults={'start_date': start_date, 'end_date': end_date}
                )
                
            # 4. Import Expenses and Settlements
            for item in parsed_items:
                item_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
                
                if item['type'] == 'expense':
                    paid_by = User.objects.get(username=item['paid_by'])
                    curr = usd if item['currency'] == 'USD' else inr
                    
                    expense = Expense.objects.create(
                        group=group,
                        date=item_date,
                        description=item['description'],
                        paid_by=paid_by,
                        amount=Decimal(item['amount']),
                        currency=curr,
                        split_type=item['split_type'],
                        notes=item['notes']
                    )
                    
                    for split_data in item['splits']:
                        split_user = User.objects.get(username=split_data['user'])
                        ExpenseSplit.objects.create(
                            expenditure=expense,
                            user=split_user,
                            share_value=Decimal(split_data['share_value']) if split_data['share_value'] is not None else None,
                            amount=Decimal(split_data['amount']),
                            amount_in_base=Decimal(split_data['amount_in_base'])
                        )
                        
                elif item['type'] == 'settlement':
                    payer = User.objects.get(username=item['payer'])
                    payee = User.objects.get(username=item['payee'])
                    curr = usd if item['currency'] == 'USD' else inr
                    
                    Settlement.objects.create(
                        group=group,
                        payer=payer,
                        payee=payee,
                        amount=Decimal(item['amount']),
                        currency=curr,
                        date=item_date,
                        notes=item['notes']
                    )
            
            # Update import log status
            import_log.status = 'applied'
            import_log.save()
            
    except Exception as e:
        return Response({'error': f'Transaction failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    return Response({
        'status': 'success',
        'group_id': group.id,
        'group_name': group.name,
        'message': f'Successfully imported {len(parsed_items)} items into group {group.name}'
    })
