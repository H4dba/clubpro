from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from users.models import PasswordResetOTP


class PasswordResetOTPTests(TestCase):
    def setUp(self):
        self.UserModel = get_user_model()
        self.user = self.UserModel.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="oldpassword123",
            first_name="Test"
        )
        self.request_url = reverse("password_reset_request")
        self.verify_url = reverse("password_reset_verify")

    def test_otp_model_expiration(self):
        """Testa se o OTP expira e invalida corretamente após o tempo limite."""
        otp = PasswordResetOTP.objects.create(
            user=self.user,
            code="123456"
        )
        self.assertTrue(otp.is_valid())

        # Forçar expiração do OTP
        otp.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        otp.save()
        self.assertFalse(otp.is_valid())

    def test_otp_model_used(self):
        """Testa se o OTP fica inválido após ser marcado como usado."""
        otp = PasswordResetOTP.objects.create(
            user=self.user,
            code="123456"
        )
        self.assertTrue(otp.is_valid())

        otp.is_used = True
        otp.save()
        self.assertFalse(otp.is_valid())

    def test_request_otp_generates_and_sends_email(self):
        """Testa se solicitar redefinição gera OTP no BD e envia e-mail com o código."""
        response = self.client.post(self.request_url, {"email": "testuser@example.com"})
        
        # Deve redirecionar para a tela de verificação
        self.assertRedirects(response, self.verify_url)

        # Deve ter gerado um registro de OTP no banco
        self.assertEqual(PasswordResetOTP.objects.filter(user=self.user).count(), 1)
        otp = PasswordResetOTP.objects.get(user=self.user)
        self.assertEqual(len(otp.code), 6)

        # Deve ter enviado um e-mail com o OTP
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.to, ["testuser@example.com"])
        self.assertIn(otp.code, sent_mail.body)

    def test_verify_otp_and_reset_password(self):
        """Testa a verificação bem sucedida de OTP e redefinição de senha."""
        otp = PasswordResetOTP.objects.create(
            user=self.user,
            code="654321"
        )
        # Prefill session to mimic flow
        session = self.client.session
        session["reset_email"] = self.user.email
        session.save()

        response = self.client.post(self.verify_url, {
            "email": self.user.email,
            "code": "654321",
            "password": "newpassword123",
            "password_confirm": "newpassword123"
        })

        # Deve redirecionar para o login após sucesso
        self.assertRedirects(response, reverse("login"))

        # OTP deve ter sido marcado como usado
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

        # Nova senha deve funcionar no login
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

    def test_verify_otp_fails_with_invalid_code(self):
        """Testa falha na verificação ao digitar um código OTP incorreto."""
        PasswordResetOTP.objects.create(
            user=self.user,
            code="111111"
        )

        response = self.client.post(self.verify_url, {
            "email": self.user.email,
            "code": "222222",  # código errado
            "password": "newpassword123",
            "password_confirm": "newpassword123"
        })

        # Deve retornar 200 (reexibir o form com erro)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Código de verificação inválido ou expirado.")

        # A senha não deve ter sido alterada
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("newpassword123"))

