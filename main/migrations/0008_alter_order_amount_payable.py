# Generated by Django 5.1.6 on 2025-04-05 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_alter_coupon_discount_percentage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='amount_payable',
            field=models.PositiveIntegerField(default=0, verbose_name='Amount Payable'),
        ),
    ]
