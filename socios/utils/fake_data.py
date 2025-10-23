import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from faker import Faker
import random
from decimal import Decimal
from datetime import timedelta

from ..models import Socio, TipoAssinatura, HistoricoPagamento
from django.contrib.auth import get_user_model

fake = Faker("pt_BR")  # localidade brasileira

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@email.com")
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())


class TipoAssinaturaFactory(DjangoModelFactory):
    class Meta:
        model = TipoAssinatura
    
    nome = factory.LazyAttribute(lambda _: random.choice([
        "Sócio Básico", "Sócio Premium", "Sócio Estudante", 
        "Sócio Família", "Sócio Senior", "Sócio Profissional"
    ]))
    descricao = factory.LazyAttribute(lambda obj: f"Plano {obj.nome.lower()}")
    valor_mensal = factory.LazyAttribute(lambda _: Decimal(str(random.randint(50, 200))))
    valor_anual = factory.LazyAttribute(lambda obj: obj.valor_mensal * 10)
    duracao_dias = 30
    cor = factory.LazyAttribute(lambda _: random.choice([
        "#3498db", "#f39c12", "#27ae60", "#e74c3c", "#9b59b6", "#34495e"
    ]))
    ativo = True
    acesso_torneios = True
    desconto_eventos = factory.LazyAttribute(lambda _: Decimal(str(random.randint(0, 20))))
    aulas_incluidas = factory.LazyAttribute(lambda _: random.randint(0, 8))


