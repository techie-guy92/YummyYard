# Generated by Django 5.1.6 on 2025-03-25 16:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('main', '0001_initial'),
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryschedule',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='DeliverySchedule_user', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AddField(
            model_name='notification',
            name='related_object_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='notification',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Notification_user', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AddField(
            model_name='order',
            name='coupon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.coupon', verbose_name='Coupon'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_schedule',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.deliveryschedule', verbose_name='Delivery Schedule'),
        ),
        migrations.AddField(
            model_name='order',
            name='in_person_customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Order_in_person_customers', to='users.inpersoncustomer', verbose_name='In-Person Customer'),
        ),
        migrations.AddField(
            model_name='order',
            name='online_customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Order_online_customers', to=settings.AUTH_USER_MODEL, verbose_name='Online Customer'),
        ),
        migrations.AddField(
            model_name='delivery',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Delivery_order', to='main.order', verbose_name='Order'),
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Product_category', to='main.category', verbose_name='Category'),
        ),
        migrations.AddField(
            model_name='gallery',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Gallery_product', to='main.product', verbose_name='Product'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='CartItem_product', to='main.product', verbose_name='Product'),
        ),
        migrations.AddField(
            model_name='rating',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Rating_product', to='main.product', verbose_name='Product'),
        ),
        migrations.AddField(
            model_name='rating',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Rating_user', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AddField(
            model_name='shoppingcart',
            name='in_person_customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ShoppingCart_in_person_customers', to='users.inpersoncustomer', verbose_name='In-Person Customer'),
        ),
        migrations.AddField(
            model_name='shoppingcart',
            name='online_customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ShoppingCart_online_customers', to=settings.AUTH_USER_MODEL, verbose_name='Online Customer'),
        ),
        migrations.AddField(
            model_name='shoppingcart',
            name='products',
            field=models.ManyToManyField(related_name='ShoppingCart_products', through='main.CartItem', to='main.product', verbose_name='Products'),
        ),
        migrations.AddField(
            model_name='order',
            name='shopping_cart',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='Order_shopping_cart', to='main.shoppingcart', verbose_name='Shopping Cart'),
        ),
        migrations.AddField(
            model_name='deliveryschedule',
            name='shopping_cart',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='DeliverySchedule_shopping_cart', to='main.shoppingcart', verbose_name='Shopping Cart'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='cart',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='CartItem_cart', to='main.shoppingcart', verbose_name='Cart'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Transaction_order', to='main.order', verbose_name='Order'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Transaction_user', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AddField(
            model_name='userview',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='UserView_product', to='main.product', verbose_name='Product'),
        ),
        migrations.AddField(
            model_name='userview',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='UserView_user', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AddField(
            model_name='warehouse',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Warehouse_product', to='main.product', verbose_name='Product'),
        ),
        migrations.AddField(
            model_name='wishlist',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Wishlist_product', to='main.product', verbose_name='Product'),
        ),
        migrations.AddField(
            model_name='wishlist',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Wishlist_user', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['name'], name='main_catego_name_5111b9_idx'),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['parent'], name='main_catego_parent__a9ff92_idx'),
        ),
        migrations.AddIndex(
            model_name='coupon',
            index=models.Index(fields=['is_active'], name='main_coupon_is_acti_27838a_idx'),
        ),
        migrations.AddIndex(
            model_name='coupon',
            index=models.Index(fields=['valid_from'], name='main_coupon_valid_f_ebc34b_idx'),
        ),
        migrations.AddIndex(
            model_name='coupon',
            index=models.Index(fields=['valid_to'], name='main_coupon_valid_t_16ecec_idx'),
        ),
        migrations.AddIndex(
            model_name='delivery',
            index=models.Index(fields=['order'], name='main_delive_order_i_7acffc_idx'),
        ),
        migrations.AddIndex(
            model_name='delivery',
            index=models.Index(fields=['status'], name='main_delive_status_350e06_idx'),
        ),
        migrations.AddIndex(
            model_name='delivery',
            index=models.Index(fields=['tracking_id'], name='main_delive_trackin_8ef715_idx'),
        ),
        migrations.AddIndex(
            model_name='delivery',
            index=models.Index(fields=['delivered_at'], name='main_delive_deliver_18c758_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['name'], name='main_produc_name_168fc5_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['price'], name='main_produc_price_98d31c_idx'),
        ),
        migrations.AddIndex(
            model_name='rating',
            index=models.Index(fields=['user'], name='main_rating_user_id_adeca3_idx'),
        ),
        migrations.AddIndex(
            model_name='rating',
            index=models.Index(fields=['product'], name='main_rating_product_39c42d_idx'),
        ),
        migrations.AddIndex(
            model_name='rating',
            index=models.Index(fields=['rating'], name='main_rating_rating_6605ad_idx'),
        ),
        migrations.AddConstraint(
            model_name='rating',
            constraint=models.UniqueConstraint(fields=('user', 'product'), name='unique_user_product_rating'),
        ),
        migrations.AddIndex(
            model_name='shoppingcart',
            index=models.Index(fields=['online_customer'], name='main_shoppi_online__6f7f88_idx'),
        ),
        migrations.AddIndex(
            model_name='shoppingcart',
            index=models.Index(fields=['in_person_customer'], name='main_shoppi_in_pers_275d38_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['online_customer'], name='main_order_online__941be1_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['in_person_customer'], name='main_order_in_pers_213ebc_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['status'], name='main_order_status_4d3738_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['order_type'], name='main_order_order_t_015705_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryschedule',
            index=models.Index(fields=['date'], name='main_delive_date_ec58fb_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryschedule',
            index=models.Index(fields=['day'], name='main_delive_day_27c48e_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryschedule',
            index=models.Index(fields=['time'], name='main_delive_time_8622f3_idx'),
        ),
        migrations.AddIndex(
            model_name='cartitem',
            index=models.Index(fields=['cart'], name='main_cartit_cart_id_8b08d4_idx'),
        ),
        migrations.AddIndex(
            model_name='cartitem',
            index=models.Index(fields=['product'], name='main_cartit_product_ef6c1e_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['user'], name='main_transa_user_id_553a48_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['order'], name='main_transa_order_i_2edbd5_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['payment_id'], name='main_transa_payment_e3dd0a_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['created_at'], name='main_transa_created_2e183b_idx'),
        ),
        migrations.AddIndex(
            model_name='userview',
            index=models.Index(fields=['user'], name='main_uservi_user_id_0418ca_idx'),
        ),
        migrations.AddIndex(
            model_name='userview',
            index=models.Index(fields=['product'], name='main_uservi_product_0e8055_idx'),
        ),
        migrations.AddIndex(
            model_name='warehouse',
            index=models.Index(fields=['product'], name='main_wareho_product_519b2a_idx'),
        ),
        migrations.AddIndex(
            model_name='warehouse',
            index=models.Index(fields=['warehouse_type'], name='main_wareho_warehou_46ea45_idx'),
        ),
        migrations.AddIndex(
            model_name='warehouse',
            index=models.Index(fields=['stock'], name='main_wareho_stock_ab8cc9_idx'),
        ),
        migrations.AddIndex(
            model_name='warehouse',
            index=models.Index(fields=['created_at'], name='main_wareho_created_13906f_idx'),
        ),
        migrations.AddIndex(
            model_name='wishlist',
            index=models.Index(fields=['product'], name='main_wishli_product_b0f13a_idx'),
        ),
    ]
