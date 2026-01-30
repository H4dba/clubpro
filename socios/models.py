from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class TipoAssinatura(models.Model):
    """Tipos de assinatura/planos disponíveis para sócios"""
    nome = models.CharField(max_length=100, verbose_name="Nome do Plano")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    valor_mensal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Valor Mensal (R$)"
    )
    valor_anual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Valor Anual (R$)",
        help_text="Deixe em branco se não houver desconto anual"
    )
    duracao_dias = models.IntegerField(
        default=30, 
        verbose_name="Duração em Dias",
        help_text="Duração padrão da assinatura em dias"
    )
    cor = models.CharField(
        max_length=7, 
        default="#3498db",
        verbose_name="Cor do Plano",
        help_text="Cor hexadecimal para identificação visual"
    )
    ativo = models.BooleanField(default=True, verbose_name="Plano Ativo")
    
    # Benefícios
    acesso_torneios = models.BooleanField(default=True, verbose_name="Acesso a Torneios")
    desconto_eventos = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name="Desconto em Eventos (%)"
    )
    aulas_incluidas = models.IntegerField(
        default=0, 
        verbose_name="Aulas Incluídas por Mês"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Tipo de Assinatura"
        verbose_name_plural = "Tipos de Assinatura"
        ordering = ['valor_mensal']

    def __str__(self):
        return f"{self.nome} - R$ {self.valor_mensal}/mês"

    @property
    def valor_anual_com_desconto(self):
        """Calcula o valor anual com possível desconto"""
        if self.valor_anual:
            return self.valor_anual
        return self.valor_mensal * 12

    @property
    def percentual_desconto_anual(self):
        """Calcula o percentual de desconto no plano anual"""
        if self.valor_anual:
            valor_mensal_x12 = self.valor_mensal * 12
            desconto = valor_mensal_x12 - self.valor_anual
            return (desconto / valor_mensal_x12) * 100
        return 0


class Socio(models.Model):
    """Modelo principal para sócios do clube"""
    
    # Relacionamento com usuário do sistema
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Usuário do Sistema",
        help_text="Usuário vinculado no sistema (opcional)"
    )
    
    # Dados pessoais básicos
    numero_socio = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Número do Sócio",
        help_text="Número único de identificação do sócio"
    )
    nome_completo = models.CharField(max_length=200, verbose_name="Nome Completo")
    nome_social = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="Nome Social",
        help_text="Nome pelo qual prefere ser chamado"
    )
    
    # Documentos
    cpf_validator = RegexValidator(
        regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{11}$',
        message="CPF deve estar no formato XXX.XXX.XXX-XX ou apenas números"
    )
    cpf = models.CharField(
        max_length=14, 
        validators=[cpf_validator],
        unique=True,
        verbose_name="CPF"
    )
    rg = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="RG"
    )
    
    # Dados pessoais
    data_nascimento = models.DateField(verbose_name="Data de Nascimento")
    genero_choices = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('NB', 'Não-binário'),
        ('O', 'Outro'),
        ('N', 'Prefiro não informar'),
    ]
    genero = models.CharField(
        max_length=2, 
        choices=genero_choices,
        verbose_name="Gênero"
    )
    
    # Contato
    telefone_validator = RegexValidator(
        regex=r'^\(\d{2}\)\s\d{4,5}-\d{4}$|^\d{10,11}$',
        message="Telefone deve estar no formato (XX) XXXXX-XXXX"
    )
    telefone = models.CharField(
        max_length=20, 
        validators=[telefone_validator],
        verbose_name="Telefone"
    )
    celular = models.CharField(
        max_length=20, 
        validators=[telefone_validator],
        blank=True,
        verbose_name="Celular"
    )
    email = models.EmailField(verbose_name="E-mail")
    
    # Endereço
    cep = models.CharField(max_length=10, verbose_name="CEP")
    endereco = models.CharField(max_length=255, verbose_name="Rua")
    numero = models.CharField(max_length=10, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    estado = models.CharField(max_length=2, verbose_name="Estado (UF)")
    
    # Dados do xadrez
    nivel_aluno_choices = [
        ('iniciante', 'Iniciante'),
        ('intermediario', 'Intermediário'),
        ('avancado', 'Avançado'),
        ('mestre', 'Mestre'),
    ]
    nivel_aluno = models.CharField(
        max_length=20,
        choices=nivel_aluno_choices,
        blank=True,
        verbose_name="Nível do Aluno"
    )
    
    rating_fide = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Rating FIDE"
    )
    rating_cbx = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Rating CBX"
    )
    categoria_cbx = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Categoria CBX"
    )
    
    # Plataformas de xadrez
    possui_lichess = models.BooleanField(default=False, verbose_name="Possui conta Lichess")
    rating_lichess_rapid = models.IntegerField(null=True, blank=True, verbose_name="Rating Lichess Rapid")
    rating_lichess_blitz = models.IntegerField(null=True, blank=True, verbose_name="Rating Lichess Blitz")
    rating_lichess_bullet = models.IntegerField(null=True, blank=True, verbose_name="Rating Lichess Bullet")
    rating_lichess_classical = models.IntegerField(null=True, blank=True, verbose_name="Rating Lichess Classical")
    
    possui_chesscom = models.BooleanField(default=False, verbose_name="Possui conta Chess.com")
    rating_chesscom_rapid = models.IntegerField(null=True, blank=True, verbose_name="Rating Chess.com Rapid")
    rating_chesscom_blitz = models.IntegerField(null=True, blank=True, verbose_name="Rating Chess.com Blitz")
    rating_chesscom_bullet = models.IntegerField(null=True, blank=True, verbose_name="Rating Chess.com Bullet")
    
    ja_participou_torneios = models.BooleanField(
        default=False,
        verbose_name="Já Participou de Torneios"
    )
    
    # Dados da associação
    tipo_assinatura = models.ForeignKey(
        TipoAssinatura, 
        on_delete=models.PROTECT,
        verbose_name="Tipo de Assinatura"
    )
    data_associacao = models.DateField(
        default=timezone.now,
        verbose_name="Data de Associação"
    )
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    
    # Status
    status_choices = [
        ('ativo', 'Ativo'),
        ('inadimplente', 'Inadimplente'),
        ('suspenso', 'Suspenso'),
        ('inativo', 'Inativo'),
    ]
    status = models.CharField(
        max_length=15, 
        choices=status_choices, 
        default='ativo',
        verbose_name="Status"
    )
    
    # Dados do responsável (para menores de idade)
    nome_responsavel = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nome do Responsável"
    )
    grau_parentesco_choices = [
        ('pai', 'Pai'),
        ('mae', 'Mãe'),
        ('avo', 'Avô/Avó'),
        ('tio', 'Tio/Tia'),
        ('irmao', 'Irmão/Irmã'),
        ('tutor', 'Tutor Legal'),
        ('outro', 'Outro'),
    ]
    grau_parentesco = models.CharField(
        max_length=20,
        choices=grau_parentesco_choices,
        blank=True,
        verbose_name="Grau de Parentesco"
    )
    cpf_responsavel = models.CharField(
        max_length=14,
        validators=[cpf_validator],
        blank=True,
        verbose_name="CPF do Responsável"
    )
    telefone_responsavel = models.CharField(
        max_length=20,
        validators=[telefone_validator],
        blank=True,
        verbose_name="Telefone do Responsável"
    )
    email_responsavel = models.EmailField(
        blank=True,
        verbose_name="E-mail do Responsável"
    )
    
    # Dados adicionais
    profissao = models.CharField(max_length=100, blank=True, verbose_name="Profissão")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    foto = models.ImageField(
        upload_to='socios/fotos/',
        blank=True,
        verbose_name="Foto"
    )
    
    # Preferências
    aceita_emails = models.BooleanField(
        default=True, 
        verbose_name="Aceita E-mails Promocionais"
    )
    aceita_whatsapp = models.BooleanField(
        default=True, 
        verbose_name="Aceita Mensagens no WhatsApp"
    )
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='socios_criados',
        verbose_name="Criado por"
    )

    class Meta:
        verbose_name = "Sócio"
        verbose_name_plural = "Sócios"
        ordering = ['numero_socio']

    def __str__(self):
        return f"{self.numero_socio} - {self.nome_completo}"

    def save(self, *args, **kwargs):
        # Gera número do sócio automaticamente se não foi fornecido
        if not self.numero_socio:
            ultimo_numero = Socio.objects.aggregate(
                models.Max('numero_socio')
            )['numero_socio__max']
            if ultimo_numero:
                try:
                    proximo_numero = int(ultimo_numero) + 1
                    self.numero_socio = str(proximo_numero).zfill(6)
                except ValueError:
                    # Se não conseguir converter, gera um UUID curto
                    self.numero_socio = str(uuid.uuid4())[:8].upper()
            else:
                self.numero_socio = "000001"
        
        # Define status padrão se não foi definido
        if not self.status:
            self.status = 'ativo'
            
        # Define valores padrão para campos obrigatórios mas vazios
        if not self.cep:
            self.cep = ''
        if not self.endereco:
            self.endereco = ''
        if not self.numero:
            self.numero = ''
        if not self.bairro:
            self.bairro = ''
        if not self.cidade:
            self.cidade = ''
        if not self.estado:
            self.estado = ''
        
        super().save(*args, **kwargs)

    @property
    def nome_exibicao(self):
        """Nome para exibição (prioriza nome social)"""
        return self.nome_social if self.nome_social else self.nome_completo

    @property
    def idade(self):
        """Calcula a idade do sócio"""
        hoje = timezone.now().date()
        return hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )

    @property
    def dias_para_vencimento(self):
        """Dias restantes até o vencimento"""
        hoje = timezone.now().date()
        return (self.data_vencimento - hoje).days

    @property
    def situacao_pagamento(self):
        """Status da situação de pagamento"""
        dias = self.dias_para_vencimento
        if dias < 0:
            return 'vencido'
        elif dias <= 7:
            return 'vence_em_breve'
        else:
            return 'em_dia'

    @property
    def endereco_completo(self):
        """Endereço formatado completo"""
        endereco = f"{self.endereco}, {self.numero}"
        if self.complemento:
            endereco += f", {self.complemento}"
        endereco += f" - {self.bairro}, {self.cidade}/{self.estado}"
        return endereco


