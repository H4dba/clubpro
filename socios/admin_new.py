from django.contrib import admin
from django.utils.html import format_html
from .models import TipoAssinatura, Socio, DocumentoSocio, HistoricoPagamento


@admin.register(TipoAssinatura)
class TipoAssinaturaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'valor_formatado', 'ativo', 'cor_preview']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']
    list_editable = ['ativo']
    ordering = ['nome']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'valor_mensal', 'valor_anual', 'duracao_dias')
        }),
        ('Benefícios', {
            'fields': ('acesso_torneios', 'desconto_eventos', 'aulas_incluidas'),
            'classes': ('collapse',)
        }),
        ('Configurações', {
            'fields': ('cor', 'ativo'),
            'classes': ('collapse',)
        })
    )
    
    def valor_formatado(self, obj):
        return f"R$ {obj.valor_mensal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    valor_formatado.short_description = 'Valor Mensal'
    valor_formatado.admin_order_field = 'valor_mensal'
    
    def cor_preview(self, obj):
        if obj.cor:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border-radius: 3px; border: 1px solid #ccc;"></div>',
                obj.cor
            )
        return '-'
    cor_preview.short_description = 'Cor'


class DocumentoSocioInline(admin.TabularInline):
    model = DocumentoSocio
    extra = 0
    fields = ['nome', 'tipo', 'arquivo', 'data_upload']
    readonly_fields = ['data_upload']


class HistoricoPagamentoInline(admin.TabularInline):
    model = HistoricoPagamento
    extra = 0
    fields = ['data_pagamento', 'valor', 'mes_referencia', 'status', 'observacoes']
    ordering = ['-data_pagamento']


@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = [
        'numero_socio', 'nome_exibicao', 'email', 'telefone', 
        'tipo_assinatura', 'status_badge', 'data_vencimento', 'dias_vencimento'
    ]
    list_filter = [
        'status', 'tipo_assinatura', 'genero', 'categoria_cbx',
        'data_associacao', 'data_vencimento'
    ]
    search_fields = [
        'nome', 'nome_preferencia', 'cpf', 'email', 
        'telefone', 'numero_socio'
    ]
    ordering = ['numero_socio']
    date_hierarchy = 'data_associacao'
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_socio', 'foto_preview', 'foto')
        }),
        ('Dados Pessoais', {
            'fields': (
                ('nome', 'nome_preferencia'),
                ('cpf', 'data_nascimento', 'genero'),
            )
        }),
        ('Contato', {
            'fields': (
                ('email', 'telefone'),
                'endereco'
            )
        }),
        ('Xadrez', {
            'fields': (
                ('rating_fide', 'rating_nacional', 'categoria_cbx'),
            ),
            'classes': ('collapse',)
        }),
        ('Associação', {
            'fields': (
                'tipo_assinatura',
                ('data_associacao', 'data_vencimento'),
                'status'
            )
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['foto_preview', 'dias_vencimento']
    inlines = [DocumentoSocioInline, HistoricoPagamentoInline]
    
    actions = ['marcar_como_ativo', 'marcar_como_inadimplente', 'exportar_csv']
    
    def foto_preview(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 50%;" />',
                obj.foto.url
            )
        return 'Sem foto'
    foto_preview.short_description = 'Preview da Foto'
    
    def status_badge(self, obj):
        colors = {
            'ativo': '#28a745',
            'inadimplente': '#dc3545',
            'suspenso': '#ffc107',
            'inativo': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def dias_vencimento(self, obj):
        from datetime import date
        if obj.data_vencimento:
            dias = (obj.data_vencimento - date.today()).days
            if dias < 0:
                return format_html(
                    '<span style="color: #dc3545; font-weight: bold;">{} dias em atraso</span>',
                    abs(dias)
                )
            elif dias == 0:
                return format_html('<span style="color: #ffc107; font-weight: bold;">Vence hoje</span>')
            elif dias <= 7:
                return format_html(
                    '<span style="color: #ffc107; font-weight: bold;">{} dias</span>',
                    dias
                )
            else:
                return format_html('<span style="color: #28a745;">{} dias</span>', dias)
        return '-'
    dias_vencimento.short_description = 'Vencimento'
    
    def marcar_como_ativo(self, request, queryset):
        updated = queryset.update(status='ativo')
        self.message_user(request, f'{updated} sócio(s) marcado(s) como ativo(s).')
    marcar_como_ativo.short_description = 'Marcar selecionados como ativos'
    
    def marcar_como_inadimplente(self, request, queryset):
        updated = queryset.update(status='inadimplente')
        self.message_user(request, f'{updated} sócio(s) marcado(s) como inadimplente(s).')
    marcar_como_inadimplente.short_description = 'Marcar selecionados como inadimplentes'
    
    def exportar_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="socios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Número', 'Nome', 'CPF', 'Email', 'Telefone', 
            'Status', 'Plano', 'Associação', 'Vencimento'
        ])
        
        for socio in queryset:
            writer.writerow([
                socio.numero_socio,
                socio.nome,
                socio.cpf,
                socio.email or '',
                socio.telefone or '',
                socio.get_status_display(),
                socio.tipo_assinatura.nome,
                socio.data_associacao.strftime('%d/%m/%Y'),
                socio.data_vencimento.strftime('%d/%m/%Y') if socio.data_vencimento else ''
            ])
        
        return response
    exportar_csv.short_description = 'Exportar selecionados para CSV'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tipo_assinatura')


@admin.register(DocumentoSocio)
class DocumentoSocioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'socio', 'tipo', 'data_upload', 'arquivo_link']
    list_filter = ['tipo', 'data_upload']
    search_fields = ['nome', 'socio__nome', 'socio__numero_socio']
    ordering = ['-data_upload']
    date_hierarchy = 'data_upload'
    
    def arquivo_link(self, obj):
        if obj.arquivo:
            return format_html(
                '<a href="{}" target="_blank">📄 Visualizar</a>',
                obj.arquivo.url
            )
        return '-'
    arquivo_link.short_description = 'Arquivo'


@admin.register(HistoricoPagamento)
class HistoricoPagamentoAdmin(admin.ModelAdmin):
    list_display = [
        'socio', 'valor_formatado', 'data_pagamento', 
        'mes_referencia', 'status_badge', 'observacoes_resumo'
    ]
    list_filter = [
        'status', 'data_pagamento', 'mes_referencia'
    ]
    search_fields = [
        'socio__nome', 'socio__numero_socio', 'observacoes'
    ]
    ordering = ['-data_pagamento']
    date_hierarchy = 'data_pagamento'
    
    fieldsets = (
        ('Informações do Pagamento', {
            'fields': ('socio', 'valor', 'data_pagamento', 'mes_referencia')
        }),
        ('Status e Observações', {
            'fields': ('status', 'observacoes')
        })
    )
    
    def valor_formatado(self, obj):
        return f"R$ {obj.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    valor_formatado.short_description = 'Valor'
    valor_formatado.admin_order_field = 'valor'
    
    def status_badge(self, obj):
        colors = {
            'pendente': '#ffc107',
            'pago': '#28a745',
            'atrasado': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def observacoes_resumo(self, obj):
        if obj.observacoes:
            return obj.observacoes[:50] + '...' if len(obj.observacoes) > 50 else obj.observacoes
        return '-'
    observacoes_resumo.short_description = 'Observações'


# Configurações personalizadas do admin
admin.site.site_header = 'ClubPro - Administração'
admin.site.site_title = 'ClubPro Admin'
admin.site.index_title = 'Painel de Administração do Clube'