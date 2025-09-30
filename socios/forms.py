from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import datetime
from .models import Socio, TipoAssinatura, DocumentoSocio, HistoricoPagamento


class BrazilianDateField(forms.DateField):
    """Campo de data que aceita formato brasileiro dd/mm/yyyy"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_formats = ['%d/%m/%Y', '%Y-%m-%d']  # Aceita tanto BR quanto ISO
    
    def to_python(self, value):
        """Converte string para objeto date"""
        if not value:
            return None
            
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
                
            # Tentar formato brasileiro primeiro
            for fmt in ['%d/%m/%Y', '%Y-%m-%d']:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            
            # Se não conseguiu converter com nenhum formato
            raise ValidationError('Digite uma data válida no formato dd/mm/aaaa.')
        
        return super().to_python(value)


class SocioForm(forms.ModelForm):
    """Formulário para cadastro e edição de sócios"""
    
    # Campos de data com formato brasileiro
    data_nascimento = BrazilianDateField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'dd/mm/aaaa',
            'data-mask': '00/00/0000'
        })
    )
    
    data_associacao = BrazilianDateField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'dd/mm/aaaa',
            'data-mask': '00/00/0000'
        })
    )
    
    data_vencimento = BrazilianDateField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'dd/mm/aaaa',
            'data-mask': '00/00/0000'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tornar campos de endereço opcionais no formulário
        self.fields['cep'].required = False
        self.fields['endereco'].required = False
        self.fields['numero'].required = False
        self.fields['bairro'].required = False
        self.fields['cidade'].required = False
        self.fields['estado'].required = False
        
        # Status é obrigatório apenas na edição, não no cadastro
        self.fields['status'].required = False
        
        # Outros campos opcionais
        self.fields['rg'].required = False
        self.fields['genero'].required = False
        self.fields['telefone'].required = False
        self.fields['rating_fide'].required = False
        self.fields['rating_cbx'].required = False
        self.fields['categoria_cbx'].required = False
        self.fields['profissao'].required = False
        self.fields['aceita_emails'].required = False
        self.fields['aceita_whatsapp'].required = False
    
    class Meta:
        model = Socio
        fields = [
            'numero_socio', 'nome_completo', 'nome_social', 'cpf', 'rg',
            'data_nascimento', 'genero', 'telefone', 'celular', 'email',
            'cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado',
            'rating_fide', 'rating_cbx', 'categoria_cbx',
            'tipo_assinatura', 'data_associacao', 'data_vencimento', 'status',
            'profissao', 'observacoes', 'foto',
            'aceita_emails', 'aceita_whatsapp'
        ]
        widgets = {
            'nome_completo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo do sócio'
            }),
            'nome_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome social (opcional)'
            }),
            'numero_socio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Deixe em branco para gerar automaticamente'
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XXX.XXX.XXX-XX',
                'data-mask': '000.000.000-00'
            }),
            'rg': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RG do sócio'
            }),
            'data_nascimento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa',
                'data-mask': '00/00/0000'
            }),
            'genero': forms.Select(attrs={
                'class': 'form-select'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(XX) XXXXX-XXXX',
                'data-mask': '(00) 00000-0000'
            }),
            'celular': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(XX) XXXXX-XXXX',
                'data-mask': '(00) 00000-0000'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XXXXX-XXX',
                'data-mask': '00000-000'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rua, Avenida, etc.'
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número'
            }),
            'complemento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartamento, bloco, etc. (opcional)'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bairro'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cidade'
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UF',
                'maxlength': '2'
            }),
            'rating_fide': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rating FIDE (opcional)'
            }),
            'rating_cbx': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rating CBX (opcional)'
            }),
            'categoria_cbx': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Categoria CBX (opcional)'
            }),
            'tipo_assinatura': forms.Select(attrs={
                'class': 'form-select'
            }),
            'data_associacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa',
                'data-mask': '00/00/0000'
            }),
            'data_vencimento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa',
                'data-mask': '00/00/0000'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'profissao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Profissão (opcional)'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observações sobre o sócio (opcional)'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'aceita_emails': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'aceita_whatsapp': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class TipoAssinaturaForm(forms.ModelForm):
    """Formulário para tipos de assinatura"""
    
    class Meta:
        model = TipoAssinatura
        fields = [
            'nome', 'descricao', 'valor_mensal', 'valor_anual', 'duracao_dias',
            'cor', 'acesso_torneios', 'desconto_eventos', 'aulas_incluidas', 'ativo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do plano'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do plano'
            }),
            'valor_mensal': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'valor_anual': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00 (opcional)'
            }),
            'duracao_dias': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '30'
            }),
            'cor': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'desconto_eventos': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'aulas_incluidas': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0'
            }),
            'acesso_torneios': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class DocumentoSocioForm(forms.ModelForm):
    """Formulário para upload de documentos"""
    
    class Meta:
        model = DocumentoSocio
        fields = ['tipo', 'nome', 'arquivo', 'observacoes']
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome/descrição do documento'
            }),
            'arquivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre o documento (opcional)'
            }),
        }


class HistoricoPagamentoForm(forms.ModelForm):
    """Formulário para registrar pagamentos"""
    
    # Campos de data com formato brasileiro
    data_pagamento = BrazilianDateField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'dd/mm/aaaa',
            'data-mask': '00/00/0000'
        })
    )
    
    data_vencimento = BrazilianDateField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'dd/mm/aaaa',
            'data-mask': '00/00/0000'
        })
    )
    
    class Meta:
        model = HistoricoPagamento
        fields = [
            'data_pagamento', 'data_vencimento', 'valor', 'mes_referencia',
            'forma_pagamento', 'status', 'descricao', 'comprovante'
        ]
        widgets = {
            'data_pagamento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa',
                'data-mask': '00/00/0000'
            }),
            'data_vencimento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa',
                'data-mask': '00/00/0000'
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'mes_referencia': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'placeholder': 'mm/aaaa',
                'data-mask': '00/0000'
            }),
            'forma_pagamento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre o pagamento (opcional)'
            }),
            'comprovante': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }


class FiltroSociosForm(forms.Form):
    """Formulário para filtrar sócios"""
    
    STATUS_CHOICES = [('', 'Todos os status')] + Socio.status_choices
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    tipo_assinatura = forms.ModelChoiceField(
        queryset=TipoAssinatura.objects.filter(ativo=True),
        required=False,
        empty_label="Todos os planos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nome, CPF, email...'
        })
    )