class SocioFactory(DjangoModelFactory):
    class Meta:
        model = Socio

    usuario = factory.SubFactory(UserFactory)

    numero_socio = factory.Sequence(lambda n: str(n + 1000).zfill(6))
    nome_completo = factory.LazyAttribute(lambda _: fake.name())
    nome_social = factory.LazyAttribute(lambda _: fake.first_name() if random.random() > 0.7 else "")
    
    cpf = factory.LazyAttribute(lambda _: fake.cpf())
    rg = factory.LazyAttribute(lambda _: str(fake.random_int(min=1000000, max=9999999)))

    data_nascimento = factory.LazyAttribute(lambda _: fake.date_of_birth(minimum_age=16, maximum_age=90))
    genero = factory.LazyAttribute(lambda _: random.choice(['M', 'F', 'NB', 'O', 'N']))

    telefone = factory.LazyAttribute(lambda _: f"({fake.random_int(11, 99)}) 9{fake.random_int(1000, 9999)}-{fake.random_int(1000, 9999)}")
    celular = factory.LazyAttribute(lambda _: f"({fake.random_int(11, 99)}) 9{fake.random_int(1000, 9999)}-{fake.random_int(1000, 9999)}")
    email = factory.LazyAttribute(lambda _: fake.unique.email())

    cep = factory.LazyAttribute(lambda _: f"{fake.random_int(10000, 99999)}-{fake.random_int(100, 999)}")
    endereco = factory.LazyAttribute(lambda _: fake.street_name())
    numero = factory.LazyAttribute(lambda _: str(fake.building_number()))
    complemento = factory.LazyAttribute(lambda _: f"Apto {fake.random_int(min=1, max=500)}" if random.random() > 0.6 else "")
    bairro = factory.LazyAttribute(lambda _: fake.neighborhood())
    cidade = factory.LazyAttribute(lambda _: fake.city())
    estado = factory.LazyAttribute(lambda _: random.choice(['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'GO', 'MT', 'MS', 'BA']))

    rating_fide = factory.LazyAttribute(lambda _: random.randint(1000, 2500) if random.random() > 0.5 else None)
    rating_cbx = factory.LazyAttribute(lambda _: random.randint(1000, 2500) if random.random() > 0.5 else None)
    categoria_cbx = factory.LazyAttribute(lambda _: random.choice(["Sub-16", "Sub-18", "Adulto", "Senior", ""]) )

    # tipo_assinatura will be set manually in create_demo_data
    data_associacao = factory.LazyAttribute(lambda _: fake.date_between(start_date="-2y", end_date="today"))
    data_vencimento = factory.LazyAttribute(lambda obj: obj.data_associacao + timedelta(days=random.randint(30, 400)))

    status = factory.LazyAttribute(lambda _: random.choices(
        ['ativo', 'inadimplente', 'suspenso', 'inativo'],
        weights=[70, 15, 10, 5],  # 70% active, 15% overdue, 10% suspended, 5% inactive
        k=1
    )[0])
    
    profissao = factory.LazyAttribute(lambda _: fake.job())
    observacoes = factory.LazyAttribute(lambda _: fake.sentence(nb_words=10))
    
    aceita_emails = factory.LazyAttribute(lambda _: fake.boolean())
    aceita_whatsapp = factory.LazyAttribute(lambda _: fake.boolean())

    created_by = factory.SubFactory(UserFactory)


class HistoricoPagamentoFactory(DjangoModelFactory):
    class Meta:
        model = HistoricoPagamento
    
    socio = factory.SubFactory(SocioFactory)
    data_pagamento = factory.LazyAttribute(lambda _: fake.date_between(start_date="-1y", end_date="today"))
    data_vencimento = factory.LazyAttribute(lambda obj: obj.data_pagamento + timedelta(days=30))
    valor = factory.LazyAttribute(lambda obj: obj.socio.tipo_assinatura.valor_mensal)
    mes_referencia = factory.LazyAttribute(lambda obj: obj.data_pagamento.replace(day=1))
    forma_pagamento = factory.LazyAttribute(lambda _: random.choice([
        'dinheiro', 'cartao_debito', 'cartao_credito', 'pix', 'transferencia', 'boleto'
    ]))
    status = factory.LazyAttribute(lambda _: random.choice(['pendente', 'confirmado', 'cancelado']))
    descricao = factory.LazyAttribute(lambda _: fake.text(max_nb_chars=100) if random.random() > 0.7 else "")
    created_by = factory.SubFactory(UserFactory)


def create_demo_data(num_tipos=5, num_socios=15, num_pagamentos_per_socio=4, clean_first=False):
    """Cria dados de demonstração para o sistema"""
    
    if clean_first:
        print("🗑️ Cleaning existing data...")
        HistoricoPagamento.objects.all().delete()
        Socio.objects.all().delete() 
        TipoAssinatura.objects.all().delete()
        User.objects.filter(username__startswith='user_').delete()
        print("✅ Cleanup complete!")
    
    print(f"🚀 Creating demo data for ClubPro...")
    
    # Criar admin user se não existir
    admin_user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            'email': 'admin@clubpro.com',
            'first_name': 'Admin',
            'last_name': 'ClubPro',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("✅ Admin user created (admin/admin123)")
    
    print(f"📋 Creating predefined membership types...")
    
    # Create specific membership types
    tipos_data = [
        {"nome": "Sócio Básico", "valor": 80, "cor": "#3498db", "desconto": 0},
        {"nome": "Sócio Premium", "valor": 150, "cor": "#f39c12", "desconto": 10},
        {"nome": "Sócio Estudante", "valor": 50, "cor": "#27ae60", "desconto": 5},
        {"nome": "Sócio Família", "valor": 200, "cor": "#e74c3c", "desconto": 15},
        {"nome": "Sócio Senior", "valor": 60, "cor": "#9b59b6", "desconto": 20},
        {"nome": "Sócio Profissional", "valor": 120, "cor": "#34495e", "desconto": 5},
    ]
    
    tipos = []
    for tipo_info in tipos_data:
        tipo, created = TipoAssinatura.objects.get_or_create(
            nome=tipo_info["nome"],
            defaults={
                'descricao': f'Plano {tipo_info["nome"].lower()}',
                'valor_mensal': Decimal(str(tipo_info["valor"])),
                'valor_anual': Decimal(str(tipo_info["valor"] * 10)),
                'duracao_dias': 30,
                'cor': tipo_info["cor"],
                'ativo': True,
                'acesso_torneios': True,
                'desconto_eventos': Decimal(str(tipo_info["desconto"])),
                'aulas_incluidas': random.randint(0, 4)
            }
        )
        tipos.append(tipo)
    
    print(f"👥 Creating {num_socios} members...")
    socios = []
    for i in range(num_socios):
        socio = SocioFactory.create(
            created_by=admin_user,
            tipo_assinatura=random.choice(tipos)  # Assign from our created types
        )
        socios.append(socio)
    
    print(f"💰 Creating payment history...")
    total_payments = 0
    for socio in socios:
        
        num_payments = random.randint(1, num_pagamentos_per_socio)
        HistoricoPagamentoFactory.create_batch(
            num_payments, 
            socio=socio, 
            created_by=admin_user
        )
        total_payments += num_payments
    
    print("✅ Demo data created successfully!")
    print(f"📊 Summary:")
    print(f"   - {len(tipos)} membership types: {[t.nome for t in tipos]}")
    print(f"   - {len(socios)} members")
    print(f"   - {total_payments} payments")
    print("🎯 Your ClubPro is ready for presentation!")
    
    return tipos, socios


# Quick usage:
# python manage.py shell
# >>> from socios.utils.fake_data import create_demo_data
# >>> create_demo_data()
