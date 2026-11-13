import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import Expense
from .forms import ExpenseForm, SignUpForm


def signup(request):
    """Register a new user, then log them in automatically."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully. Welcome!')
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def dashboard(request):
    """Show the logged-in user's expenses plus totals and a category breakdown."""
    expenses = Expense.objects.filter(user=request.user)

    # Grand total of all the user's expenses.
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    # Spending grouped by category, highest first.
    by_category = list(
        expenses.values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    # Attach a colour to each category row (for the list + chart).
    for row in by_category:
        row['color'] = Expense.CATEGORY_COLORS.get(row['category'], '#64748b')

    # Data for the Chart.js doughnut chart.
    chart_data = {
        'labels': [row['category'] for row in by_category],
        'data': [float(row['total']) for row in by_category],
        'colors': [row['color'] for row in by_category],
    }

    # The single biggest category (for a stat card).
    top_category = by_category[0]['category'] if by_category else '—'

    context = {
        'expenses': expenses,
        'total': total,
        'by_category': by_category,
        'count': expenses.count(),
        'top_category': top_category,
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'expenses/dashboard.html', context)


@login_required
def add_expense(request):
    """Create a new expense for the current user."""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user  # attach the logged-in user
            expense.save()
            messages.success(request, 'Expense added.')
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Add Expense'})


@login_required
def edit_expense(request, pk):
    """Edit an existing expense (only if it belongs to the current user)."""
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated.')
            return redirect('dashboard')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Edit Expense'})


@login_required
def delete_expense(request, pk):
    """Delete an expense after a confirmation page."""
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('dashboard')
    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})