class DocumentoSocio(models.Model):
    """Documentos anexados aos sócios"""
    
    socio = models.ForeignKey(
        Socio, 
        on_delete=models.CASCADE, 
        related_name='documentos',
        verbose_name="Sócio"
    )
    
    tipo_choices = [
        ('identidade', 'RG/Identidade'),
        ('cpf', 'CPF'),
        ('comprovante_residencia', 'Comprovante de Residência'),
        ('certidao_nascimento', 'Certidão de Nascimento'),
        ('foto_3x4', 'Foto 3x4'),
        ('atestado_medico', 'Atestado Médico'),
        ('outro', 'Outro'),
    ]
    tipo = models.CharField(
        max_length=30, 
        choices=tipo_choices,
        verbose_name="Tipo de Documento"
    )
    
    nome = models.CharField(
        max_length=200, 
        verbose_name="Nome do Documento"
    )
    arquivo = models.FileField(
        upload_to='socios/documentos/',
        verbose_name="Arquivo"
    )
    observacoes = models.TextField(
        blank=True, 
        verbose_name="Observações"
    )
    
    # Controle
    data_upload = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Data do Upload"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Enviado por"
    )

    class Meta:
        verbose_name = "Documento do Sócio"
        verbose_name_plural = "Documentos dos Sócios"
        ordering = ['-data_upload']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.socio.nome_completo}"


