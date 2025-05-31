import json
import tempfile
from datetime import date, timedelta
from unittest.mock import patch, Mock, MagicMock
from io import BytesIO
from PIL import Image

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User

User = get_user_model()


class BaseAuthenticationTestCase(APITestCase):
    """Clasa de bază pentru toate testele de autentificare"""
    
    def setUp(self):
        """Configurează datele de test comune"""
        self.client = APIClient()
        
        # Mock pentru funcțiile de securitate din backend
        self.security_patcher = patch('users.views.create_security_event')
        self.mock_security_event = self.security_patcher.start()
        
        self.gdpr_patcher = patch('users.views.log_gdpr_event')
        self.mock_gdpr_event = self.gdpr_patcher.start()
        
        self.captcha_patcher = patch('users.views.log_captcha_attempt')
        self.mock_captcha_attempt = self.captcha_patcher.start()
        
        self.twofa_patcher = patch('users.views.log_2fa_event')
        self.mock_2fa_event = self.twofa_patcher.start()
        
        # Utilizator standard cu email și parolă
        self.user_email = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            is_active=True
        )
        
        # Utilizator cu buletin
        self.user_id_card = User.objects.create(
            cnp='1234567890123',
            first_name='Jane',
            last_name='Smith',
            series='AB',
            number='123456',
            place_of_birth='București',
            address='Str. Test nr. 1',
            issuing_authority='SPCEP Sector 1',
            sex='F',
            date_of_issue=date.today() - timedelta(days=365),
            date_of_expiry=date.today() + timedelta(days=365),
            is_verified_by_id=True,
            is_active=True
        )
        
        # Utilizator inactiv pentru teste
        self.user_inactive = User.objects.create_user(
            email='inactive@example.com',
            password='TestPass123!',
            first_name='Inactive',
            last_name='User',
            is_active=False
        )
    
    def tearDown(self):
        """Curăță mock-urile după fiecare test"""
        self.security_patcher.stop()
        self.gdpr_patcher.stop()
        self.captcha_patcher.stop()
        self.twofa_patcher.stop()
    
    def _create_mock_image(self):
        """Creează o imagine mock pentru teste"""
        image = Image.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        image.save(img_io, 'JPEG')
        img_io.seek(0)
        return SimpleUploadedFile("test_image.jpg", img_io.read(), content_type="image/jpeg")


class TestEmailPasswordAuthentication(BaseAuthenticationTestCase):
    """Teste pentru autentificare cu email și parolă"""
    
    @patch('users.views.AccountSettings.objects.get')
    def test_successful_login_without_2fa(self, mock_account_settings):
        """Test autentificare reușită cu email și parolă fără 2FA"""
        # Mock pentru setările de cont - fără 2FA
        mock_settings = Mock()
        mock_settings.two_factor_enabled = False
        mock_settings.two_factor_verified = False
        mock_account_settings.return_value = mock_settings
        
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
    
    @patch('users.views.AccountSettings.objects.get')
    def test_successful_login_with_2fa_required(self, mock_account_settings):
        """Test autentificare cu 2FA necesar"""
        # Mock pentru setările de cont - cu 2FA activat
        mock_settings = Mock()
        mock_settings.two_factor_enabled = True
        mock_settings.two_factor_verified = True
        mock_account_settings.return_value = mock_settings
        
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['requires_2fa'])
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertIn('message', response.data)
        # Nu ar trebui să avem token-uri când se necesită 2FA
        self.assertNotIn('access', response.data)
    
    def test_login_with_wrong_password(self):
        """Test autentificare cu parolă greșită"""
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertIn('eșuată', response.data['detail'].lower())
    
    def test_login_with_nonexistent_email(self):
        """Test autentificare cu email inexistent"""
        url = reverse('login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
    
    @patch('users.views.SocialAccount.objects.filter')
    def test_login_with_social_account_user(self, mock_social_filter):
        """Test autentificare clasică pe cont social"""
        mock_social_filter.return_value.exists.return_value = True
        
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('social', response.data['detail'].lower())
    
    def test_login_missing_email(self):
        """Test autentificare fără email"""
        url = reverse('login')
        data = {
            'password': 'TestPass123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        # Backend-ul nu specifică validări explicite pentru câmpuri lipsă în view
        # dar este probabil să returneze o eroare
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])
    
    def test_login_missing_password(self):
        """Test autentificare fără parolă"""
        url = reverse('login')
        data = {
            'email': 'test@example.com'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])


