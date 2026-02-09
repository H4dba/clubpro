# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('socios', '0002_add_campos_cadastro_socio'),
    ]

    operations = [
        # Tornar tipo_assinatura opcional
        migrations.AlterField(
            model_name='socio',
            name='tipo_assinatura',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='socios.tipoassinatura',
                verbose_name='Tipo de Assinatura'
            ),
        ),
        
        # Tornar data_associacao opcional
        migrations.AlterField(
            model_name='socio',
            name='data_associacao',
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name='Data de Associação'
            ),
        ),
        
        # Tornar data_vencimento opcional
        migrations.AlterField(
            model_name='socio',
            name='data_vencimento',
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name='Data de Vencimento'
            ),
        ),
    ]
