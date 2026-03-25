from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db import transaction

from .models import ChessComProfile, TiposPlano, UsuarioCustom


class CustomUserAdminForm(forms.ModelForm):
    class Meta:
        model = UsuarioCustom
        fields = "__all__"

    def clean_chesscom_username(self):
        username = (self.cleaned_data.get("chesscom_username") or "").strip()
        if not username:
            return ""

        conflict = ChessComProfile.objects.filter(chesscom_username__iexact=username).exclude(user=self.instance).exists()
        if conflict:
            raise forms.ValidationError("Esse usuário do Chess.com já está vinculado a outro usuário.")
        return username

class CustomUserAdmin(UserAdmin):
    form = CustomUserAdminForm
    fieldsets = UserAdmin.fieldsets + (
        ("Dados pessoais", {"fields": ("data_nascimento", "telefone")}),
        ("Plano", {"fields": ("tipo_plano",)}),
        ("Chess.com", {"fields": ("chesscom_username", "is_chesscom_connected")}),
    )
    list_display = ("username", "email", "chesscom_username", "is_chesscom_connected", "tipo_plano", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name", "chesscom_username")

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        obj.chesscom_username = (obj.chesscom_username or "").strip() or None
        if not obj.chesscom_username:
            obj.is_chesscom_connected = False

        super().save_model(request, obj, form, change)

        if obj.chesscom_username:
            profile, _ = ChessComProfile.objects.get_or_create(
                user=obj,
                defaults={"chesscom_username": obj.chesscom_username},
            )
            if profile.chesscom_username != obj.chesscom_username:
                profile.chesscom_username = obj.chesscom_username
                profile.save(update_fields=["chesscom_username"])
            if not obj.is_chesscom_connected:
                messages.warning(
                    request,
                    "Usuário Chess.com definido, mas marcado como desconectado. Ajuste se desejar.",
                )
        else:
            ChessComProfile.objects.filter(user=obj).delete()


@admin.register(ChessComProfile)
class ChessComProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "chesscom_username",
        "rapid_rating",
        "blitz_rating",
        "bullet_rating",
        "updated_at",
    )
    search_fields = ("user__username", "user__email", "chesscom_username")
    readonly_fields = ("updated_at", "created_at_local")


admin.site.register(UsuarioCustom, CustomUserAdmin)
admin.site.register(TiposPlano)

