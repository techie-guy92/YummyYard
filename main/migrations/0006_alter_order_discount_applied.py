# Generated by Django 5.1.6 on 2025-04-05 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_alter_coupon_discount_percentage_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='discount_applied',
            field=models.IntegerField(default=0, verbose_name='Discount Applied'),
        ),
    ]
