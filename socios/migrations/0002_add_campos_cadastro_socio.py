# Generated manually

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('socios', '0001_initial'),
    ]

    operations = [
        # Nível do aluno
        migrations.AddField(
            model_name='socio',
            name='nivel_aluno',
            field=models.CharField(blank=True, choices=[('iniciante', 'Iniciante'), ('intermediario', 'Intermediário'), ('avancado', 'Avançado'), ('mestre', 'Mestre')], max_length=20, verbose_name='Nível do Aluno'),
        ),
        
        # Plataformas e ratings Lichess
        migrations.AddField(
            model_name='socio',
            name='possui_lichess',
            field=models.BooleanField(default=False, verbose_name='Possui conta Lichess'),
        ),
        migrations.AddField(
            model_name='socio',
            name='rating_lichess_rapid',
            field=models.IntegerField(blank=True, null=True, verbose_name='Rating Lichess Rapid'),
        ),
        migrations.AddField(
            model_name='socio',
            name='rating_lichess_blitz',
            field=models.IntegerField(blank=True, null=True, verbose_name='Rating Lichess Blitz'),
        ),
        migrations.AddField(
            model_name='socio',
            name='rating_lichess_bullet',
            field=models.IntegerField(blank=True, null=True, verbose_name='Rating Lichess Bullet'),
        ),
        migrations.AddField(
            model_name='socio',
            name='rating_lichess_classical',
            field=models.IntegerField(blank=True, null=True, verbose_name='Rating Lichess Classical'),
        ),
        
        # Plataformas e ratings Chess.com
        migrations.AddField(
            model_name='socio',
            name='possui_chesscom',
            field=models.BooleanField(default=False, verbose_name='Possui conta Chess.com'),
        ),
        migrations.AddField(
            model_name='socio',
            name='rating_chesscom_rapid',
            field=models.IntegerField(blank=True, null=True, verbose_name='Rating Chess.com Rapid'),
        ),
        migrations.AddField(
            model_name='socio',
            name='rating_chesscom_blitz',
            field=models.IntegerField(blank=True, null=True, verbose_name='Rating Chess.com Blitz'),
        ),
        migrations.AddField(
            model_name='socio',
            name='rating_chesscom_bullet',
            field=models.IntegerField(blank=True, null=True, verbose_name='Rating Chess.com Bullet'),
        ),
        
        # Participação em torneios
        migrations.AddField(
            model_name='socio',
            name='ja_participou_torneios',
            field=models.BooleanField(default=False, verbose_name='Já Participou de Torneios'),
        ),
        
        # Dados do responsável
        migrations.AddField(
            model_name='socio',
            name='nome_responsavel',
            field=models.CharField(blank=True, max_length=200, verbose_name='Nome do Responsável'),
        ),
        migrations.AddField(
            model_name='socio',
            name='grau_parentesco',
            field=models.CharField(blank=True, choices=[('pai', 'Pai'), ('mae', 'Mãe'), ('avo', 'Avô/Avó'), ('tio', 'Tio/Tia'), ('irmao', 'Irmão/Irmã'), ('tutor', 'Tutor Legal'), ('outro', 'Outro')], max_length=20, verbose_name='Grau de Parentesco'),
        ),
        migrations.AddField(
            model_name='socio',
            name='cpf_responsavel',
            field=models.CharField(blank=True, max_length=14, validators=[django.core.validators.RegexValidator(message='CPF deve estar no formato XXX.XXX.XXX-XX ou apenas números', regex='^\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}$|^\\d{11}$')], verbose_name='CPF do Responsável'),
        ),
        migrations.AddField(
            model_name='socio',
            name='telefone_responsavel',
            field=models.CharField(blank=True, max_length=20, validators=[django.core.validators.RegexValidator(message='Telefone deve estar no formato (XX) XXXXX-XXXX', regex='^\\(\\d{2}\\)\\s\\d{4,5}-\\d{4}$|^\\d{10,11}$')], verbose_name='Telefone do Responsável'),
        ),
        migrations.AddField(
            model_name='socio',
            name='email_responsavel',
            field=models.EmailField(blank=True, max_length=254, verbose_name='E-mail do Responsável'),
        ),
    ]
