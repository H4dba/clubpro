from django.core.management.base import BaseCommand
from django.utils import timezone
from socios.models import Socio

class Command(BaseCommand):
    help = 'Varre os sócios ativos e atualiza para inadimplente aqueles cujas mensalidades venceram'

    def handle(self, *args, **options):
        hoje = timezone.now().date()
        self.stdout.write(f'Iniciando verificação de vencimentos para a data: {hoje}')

        # Sócios ativos, que não são bolsistas e que têm data de vencimento menor que hoje
        socios_vencidos = Socio.objects.filter(
            status='ativo',
            bolsista=False,
            data_vencimento__lt=hoje
        )

        total_vencidos = socios_vencidos.count()

        if total_vencidos == 0:
            self.stdout.write(self.style.SUCCESS('Nenhum sócio ativo com pagamento vencido encontrado.'))
            return

        for socio in socios_vencidos:
            old_status = socio.status
            socio.status = 'inadimplente'
            socio.save(update_fields=['status'])
            self.stdout.write(
                f'Sócio Nº {socio.numero_socio} - {socio.nome_completo}: status alterado de {old_status} para inadimplente (vencimento: {socio.data_vencimento})'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Verificação concluída. Total de {total_vencidos} sócios atualizados para inadimplente.'
            )
        )
