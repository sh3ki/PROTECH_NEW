from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PROTECHAPP', '0018_systemsettings_spoof_proof_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsettings',
            name='gate_mode',
            field=models.CharField(
                choices=[('CLOSED', 'Closed Gate'), ('OPEN', 'Open Gate')],
                default='CLOSED',
                help_text='Select gate behavior: Closed applies class timing rules; Open allows free entry/exit and marks all logs On Time',
                max_length=10,
            ),
        ),
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together=set(),
        ),
    ]
