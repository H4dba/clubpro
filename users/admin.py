from django.contrib import admin
from .models import UsuarioCustom, TiposPlano
from django.contrib.auth.admin import UserAdmin
# Register your models here.

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Plano", {"fields": ("tipo_plano",)}),
    )
    list_display = ("username", "email", "tipo_plano", "is_staff")
    

admin.site.register(UsuarioCustom, CustomUserAdmin)
admin.site.register(TiposPlano)

