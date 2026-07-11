from decimal import Decimal
from collections import defaultdict
from .models import User, Expense, ExpenseSplit, Settlement

def calculate_group_balances(group):
    """
    Computes:
    1. Net balance for each active user in the group.
    2. Simplified settlement paths (Who pays whom, how much).
    3. Individual totals (Paid, Share, Settled).
    """
    # Fetch all members of the group
    memberships = group.memberships.select_related('user')
    users = [m.user for m in memberships]
    usernames = [u.username for u in users]
    
    # Initialize structures
    user_totals = {
        username: {
            'username': username,
            'user_id': user.id,
            'paid_amount': Decimal('0.00'),
            'share_amount': Decimal('0.00'),
            'settlements_sent': Decimal('0.00'),
            'settlements_received': Decimal('0.00'),
            'net_balance': Decimal('0.00')
        }
        for username, user in zip(usernames, users)
    }

    # 1. Process Expenses
    expenses = Expense.objects.filter(group=group).select_related('paid_by', 'currency')
    for expense in expenses:
        if not expense.paid_by:
            continue
        payer_name = expense.paid_by.username
        
        # Base currency amount paid
        # If currency is USD, we convert to base (INR) using exchange_rate of the currency
        rate = expense.currency.exchange_rate if expense.currency else Decimal('1.0000')
        paid_in_base = (expense.amount * rate).quantize(Decimal('0.01'))
        
        if payer_name in user_totals:
            user_totals[payer_name]['paid_amount'] += paid_in_base

        # Process splits
        splits = expense.splits.select_related('user')
        for split in splits:
            if not split.user:
                continue
            split_user = split.user.username
            if split_user in user_totals:
                user_totals[split_user]['share_amount'] += split.amount_in_base

    # 2. Process Settlements
    settlements = Settlement.objects.filter(group=group).select_related('payer', 'payee', 'currency')
    for sett in settlements:
        payer_name = sett.payer.username
        payee_name = sett.payee.username
        
        rate = sett.currency.exchange_rate if sett.currency else Decimal('1.0000')
        sett_in_base = (sett.amount * rate).quantize(Decimal('0.01'))
        
        if payer_name in user_totals:
            user_totals[payer_name]['settlements_sent'] += sett_in_base
        if payee_name in user_totals:
            user_totals[payee_name]['settlements_received'] += sett_in_base

    # 3. Calculate Net Balance
    # Net Balance = Paid - Share + Sent - Received
    for u in user_totals.values():
        u['net_balance'] = u['paid_amount'] - u['share_amount'] + u['settlements_sent'] - u['settlements_received']

    # 4. Simplify Debts (Greedy Min-Max Matching)
    # We want to match debtors (net_balance < 0) with creditors (net_balance > 0)
    debtors = []
    creditors = []
    
    for username, totals in user_totals.items():
        bal = totals['net_balance']
        if bal < Decimal('-0.005'):
            debtors.append([username, bal])
        elif bal > Decimal('0.005'):
            creditors.append([username, bal])
            
    simplified_debts = []
    
    # Run the simplification
    while debtors and creditors:
        # Sort so we always settle the largest amounts
        debtors.sort(key=lambda x: x[1]) # most negative first
        creditors.sort(key=lambda x: x[1], reverse=True) # most positive first
        
        debtor_name, debt_bal = debtors[0]
        creditor_name, cred_bal = creditors[0]
        
        amount_to_settle = min(-debt_bal, cred_bal).quantize(Decimal('0.01'))
        
        simplified_debts.append({
            'from_user': debtor_name,
            'to_user': creditor_name,
            'amount': amount_to_settle
        })
        
        # Update balances
        debtors[0][1] += amount_to_settle
        creditors[0][1] -= amount_to_settle
        
        # Remove if settled
        if abs(debtors[0][1]) < Decimal('0.005'):
            debtors.pop(0)
        if abs(creditors[0][1]) < Decimal('0.005'):
            creditors.pop(0)

    return {
        'users_summary': list(user_totals.values()),
        'simplified_debts': simplified_debts
    }

def get_user_detailed_breakdown(group, user):
    """
    Rohan's Request: Returns a list of contributions/splits explaining the balance.
    Shows exactly which transactions lead to the final net balance.
    """
    breakdown = []
    
    # 1. Fetch Expenses involving this user (either paid by them or split with them)
    expenses = Expense.objects.filter(group=group).select_related('paid_by', 'currency').order_by('date')
    
    for expense in expenses:
        rate = expense.currency.exchange_rate if expense.currency else Decimal('1.0000')
        
        is_payer = (expense.paid_by == user)
        
        # Find user's split if any
        user_split = expense.splits.filter(user=user).first()
        is_in_split = (user_split is not None)
        
        if not is_payer and not is_in_split:
            continue
            
        paid_amount = expense.amount if is_payer else Decimal('0.00')
        paid_amount_in_base = (paid_amount * rate).quantize(Decimal('0.01'))
        
        share_amount = user_split.amount if is_in_split else Decimal('0.00')
        share_amount_in_base = user_split.amount_in_base if is_in_split else Decimal('0.00')
        
        net_effect = paid_amount_in_base - share_amount_in_base
        
        breakdown.append({
            'type': 'expense',
            'id': expense.id,
            'date': expense.date,
            'description': expense.description,
            'original_amount': expense.amount,
            'currency': expense.currency.code if expense.currency else 'INR',
            'exchange_rate': rate,
            'paid_by': expense.paid_by.username if expense.paid_by else 'Unknown',
            'user_paid': paid_amount,
            'user_paid_in_base': paid_amount_in_base,
            'user_share': share_amount,
            'user_share_in_base': share_amount_in_base,
            'net_effect': net_effect
        })

    # 2. Fetch Settlements involving this user
    settlements = Settlement.objects.filter(group=group).filter(
        payer=user
    ) | Settlement.objects.filter(group=group).filter(
        payee=user
    )
    settlements = settlements.select_related('payer', 'payee', 'currency').order_by('date')
    
    for sett in settlements:
        rate = sett.currency.exchange_rate if sett.currency else Decimal('1.0000')
        
        is_sent = (sett.payer == user)
        amount_in_base = (sett.amount * rate).quantize(Decimal('0.01'))
        
        # If we sent, it increases our net balance (we paid off debt) -> positive effect
        # If we received, it decreases our net balance (we got paid) -> negative effect
        net_effect = amount_in_base if is_sent else -amount_in_base
        
        breakdown.append({
            'type': 'settlement',
            'id': sett.id,
            'date': sett.date,
            'description': f"Settlement: {sett.payer.username} paid {sett.payee.username}",
            'original_amount': sett.amount,
            'currency': sett.currency.code if sett.currency else 'INR',
            'exchange_rate': rate,
            'paid_by': sett.payer.username,
            'user_paid': sett.amount if is_sent else Decimal('0.00'),
            'user_paid_in_base': amount_in_base if is_sent else Decimal('0.00'),
            'user_share': sett.amount if not is_sent else Decimal('0.00'),
            'user_share_in_base': amount_in_base if not is_sent else Decimal('0.00'),
            'net_effect': net_effect
        })
        
    # Sort breakdown by date
    breakdown.sort(key=lambda x: x['date'])
    
    # Calculate running balance
    running = Decimal('0.00')
    for item in breakdown:
        running += item['net_effect']
        item['running_balance'] = running

    return breakdown
