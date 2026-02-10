# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('socios', '0003_tornar_campos_associacao_opcionais'),
    ]

    operations = [
        migrations.AddField(
            model_name='socio',
            name='rating_fexerj',
            field=models.IntegerField(blank=True, null=True, verbose_name='Rating FEXERJ'),
        ),
    ]
