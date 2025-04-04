# Generated by Django 5.1.6 on 2025-03-25 16:38

import django.core.validators
import django.db.models.deletion
import main.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Quantity')),
                ('grand_total', models.PositiveIntegerField(default=0, verbose_name='Grand Total')),
            ],
            options={
                'verbose_name': 'Cart Item',
                'verbose_name_plural': 'Cart Items',
            },
        ),
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('shipped', 'Shipped'), ('delivered', 'Delivered')], default='pending', max_length=20, verbose_name='Status Delivery')),
                ('tracking_id', models.CharField(blank=True, max_length=20, unique=True, verbose_name='Tracking Number')),
                ('postman', models.CharField(blank=True, max_length=20, null=True, verbose_name='Postman Name')),
                ('shipped_at', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Shipped At')),
                ('delivered_at', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Delivered At')),
            ],
            options={
                'verbose_name': 'Delivery',
                'verbose_name_plural': 'Deliveries',
            },
        ),
        migrations.CreateModel(
            name='DeliverySchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivery_method', models.CharField(choices=[('normal', 'Normal Shipping'), ('fast', 'Fast Shipping'), ('postal', 'Postal Delivery')], max_length=20, verbose_name='Delivery Method')),
                ('date', models.DateField(verbose_name='Delivery Date')),
                ('day', models.CharField(editable=False, max_length=10, verbose_name='Day of the Week')),
                ('time', models.CharField(choices=[('8_10', '8 - 10'), ('10_12', '10 - 12'), ('12_14', '12 - 14'), ('14_16', '14 - 16'), ('16_18', '16 - 18'), ('18_20', '18 - 20'), ('20_22', '20 - 22')], max_length=10, verbose_name='Time')),
                ('delivery_cost', models.PositiveIntegerField(default=0, verbose_name='Delivery Cost')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Delivery Schedule',
                'verbose_name_plural': 'Delivery Schedules',
            },
        ),
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=main.models.upload_to, verbose_name='Image')),
            ],
            options={
                'verbose_name': 'Gallery',
                'verbose_name_plural': 'Galleries',
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(verbose_name='Message')),
                ('type', models.CharField(choices=[('order', 'Order Update'), ('promotion', 'Promotion'), ('system', 'System Alert')], max_length=20, verbose_name='Type')),
                ('is_read', models.BooleanField(default=False, verbose_name='Is Read')),
                ('related_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_type', models.CharField(choices=[('in_person', 'In-Person'), ('online', 'Online')], max_length=10, verbose_name='Order Type')),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('credit_card', 'Credit-Card'), ('online', 'Online')], max_length=15, verbose_name='Payment Method')),
                ('total_amount', models.PositiveIntegerField(default=0, verbose_name='Total Amount')),
                ('amount_payable', models.PositiveIntegerField(verbose_name='Amount Payable')),
                ('discount_applied', models.DecimalField(decimal_places=2, default=0, max_digits=4, verbose_name='Discount Applied')),
                ('status', models.CharField(choices=[('on_hold', 'On Hold'), ('waiting', 'Waiting for Payment'), ('successful', 'Successful Payment'), ('failed', 'Failed Payment'), ('shipped', 'Shipped'), ('completed', 'Completed Order'), ('canceled', 'Canceled Order'), ('refunded', 'Refunded Payment')], default='on_hold', max_length=20, verbose_name='Status')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250, verbose_name='Product')),
                ('slug', models.SlugField(editable=False, unique=True, verbose_name='Slug')),
                ('price', models.PositiveIntegerField(default=0, verbose_name='Price')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('image', models.ImageField(blank=True, null=True, upload_to=main.models.upload_to, verbose_name='Image')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
            },
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Rating')),
                ('review', models.TextField(blank=True, null=True, verbose_name='Review')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'Rating',
                'verbose_name_plural': 'Ratings',
            },
        ),
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_price', models.PositiveIntegerField(default=0, verbose_name='Total Price')),
            ],
            options={
                'verbose_name': 'Shopping Cart',
                'verbose_name_plural': 'Shopping Carts',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(verbose_name='Amount')),
                ('payment_id', models.CharField(blank=True, max_length=50, null=True, verbose_name='Payment ID')),
                ('is_successful', models.BooleanField(default=False, verbose_name='Is Successful')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
            },
        ),
        migrations.CreateModel(
            name='UserView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Viewed At')),
            ],
            options={
                'verbose_name': 'User View',
                'verbose_name_plural': 'User Views',
            },
        ),
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('warehouse_type', models.CharField(choices=[('input', 'Input'), ('output', 'Output'), ('sent_back', 'Sent Back'), ('defective', 'Defective')], max_length=20, verbose_name='Warehouse Type')),
                ('stock', models.PositiveIntegerField(default=0, verbose_name='Stock')),
                ('is_active', models.BooleanField(default=True, editable=False, verbose_name='Is Active')),
                ('price', models.IntegerField(default=0, verbose_name='Price')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Warehouse',
                'verbose_name_plural': 'Warehouses',
            },
        ),
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Wishlist',
                'verbose_name_plural': 'Wishlists',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Category')),
                ('slug', models.SlugField(editable=False, unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('image', models.ImageField(blank=True, null=True, upload_to=main.models.upload_to, verbose_name='Image')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Category_parent', to='main.category', verbose_name='Parent')),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=10, verbose_name='Code')),
                ('discount_percentage', models.DecimalField(decimal_places=2, max_digits=4, validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(50)], verbose_name='Discount Percentage')),
                ('max_usage', models.PositiveIntegerField(default=1, verbose_name='Maximum Usage')),
                ('usage_count', models.PositiveIntegerField(default=0, editable=False, verbose_name='Usage Count')),
                ('valid_from', models.DateTimeField(verbose_name='Valid From')),
                ('valid_to', models.DateTimeField(verbose_name='Valid To')),
                ('is_active', models.BooleanField(default=False, verbose_name='Is Active')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Coupon_category', to='main.category', verbose_name='Category')),
            ],
            options={
                'verbose_name': 'Coupon',
                'verbose_name_plural': 'Coupons',
            },
        ),
    ]
