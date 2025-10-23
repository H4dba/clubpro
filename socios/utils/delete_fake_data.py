from socios.models import Socio, TipoAssinatura, HistoricoPagamento
from django.contrib.auth import get_user_model

# Delete all data (keeps admin user)
print("🗑️ Cleaning up old data...")
HistoricoPagamento.objects.all().delete()
Socio.objects.all().delete()
TipoAssinatura.objects.all().delete()



print("✅ Cleanup complete!")

# Now create fresh data
from socios.utils.fake_data import create_demo_data
create_demo_data()