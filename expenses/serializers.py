from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Group, Membership, Currency, Expense, ExpenseSplit, Settlement, ImportLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']

class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Membership
        fields = ['id', 'user', 'start_date', 'end_date']

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'exchange_rate', 'last_updated']

class ExpenseSplitSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = ExpenseSplit
        fields = ['id', 'user', 'username', 'share_value', 'amount', 'amount_in_base']

class ExpenseSerializer(serializers.ModelSerializer):
    splits = ExpenseSplitSerializer(many=True, required=False)
    paid_by = UserSerializer(read_only=True)
    payer_username = serializers.CharField(write_only=True, required=False)
    currency_code = serializers.CharField(write_only=True, required=False)
    currency = CurrencySerializer(read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'date', 'description', 'paid_by', 'payer_username', 
            'group', 'currency', 'currency_code', 'amount', 'split_type', 
            'notes', 'splits'
        ]

    def create(self, validated_data):
        splits_data = validated_data.pop('splits', [])
        payer_username = validated_data.pop('payer_username', None)
        currency_code = validated_data.pop('currency_code', 'INR')

        if payer_username:
            user, _ = User.objects.get_or_create(username=payer_username)
            validated_data['paid_by'] = user
        
        currency = Currency.objects.filter(code=currency_code).first()
        if not currency:
            currency = Currency.objects.create(code=currency_code, name=currency_code)
        validated_data['currency'] = currency

        expense = Expense.objects.create(**validated_data)

        for split_data in splits_data:
            username = split_data.pop('username', None)
            if username:
                u, _ = User.objects.get_or_create(username=username)
                split_data['user'] = u
            ExpenseSplit.objects.create(expenditure=expense, **split_data)

        return expense

class SettlementSerializer(serializers.ModelSerializer):
    payer = UserSerializer(read_only=True)
    payee = UserSerializer(read_only=True)
    payer_username = serializers.CharField(write_only=True, required=False)
    payee_username = serializers.CharField(write_only=True, required=False)
    currency_code = serializers.CharField(write_only=True, required=False)
    currency = CurrencySerializer(read_only=True)

    class Meta:
        model = Settlement
        fields = [
            'id', 'group', 'payer', 'payee', 'payer_username', 
            'payee_username', 'amount', 'currency', 'currency_code', 
            'date', 'status', 'notes'
        ]

    def create(self, validated_data):
        payer_username = validated_data.pop('payer_username', None)
        payee_username = validated_data.pop('payee_username', None)
        currency_code = validated_data.pop('currency_code', 'INR')

        if payer_username:
            payer, _ = User.objects.get_or_create(username=payer_username)
            validated_data['payer'] = payer

        if payee_username:
            payee, _ = User.objects.get_or_create(username=payee_username)
            validated_data['payee'] = payee

        currency = Currency.objects.filter(code=currency_code).first()
        if not currency:
            currency = Currency.objects.create(code=currency_code, name=currency_code)
        validated_data['currency'] = currency

        return Settlement.objects.create(**validated_data)

class ImportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportLog
        fields = ['id', 'imported_at', 'filename', 'status', 'report']
