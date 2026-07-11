from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date

from .models import Group, Membership, Currency, Expense, ExpenseSplit, Settlement
from .import_engine import process_file_rows, get_membership_ranges
from .balance_calculator import calculate_group_balances, get_user_detailed_breakdown

class ImportEngineTestCase(TestCase):
    def test_spelling_variants_normalization(self):
        # We test how name variants like Priya S, priya, rohan  are handled.
        rows = [
            {
                'date': '2026-02-03',
                'description': 'Groceries BigBasket',
                'paid_by': 'Priya S',
                'amount': '2340',
                'currency': 'INR',
                'split_type': 'equal',
                'split_with': 'Aisha;rohan ;Priya;Meera',
                'split_details': '',
                'notes': ''
            }
        ]
        parsed_items, anomalies, summary = process_file_rows(rows)
        
        self.assertEqual(len(parsed_items), 1)
        self.assertEqual(parsed_items[0]['paid_by'], 'Priya')
        
        # Verify split participants are normalized
        participants = [s['user'] for s in parsed_items[0]['splits']]
        self.assertIn('Priya', participants)
        self.assertIn('Rohan', participants)
        
        # We expect anomalies for spelling variants
        spelling_anoms = [a for a in anomalies if a['type'] == 'spelling_variant']
        self.assertTrue(len(spelling_anoms) >= 1)

    def test_settlement_detection(self):
        # Test detection of settlements logged as expenses
        rows = [
            {
                'date': '2026-02-25',
                'description': 'Rohan paid Aisha back',
                'paid_by': 'Rohan',
                'amount': '5000',
                'currency': 'INR',
                'split_type': '',
                'split_with': 'Aisha',
                'split_details': '',
                'notes': 'this is a settlement'
            }
        ]
        parsed_items, anomalies, summary = process_file_rows(rows)
        self.assertEqual(len(parsed_items), 1)
        self.assertEqual(parsed_items[0]['type'], 'settlement')
        self.assertEqual(parsed_items[0]['payer'], 'Rohan')
        self.assertEqual(parsed_items[0]['payee'], 'Aisha')
        self.assertEqual(parsed_items[0]['amount'], Decimal('5000.00'))

    def test_percentage_sum_error_normalization(self):
        # Test percentage split summing to 110%
        rows = [
            {
                'date': '2026-02-28',
                'description': 'Pizza Friday',
                'paid_by': 'Aisha',
                'amount': '1440',
                'currency': 'INR',
                'split_type': 'percentage',
                'split_with': 'Aisha;Rohan;Priya;Meera',
                'split_details': 'Aisha 30%; Rohan 30%; Priya 30%; Meera 20%',
                'notes': ''
            }
        ]
        parsed_items, anomalies, summary = process_file_rows(rows)
        self.assertEqual(len(parsed_items), 1)
        
        splits = parsed_items[0]['splits']
        total_amount = sum(Decimal(s['amount']) for s in splits)
        self.assertEqual(total_amount, Decimal('1440.00'))
        
        # Aisha's split normalized share value should be (30/110) * 100
        aisha_split = next(s for s in splits if s['user'] == 'Aisha')
        self.assertAlmostEqual(float(aisha_split['share_value']), 30.0 / 110.0 * 100.0, places=2)

    def test_temporal_membership_violation(self):
        # Meera left end of March. Test if she is excluded on April 2.
        rows = [
            {
                'date': '2026-04-02',
                'description': 'Groceries BigBasket',
                'paid_by': 'Priya',
                'amount': '2640',
                'currency': 'INR',
                'split_type': 'equal',
                'split_with': 'Aisha;Rohan;Priya;Meera',
                'split_details': '',
                'notes': 'oops Meera still in list'
            }
        ]
        parsed_items, anomalies, summary = process_file_rows(rows)
        self.assertEqual(len(parsed_items), 1)
        
        splits = parsed_items[0]['splits']
        participants = [s['user'] for s in splits]
        # Meera should be excluded
        self.assertNotIn('Meera', participants)
        self.assertIn('Aisha', participants)
        self.assertIn('Rohan', participants)
        self.assertIn('Priya', participants)
        
        # Verify the sum is still 2640
        self.assertEqual(sum(Decimal(s['amount']) for s in splits), Decimal('2640.00'))
        # Each active participant should pay 2640 / 3 = 880
        for s in splits:
            self.assertEqual(Decimal(s['amount']), Decimal('880.00'))

    def test_out_of_range_date_correction(self):
        # 2014-03-01 Airport cab should be corrected to 2026-03-12
        rows = [
            {
                'date': '2014-03-01',
                'description': 'Airport cab',
                'paid_by': 'Rohan',
                'amount': '1100',
                'currency': 'INR',
                'split_type': 'equal',
                'split_with': 'Aisha;Rohan;Priya;Dev',
                'split_details': '',
                'notes': ''
            }
        ]
        parsed_items, anomalies, summary = process_file_rows(rows)
        self.assertEqual(len(parsed_items), 1)
        self.assertEqual(parsed_items[0]['date'], date(2026, 3, 12))

    def test_invalid_headers_csv_throws_value_error(self):
        import tempfile
        import os
        from .import_engine import read_csv_file
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("wrong_header_1,wrong_header_2\n1,2\n")
            temp_path = f.name
            
        try:
            with self.assertRaises(ValueError):
                read_csv_file(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class BalanceCalculatorTestCase(TestCase):
    def setUp(self):
        # Setup basic users and group
        self.group = Group.objects.create(name="Test Flatmates")
        
        self.aisha = User.objects.create(username="Aisha")
        self.rohan = User.objects.create(username="Rohan")
        self.priya = User.objects.create(username="Priya")
        
        Membership.objects.create(user=self.aisha, group=self.group, start_date=date(2026, 2, 1))
        Membership.objects.create(user=self.rohan, group=self.group, start_date=date(2026, 2, 1))
        Membership.objects.create(user=self.priya, group=self.group, start_date=date(2026, 2, 1))
        
        self.inr = Currency.objects.create(code="INR", name="Rupees", exchange_rate=Decimal("1.0000"))
        self.usd = Currency.objects.create(code="USD", name="Dollars", exchange_rate=Decimal("83.0000"))

    def test_simple_split_balances(self):
        # Aisha paid 900 INR for dinner, split equally among Aisha, Rohan, Priya.
        expense = Expense.objects.create(
            group=self.group,
            date=date(2026, 2, 10),
            description="Dinner",
            paid_by=self.aisha,
            amount=Decimal("900.00"),
            currency=self.inr,
            split_type="equal"
        )
        for u in [self.aisha, self.rohan, self.priya]:
            ExpenseSplit.objects.create(
                expenditure=expense,
                user=u,
                amount=Decimal("300.00"),
                amount_in_base=Decimal("300.00")
            )

        balances = calculate_group_balances(self.group)
        
        # Aisha paid 900, share is 300 -> net balance is +600 INR
        # Rohan paid 0, share is 300 -> net balance is -300 INR
        # Priya paid 0, share is 300 -> net balance is -300 INR
        summary = {u['username']: u['net_balance'] for u in balances['users_summary']}
        
        self.assertEqual(summary['Aisha'], Decimal('600.00'))
        self.assertEqual(summary['Rohan'], Decimal('-300.00'))
        self.assertEqual(summary['Priya'], Decimal('-300.00'))
        
        # Simplified debts: Rohan pays Aisha 300, Priya pays Aisha 300
        debts = balances['simplified_debts']
        self.assertEqual(len(debts), 2)
        
        # Verify debt details
        rohan_debt = next(d for d in debts if d['from_user'] == 'Rohan')
        self.assertEqual(rohan_debt['to_user'], 'Aisha')
        self.assertEqual(rohan_debt['amount'], Decimal('300.00'))
        
        priya_debt = next(d for d in debts if d['from_user'] == 'Priya')
        self.assertEqual(priya_debt['to_user'], 'Aisha')
        self.assertEqual(priya_debt['amount'], Decimal('300.00'))

    def test_usd_conversion_balances(self):
        # Rohan paid 100 USD (which is 8300 INR), split equally with Priya.
        expense = Expense.objects.create(
            group=self.group,
            date=date(2026, 3, 10),
            description="Hotel",
            paid_by=self.rohan,
            amount=Decimal("100.00"),
            currency=self.usd,
            split_type="equal"
        )
        # Rohan pays, splits with Rohan and Priya
        for u in [self.rohan, self.priya]:
            ExpenseSplit.objects.create(
                expenditure=expense,
                user=u,
                amount=Decimal("50.00"),
                amount_in_base=Decimal("4150.00")
            )

        balances = calculate_group_balances(self.group)
        summary = {u['username']: u['net_balance'] for u in balances['users_summary']}
        
        # Rohan paid 8300, share is 4150 -> net balance is +4150 INR
        # Priya paid 0, share is 4150 -> net balance is -4150 INR
        self.assertEqual(summary['Rohan'], Decimal('4150.00'))
        self.assertEqual(summary['Priya'], Decimal('-4150.00'))

    def test_detailed_breakdown_running_balance(self):
        # Aisha paid 900 INR (split 3 ways).
        expense1 = Expense.objects.create(
            group=self.group,
            date=date(2026, 2, 10),
            description="Dinner",
            paid_by=self.aisha,
            amount=Decimal("900.00"),
            currency=self.inr,
            split_type="equal"
        )
        for u in [self.aisha, self.rohan, self.priya]:
            ExpenseSplit.objects.create(
                expenditure=expense1,
                user=u,
                amount=Decimal("300.00"),
                amount_in_base=Decimal("300.00")
            )
            
        # Rohan paid Aisha back 300 INR (Settlement)
        sett = Settlement.objects.create(
            group=self.group,
            payer=self.rohan,
            payee=self.aisha,
            amount=Decimal("300.00"),
            currency=self.inr,
            date=date(2026, 2, 11)
        )
        
        # Fetch breakdown for Rohan
        breakdown = get_user_detailed_breakdown(self.group, self.rohan)
        
        self.assertEqual(len(breakdown), 2)
        
        # Item 1: Dinner expense. Net effect = -300
        self.assertEqual(breakdown[0]['description'], 'Dinner')
        self.assertEqual(breakdown[0]['net_effect'], Decimal('-300.00'))
        self.assertEqual(breakdown[0]['running_balance'], Decimal('-300.00'))
        
        # Item 2: Settlement. Net effect = +300
        self.assertEqual(breakdown[1]['net_effect'], Decimal('300.00'))
        self.assertEqual(breakdown[1]['running_balance'], Decimal('0.00'))