class HistoricoPagamento(models.Model):
    """Histórico de pagamentos dos sócios"""
    
    socio = models.ForeignKey(
        Socio, 
        on_delete=models.CASCADE, 
        related_name='pagamentos',
        verbose_name="Sócio"
    )
    
    # Dados do pagamento
    data_pagamento = models.DateField(verbose_name="Data do Pagamento")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    valor = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Valor Pago"
    )
    
    # Referência
    mes_referencia = models.DateField(
        verbose_name="Mês de Referência",
        help_text="Mês ao qual o pagamento se refere"
    )
    
    # Forma de pagamento
    forma_pagamento_choices = [
        ('dinheiro', 'Dinheiro'),
        ('cartao_debito', 'Cartão de Débito'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('pix', 'PIX'),
        ('transferencia', 'Transferência Bancária'),
        ('boleto', 'Boleto'),
        ('outro', 'Outro'),
    ]
    forma_pagamento = models.CharField(
        max_length=20, 
        choices=forma_pagamento_choices,
        verbose_name="Forma de Pagamento"
    )
    
    # Status
    status_choices = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
        ('estornado', 'Estornado'),
    ]
    status = models.CharField(
        max_length=15, 
        choices=status_choices, 
        default='confirmado',
        verbose_name="Status"
    )
    
    # Dados adicionais
    descricao = models.TextField(
        blank=True, 
        verbose_name="Descrição/Observações"
    )
    comprovante = models.FileField(
        upload_to='socios/comprovantes/',
        blank=True,
        verbose_name="Comprovante"
    )
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Registrado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Registrado por"
    )

    class Meta:
        verbose_name = "Histórico de Pagamento"
        verbose_name_plural = "Histórico de Pagamentos"
        ordering = ['-data_pagamento']

    def __str__(self):
        return f"{self.socio.nome_completo} - {self.mes_referencia.strftime('%m/%Y')}"

    @property
    def em_atraso(self):
        """Verifica se o pagamento está em atraso"""
        hoje = timezone.now().date()
        return self.data_vencimento < hoje and self.status == 'pendente'
