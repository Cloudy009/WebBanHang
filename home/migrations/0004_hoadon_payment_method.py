# Generated by Django 4.2 on 2024-10-25 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_userprofile_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='hoadon',
            name='payment_method',
            field=models.CharField(choices=[('credit', 'Credit/Debit Card'), ('paypal', 'Paypal'), ('cod', 'Cash on Delivery')], default='cod', max_length=10),
        ),
    ]