class TestIDCardAuthentication(BaseAuthenticationTestCase):
    """Teste pentru autentificare cu buletinul"""
    
    @patch('users.views.AccountSettings.objects.get')
    def test_successful_id_card_login_manual_without_2fa(self, mock_account_settings):
        """Test autentificare reușită cu buletin - verificare manuală fără 2FA"""
        # Mock pentru setările de cont - fără 2FA
        mock_settings = Mock()
        mock_settings.two_factor_enabled = False
        mock_settings.two_factor_verified = False
        mock_account_settings.return_value = mock_settings
        
        url = reverse('login-id-card')
        data = {
            'cnp': '1234567890123',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'id_series': 'AB'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['cnp'], '1234567890123')
        self.assertIn('message', response.data)

class TestEmailVerification(BaseAuthenticationTestCase):
    """Teste pentru verificarea email-ului"""
    
    def test_successful_email_verification(self):
        """Test verificare email reușită"""
        # Setează un cod de verificare
        self.user_inactive.verification_code = '123456'
        self.user_inactive.save()
        
        url = reverse('verify-email')
        data = {
            'email': 'inactive@example.com',
            'verification_code': '123456'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('verificat', response.data['message'].lower())
        
        # Verifică că utilizatorul a fost activat
        self.user_inactive.refresh_from_db()
        self.assertTrue(self.user_inactive.is_active)
        self.assertIsNone(self.user_inactive.verification_code)
    
    def test_email_verification_wrong_code(self):
        """Test verificare email cu cod greșit"""
        self.user_inactive.verification_code = '123456'
        self.user_inactive.save()
        
        url = reverse('verify-email')
        data = {
            'email': 'inactive@example.com',
            'verification_code': '654321'  # Cod greșit
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('incorect', response.data['error'].lower())
    
    def test_email_verification_missing_data(self):
        """Test verificare email cu date lipsă"""
        url = reverse('verify-email')
        data = {
            'email': 'inactive@example.com'
            # Lipsește verification_code
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('obligatorii', response.data['error'].lower())


class TestPasswordReset(BaseAuthenticationTestCase):
    """Teste pentru resetarea parolei"""
    
    @patch('django.core.mail.EmailMessage.send')
    @patch('users.views.SocialAccount.objects.filter')
    def test_request_password_reset_success(self, mock_social_filter, mock_send):
        """Test cerere resetare parolă reușită"""
        mock_social_filter.return_value.exists.return_value = False  # Nu e cont social
        mock_send.return_value = True
        
        url = reverse('request-password-reset')
        data = {
            'email': 'test@example.com'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('trimis', response.data['message'].lower())
        
        # Verifică că utilizatorul are un cod de verificare
        self.user_email.refresh_from_db()
        self.assertIsNotNone(self.user_email.verification_code)
    
    @patch('users.views.SocialAccount.objects.filter')
    def test_request_password_reset_social_account(self, mock_social_filter):
        """Test cerere resetare parolă pentru cont social"""
        mock_social_filter.return_value.exists.return_value = True  # Este cont social
        
        url = reverse('request-password-reset')
        data = {
            'email': 'test@example.com'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('social', response.data['error'].lower())
    
    def test_verify_reset_code_success(self):
        """Test verificare cod resetare reușită"""
        self.user_email.verification_code = '123456'
        self.user_email.save()
        
        url = reverse('verify-reset-code')
        data = {
            'email': 'test@example.com',
            'verification_code': '123456'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    

    def test_reset_password_weak_password(self):
        """Test resetare parolă cu parolă slabă"""
        self.user_email.verification_code = '123456'
        self.user_email.save()
        
        url = reverse('reset-password')
        data = {
            'email': 'test@example.com',
            'verification_code': '123456',
            'new_password': '123'  # Parolă prea scurtă
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIsInstance(response.data['error'], list)
        self.assertTrue(len(response.data['error']) > 0)
    
    def test_reset_password_with_personal_info(self):
        """Test resetare parolă care conține informații personale"""
        self.user_email.verification_code = '123456'
        self.user_email.save()
        
        url = reverse('reset-password')
        data = {
            'email': 'test@example.com',
            'verification_code': '123456',
            'new_password': 'JohnPassword123!'  # Conține prenumele
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

class TestTwoFactorAuthentication(BaseAuthenticationTestCase):
    """Teste pentru autentificarea cu doi factori"""
    
    @patch('pyotp.TOTP')
    @patch('users.views.AccountSettings.objects.get')
    def test_successful_2fa_verification(self, mock_account_settings, mock_totp_class):
        """Test verificare 2FA reușită"""
        # Mock pentru setările de cont
        mock_settings = Mock()
        mock_settings.two_factor_enabled = True
        mock_settings.two_factor_verified = True
        mock_settings.two_factor_secret = 'test_secret'
        mock_account_settings.return_value = mock_settings
        
        # Mock pentru TOTP
        mock_totp = Mock()
        mock_totp.verify.return_value = True
        mock_totp_class.return_value = mock_totp
        
        url = reverse('verify-two-factor')
        data = {
            'email': 'test@example.com',
            'code': '123456'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    @patch('pyotp.TOTP')
    @patch('users.views.AccountSettings.objects.get')
    def test_failed_2fa_verification(self, mock_account_settings, mock_totp_class):
        """Test verificare 2FA eșuată"""
        # Mock pentru setările de cont
        mock_settings = Mock()
        mock_settings.two_factor_enabled = True
        mock_settings.two_factor_verified = True
        mock_settings.two_factor_secret = 'test_secret'
        mock_account_settings.return_value = mock_settings
        
        # Mock pentru TOTP - cod invalid
        mock_totp = Mock()
        mock_totp.verify.return_value = False
        mock_totp.now.return_value = '654321'  # Pentru debugging
        mock_totp_class.return_value = mock_totp
        
        url = reverse('verify-two-factor')
        data = {
            'email': 'test@example.com',
            'code': '123456'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('invalid', response.data['error'].lower())
    
    def test_2fa_verification_missing_code(self):
        """Test verificare 2FA fără cod"""
        url = reverse('verify-two-factor')
        data = {
            'email': 'test@example.com'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class TestLogout(BaseAuthenticationTestCase):
    """Teste pentru deconectare"""
    
    def test_successful_logout(self):
        """Test deconectare reușită"""
        # Autentifică utilizatorul
        refresh = RefreshToken.for_user(self.user_email)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('logout')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('reușită', response.data['message'].lower())

class TestUserAccountStatus(BaseAuthenticationTestCase):
    """Teste pentru statusul conturilor de utilizator"""
    
    @patch('users.views.AccountSettings.objects.get')
    def test_login_unverified_id_card_user(self, mock_account_settings):
        """Test autentificare cu buletin pentru utilizator neverificat"""
        # Mock pentru setările de cont
        mock_settings = Mock()
        mock_settings.two_factor_enabled = False
        mock_account_settings.return_value = mock_settings
        
        # Creează utilizator cu buletin neverificat
        unverified_user = User.objects.create(
            cnp='1111111111111',
            first_name='Test',
            last_name='User',
            series='XY',
            number='111111',
            is_verified_by_id=False,  # Neverificat prin buletin
            is_active=True
        )
        
        url = reverse('login-id-card')
        data = {
            'cnp': '1111111111111',
            'first_name': 'Test',
            'last_name': 'User',
            'id_series': 'XY'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
        self.assertIn('verificat', response.data['detail'].lower())
    
    def test_user_activation_after_verification(self):
        """Test activarea utilizatorului după verificarea email-ului"""
        # Utilizatorul inactiv cu cod de verificare
        self.user_inactive.verification_code = '123456'
        self.user_inactive.save()
        
        # Verifică email
        url = reverse('verify-email')
        data = {
            'email': 'inactive@example.com',
            'verification_code': '123456'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verifică că utilizatorul poate să se autentifice acum
        with patch('users.views.AccountSettings.objects.get') as mock_settings:
            mock_settings_obj = Mock()
            mock_settings_obj.two_factor_enabled = False
            mock_settings.return_value = mock_settings_obj
            
            login_url = reverse('login')
            login_data = {
                'email': 'inactive@example.com',
                'password': 'TestPass123!'
            }
            
            login_response = self.client.post(login_url, login_data, format='json')
            self.assertEqual(login_response.status_code, status.HTTP_200_OK)
            self.assertIn('access', login_response.data)


class TestRegistrationViews(BaseAuthenticationTestCase):
    """Teste pentru înregistrare"""
    
    @patch('django.core.mail.EmailMessage.send')
    @patch('users.views.SocialAccount.objects.filter')
    def test_successful_email_registration(self, mock_social_filter, mock_send):
        """Test înregistrare cu email reușită"""
        mock_social_filter.return_value.exists.return_value = False
        mock_send.return_value = True
        
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'password': 'NewPassword123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        
        # Verifică că utilizatorul a fost creat
        user = User.objects.get(email='newuser@example.com')
        self.assertFalse(user.is_active)  # Inactiv până la verificare
        self.assertIsNotNone(user.verification_code)

if __name__ == '_main_':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    # Configurează Django pentru rularea testelor
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'users',
                'rest_framework',
                'rest_framework_simplejwt',
            ],
            SECRET_KEY='test-secret-key',
            REST_FRAMEWORK={
                'DEFAULT_AUTHENTICATION_CLASSES': [
                    'rest_framework_simplejwt.authentication.JWTAuthentication',
                ],
            }
        )
    
    django.setup()
    
    # Rulează testele
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['_main_'])