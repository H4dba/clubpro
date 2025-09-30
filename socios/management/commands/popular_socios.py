from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from socios.models import TipoAssinatura, Socio
from datetime import date, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula o sistema com dados de exemplo para demonstração'

    def add_arguments(self, parser):
        parser.add_argument(
            '--socios',
            type=int,
            default=20,
            help='Número de sócios de exemplo para criar'
        )
        
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Remove todos os dados existentes antes de popular'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Removendo dados existentes...')
            Socio.objects.all().delete()
            TipoAssinatura.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Dados removidos com sucesso!'))

        # Criar tipos de assinatura se não existirem
        self.criar_tipos_assinatura()
        
        # Criar sócios de exemplo
        num_socios = options['socios']
        self.criar_socios_exemplo(num_socios)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Sistema populado com sucesso! {num_socios} sócios criados.'
            )
        )

    def criar_tipos_assinatura(self):
        tipos = [
            {
                'nome': 'Mensalidade Básica',
                'descricao': 'Plano básico com acesso às dependências do clube',
                'valor': 150.00,
                'periodicidade': 'mensal',
                'cor': '#3498db'
            },
            {
                'nome': 'Mensalidade Premium',
                'descricao': 'Plano premium com aulas particulares incluídas',
                'valor': 250.00,
                'periodicidade': 'mensal',
                'cor': '#9b59b6'
            },
            {
                'nome': 'Trimestral',
                'descricao': 'Pagamento trimestral com desconto',
                'valor': 400.00,
                'periodicidade': 'trimestral',
                'cor': '#27ae60'
            },
            {
                'nome': 'Anual',
                'descricao': 'Pagamento anual com maior desconto',
                'valor': 1500.00,
                'periodicidade': 'anual',
                'cor': '#f39c12'
            },
            {
                'nome': 'Estudante',
                'descricao': 'Plano especial para estudantes (com comprovante)',
                'valor': 80.00,
                'periodicidade': 'mensal',
                'cor': '#e74c3c'
            }
        ]
        
        for tipo_data in tipos:
            tipo, created = TipoAssinatura.objects.get_or_create(
                nome=tipo_data['nome'],
                defaults=tipo_data
            )
            if created:
                self.stdout.write(f'Tipo de assinatura criado: {tipo.nome}')

    def criar_socios_exemplo(self, num_socios):
        nomes = [
            'Ana Silva Santos', 'Carlos Eduardo Oliveira', 'Maria José da Costa',
            'João Pedro Almeida', 'Fernanda Lima Souza', 'Ricardo Mendes Pereira',
            'Juliana Rodrigues', 'Paulo César Martins', 'Beatriz Ferreira',
            'André Luis Barbosa', 'Camila Santos', 'Diego Nascimento',
            'Larissa Campos', 'Marcos Vinícius', 'Patrícia Gomes',
            'Thiago Araújo', 'Vanessa Cardoso', 'Rafael Monteiro',
            'Isabela Costa', 'Leonardo Ribeiro', 'Natália Torres',
            'Gustavo Pinto', 'Priscila Dias', 'Henrique Castro',
            'Amanda Rocha', 'Bruno Carvalho', 'Letícia Moreira',
            'Rodrigo Silva', 'Daniela Freitas', 'Mateus Gonçalves'
        ]
        
        emails = [
            'ana.santos@email.com', 'carlos.oliveira@gmail.com', 'maria.costa@hotmail.com',
            'joao.almeida@yahoo.com', 'fernanda.lima@outlook.com', 'ricardo.pereira@gmail.com',
            'juliana.rodrigues@email.com', 'paulo.martins@hotmail.com', 'beatriz.ferreira@gmail.com',
            'andre.barbosa@yahoo.com', 'camila.santos@outlook.com', 'diego.nascimento@gmail.com',
            'larissa.campos@email.com', 'marcos.vinicius@hotmail.com', 'patricia.gomes@gmail.com',
            'thiago.araujo@yahoo.com', 'vanessa.cardoso@outlook.com', 'rafael.monteiro@gmail.com',
            'isabela.costa@email.com', 'leonardo.ribeiro@hotmail.com', 'natalia.torres@gmail.com',
            'gustavo.pinto@yahoo.com', 'priscila.dias@outlook.com', 'henrique.castro@gmail.com',
            'amanda.rocha@email.com', 'bruno.carvalho@hotmail.com', 'leticia.moreira@gmail.com',
            'rodrigo.silva@yahoo.com', 'daniela.freitas@outlook.com', 'mateus.goncalves@gmail.com'
        ]
        
        telefones = [
            '(11) 99999-1111', '(11) 98888-2222', '(21) 97777-3333',
            '(31) 96666-4444', '(41) 95555-5555', '(51) 94444-6666',
            '(61) 93333-7777', '(71) 92222-8888', '(81) 91111-9999',
            '(85) 99888-0000', '(11) 98765-4321', '(21) 97654-3210',
            '(31) 96543-2109', '(41) 95432-1098', '(51) 94321-0987',
            '(61) 93210-9876', '(71) 92109-8765', '(81) 91098-7654',
            '(85) 90987-6543', '(11) 89876-5432', '(21) 88765-4321',
            '(31) 87654-3210', '(41) 86543-2109', '(51) 85432-1098',
            '(61) 84321-0987', '(71) 83210-9876', '(81) 82109-8765',
            '(85) 81098-7654', '(11) 80987-6543', '(21) 79876-5432'
        ]
        
        tipos_assinatura = list(TipoAssinatura.objects.filter(ativo=True))
        
        for i in range(num_socios):
            # Dados básicos
            nome_completo = random.choice(nomes)
            nomes = [n for n in nomes if n != nome_completo]  # Remove para não repetir
            
            # CPF fictício (apenas para exemplo - não válido)
            cpf = f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}"
            
            # Datas
            data_nascimento = date.today() - timedelta(days=random.randint(6570, 25550))  # 18 a 70 anos
            data_associacao = date.today() - timedelta(days=random.randint(30, 1095))  # 1 mês a 3 anos
            
            # Status e vencimento baseados na probabilidade
            status_choices = ['ativo', 'ativo', 'ativo', 'inadimplente', 'suspenso']  # Mais ativos
            status = random.choice(status_choices)
            
            if status == 'ativo':
                # Sócios ativos: vencimento futuro ou próximo
                dias_vencimento = random.randint(-5, 30)
            elif status == 'inadimplente':
                # Inadimplentes: vencimento passado
                dias_vencimento = random.randint(-60, -1)
            else:
                # Suspensos: pode variar
                dias_vencimento = random.randint(-30, 15)
            
            data_vencimento = date.today() + timedelta(days=dias_vencimento)
            
            # Criar sócio
            socio = Socio.objects.create(
                nome=nome_completo,
                nome_preferencia=nome_completo.split()[0] if random.choice([True, False]) else None,
                cpf=cpf,
                data_nascimento=data_nascimento,
                genero=random.choice(['M', 'F', 'O', None]),
                email=emails[i] if i < len(emails) else f'socio{i+1}@exemplo.com',
                telefone=telefones[i] if i < len(telefones) else f'(11) 9999-{i+1000:04d}',
                endereco=f'Rua Exemplo, {random.randint(100, 9999)} - São Paulo, SP' if random.choice([True, False]) else None,
                tipo_assinatura=random.choice(tipos_assinatura),
                data_associacao=data_associacao,
                data_vencimento=data_vencimento,
                status=status,
                rating_fide=random.randint(1200, 2400) if random.choice([True, False, False]) else None,
                rating_nacional=random.randint(1000, 2200) if random.choice([True, False]) else None,
                categoria=random.choice(['A', 'B', 'C', 'D', None, None]),
                observacoes='Sócio criado automaticamente para demonstração.' if random.choice([True, False, False]) else None
            )
            
            self.stdout.write(f'Sócio criado: {socio.numero_socio} - {socio.nome} ({socio.get_status_display()})')
            
            # Criar alguns pagamentos para alguns sócios
            if random.choice([True, False, False]) and status in ['ativo', 'inadimplente']:
                from socios.models import HistoricoPagamento
                
                num_pagamentos = random.randint(1, 6)
                for j in range(num_pagamentos):
                    data_pagamento = data_associacao + timedelta(days=j*30 + random.randint(0, 10))
                    if data_pagamento <= date.today():
                        mes_ref = data_pagamento.replace(day=1)
                        
                        HistoricoPagamento.objects.create(
                            socio=socio,
                            valor=socio.tipo_assinatura.valor + random.uniform(-10, 10),
                            data_pagamento=data_pagamento,
                            mes_referencia=mes_ref,
                            status='pago',
                            observacoes='Pagamento de exemplo'
                        )