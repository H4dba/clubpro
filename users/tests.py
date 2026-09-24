from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username='jogador',
			email='jogador@example.com',
			password='Senha antiga 123',
		)

	def test_password_reset_sends_email_for_registered_address(self):
		response = self.client.post(
			reverse('password_reset'),
			{'email': self.user.email},
		)

		self.assertRedirects(response, reverse('password_reset_done'))
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn('Redefinição de senha', mail.outbox[0].subject)
		self.assertIn('redefinir a senha', mail.outbox[0].body)

	def test_password_reset_does_not_reveal_unknown_address(self):
		response = self.client.post(
			reverse('password_reset'),
			{'email': 'nao-cadastrado@example.com'},
		)

		self.assertRedirects(response, reverse('password_reset_done'))
		self.assertEqual(len(mail.outbox), 0)

	def test_password_reset_changes_password_with_email_link(self):
		self.client.post(reverse('password_reset'), {'email': self.user.email})
		reset_url = mail.outbox[0].body.splitlines()[5]

		response = self.client.get(reset_url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Crie uma nova senha')

		response = self.client.post(
			reset_url,
			{'new_password1': 'Senha nova 456', 'new_password2': 'Senha nova 456'},
		)

		self.assertRedirects(response, reverse('password_reset_complete'))
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('Senha nova 456'))
