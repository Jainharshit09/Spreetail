from django.contrib.auth.models import User
from django.db import models

class Group(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'group')

    def __str__(self):
        return f'{self.user.username} in {self.group.name} ({self.start_date} to {self.end_date or "Present"})'

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000) # Base is INR (1.0000)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.code} ({self.name})'

class Expense(models.Model):
    SPLIT_CHOICES = [
        ('equal', 'Equal'),
        ('percentage', 'Percentage'),
        ('share', 'Custom Shares'),
        ('unequal', 'Unequal'),
    ]

    date = models.DateField()
    description = models.TextField()
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expenses_paid')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='expenses')
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    split_type = models.CharField(max_length=20, choices=SPLIT_CHOICES)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'{self.date} - {self.description} ({self.amount} {self.currency.code if self.currency else ""})'

class ExpenseSplit(models.Model):
    expenditure = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='splits')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expense_splits')
    share_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True) # Percentage or Share count
    amount = models.DecimalField(max_digits=12, decimal_places=2) # in expense's currency
    amount_in_base = models.DecimalField(max_digits=12, decimal_places=2) # in base currency (INR)

    class Meta:
        unique_together = ('expenditure', 'user')

    def __str__(self):
        return f'{self.expenditure.description} - {self.user.username}: {self.amount}'

class Settlement(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='settlements', null=True, blank=True)
    payer = models.ForeignKey(User, related_name='sent_settlements', on_delete=models.CASCADE)
    payee = models.ForeignKey(User, related_name='received_settlements', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'{self.payer.username} to {self.payee.username} - {self.amount} {self.currency.code if self.currency else ""}'

class ImportLog(models.Model):
    imported_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='pending') # pending, applied
    report = models.JSONField(default=dict)

    def __str__(self):
        return f'Import {self.filename} at {self.imported_at}'
