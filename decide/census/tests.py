from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from .models import Census
from base import mods
from django.test import LiveServerTestCase
from base.tests import BaseTestCase
from authentication.tests import AuthTestCase
from datetime import datetime
from django.contrib import admin
from .admin import export_to_csv, export_to_pdf, get_related_object, CensusAdmin
from io import StringIO
from django.http import HttpResponse
import csv


class CensusTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.census = Census(voting_id=1, voter_id=1)
        self.census.save()

    def tearDown(self):
        super().tearDown()
        self.census = None

    def test_check_vote_permissions(self):
        response = self.client.get('/census/{}/?voter_id={}'.format(1, 2), format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), 'Invalid voter')

        response = self.client.get('/census/{}/?voter_id={}'.format(1, 1), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Valid voter')

    def test_list_voting(self):
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'voters': [1]})

    def test_add_new_voters_conflict(self):
        data = {'voting_id': 1, 'voters': [1]}
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 409)

    def test_add_new_voters(self):
        data = {'voting_id': 2, 'voters': [1,2,3,4]}
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(data.get('voters')), Census.objects.count() - 1)

    def test_destroy_voter(self):
        data = {'voters': [1]}
        response = self.client.delete('/census/{}/'.format(1), data, format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(0, Census.objects.count())


class CensusTest(StaticLiveServerTestCase):
    def setUp(self):
        #Load base test functionality for decide
        self.base = BaseTestCase()
        self.base.setUp()
        self.census = Census(voting_id=1, voter_id=1)
        self.user = User.objects.create(username='testuser')
        self.census_admin = CensusAdmin(Census,admin.site)

        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()

        self.base.tearDown()
    
    def createCensusSuccess(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/census/census/add")
        now = datetime.now()
        self.cleaner.find_element(By.ID, "id_voting_id").click()
        self.cleaner.find_element(By.ID, "id_voting_id").send_keys(now.strftime("%m%d%M%S"))
        self.cleaner.find_element(By.ID, "id_voter_id").click()
        self.cleaner.find_element(By.ID, "id_voter_id").send_keys(now.strftime("%m%d%M%S"))
        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/census/census")

    def createCensusEmptyError(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/census/census/add")

        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[3]/div/div[1]/div/form/div/p').text == 'Please correct the errors below.')
        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/census/census/add")

    def createCensusValueError(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/census/census/add")
        now = datetime.now()
        self.cleaner.find_element(By.ID, "id_voting_id").click()
        self.cleaner.find_element(By.ID, "id_voting_id").send_keys('64654654654654')
        self.cleaner.find_element(By.ID, "id_voter_id").click()
        self.cleaner.find_element(By.ID, "id_voter_id").send_keys('64654654654654')
        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[3]/div/div[1]/div/form/div/p').text == 'Please correct the errors below.')
        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/census/census/add")

    def test_export_to_csv(self):
        # Crea un queryset con los datos de prueba
        self.censuses = [Census(voting_id=1, voter_id=1),Census(voting_id=1,voter_id=2)]
        queryset = self.censuses
        # Invoque la función de exportación
        response = export_to_csv(self.census_admin, None, queryset)

        # Verifique que la respuesta sea un objeto HttpResponse
        self.assertEqual(response.status_code,200)
        self.assertIsInstance(response, HttpResponse)

        # Verifique que el contenido de la respuesta sea un archivo CSV válido
        csv_data = response.getvalue().decode('utf-8')
        csv_reader = csv.reader(StringIO(csv_data))
        rows = list(csv_reader)

        # Verifique el encabezado
        self.assertEqual(rows[0], ['ID', 'voting id', 'voter id'])
        #linea de encabezado y dos census
        self.assertEquals(len(rows), 3)
        self.assertEquals(rows[1][1], '1')
        self.assertEquals(rows[1][2], '1')
        self.assertEquals(rows[2][1], '1')
        self.assertEquals(rows[2][2], '2')

        # Verifique el encabezado
        self.assertEqual(rows[0], ['ID', 'voting id', 'voter id'])

    def test_export_to_pdf(self):
        # Crea un queryset con los datos de prueba
        queryset = Census.objects.all()

        # Invoque la función de exportación
        response = export_to_pdf(self.census_admin, None, queryset)

        # Verifique que la respuesta sea un objeto HttpResponse
        self.assertIsInstance(response, HttpResponse)

    def test_get_related_object(self):
        # Prueba la función get_related_object con datos de prueba
        related_user = get_related_object('User', self.user.pk)
        self.assertEqual(self.user, related_user)

    def test_get_related_object_blank(self):
        # Prueba la función get_related_object con datos de prueba
        related_user = get_related_object('User', '999')
        self.assertEqual('', related_user)


class CensusSeleniumTests(LiveServerTestCase):
    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()
        self.census = Census(voting_id=1, voter_id=1)
        self.census.save()
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()

    def test_export_to_csv(self):
        # Abre la página de administración
        self.driver.get(self.live_server_url + '/admin/login/?next=/admin/')
        self.driver.set_window_size(1400,800)

        # Inicia sesión en el administrador
        self.driver.find_element(By.ID,'id_username').click()
        self.driver.find_element(By.ID,'id_username').send_keys('admin')
        self.driver.find_element(By.ID,'id_password').click()
        self.driver.find_element(By.ID,'id_password').send_keys('qwerty')
        self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        # Navega a la sección de censos
        self.driver.get(self.live_server_url + '/admin/census/census')
        # Selecciona todos los censos
        self.driver.find_element(By.CLASS_NAME,'action-select').click()
        
        # Ejecuta la acción de exportar a CSV
        self.driver.find_element(By.NAME,'action').click()
        self.driver.find_element(By.NAME,'action').send_keys('export_to_csv')
        self.driver.find_element(By.NAME,'index').click()

        # Confirma la acción
        self.driver.find_element(By.NAME,'index').click()
        self.driver.save_screenshot("capturacsv.png")
        # Verifica que la respuesta sea un archivo CSV
        check=False
        
        try:
            self.driver.find_element(By.CLASS_NAME,'warning')
        except NoSuchElementException:
            check =  True

        self.assertTrue(check)

    def test_export_to_pdf(self):
        # Abre la página de administración
        self.driver.get(self.live_server_url + '/admin/login/?next=/admin/')
        self.driver.set_window_size(1400,800)
        # Inicia sesión en el administrador
        self.driver.find_element(By.ID,'id_username').click()
        self.driver.find_element(By.ID,'id_username').send_keys('admin')
        self.driver.find_element(By.ID,'id_password').click()
        self.driver.find_element(By.ID,'id_password').send_keys('qwerty')
        self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

        # Navega a la sección de censos
        self.driver.get(self.live_server_url + '/admin/census/census')
       
        # Selecciona todos los censos
        self.driver.find_element(By.CLASS_NAME,'action-select').click()
        self.driver.save_screenshot("captura1.png")
        # Ejecuta la acción de exportar a CSV
        self.driver.find_element(By.NAME,'action').click()
        self.driver.save_screenshot("captura2.png")
        self.driver.find_element(By.NAME,'action').send_keys('export_to_pdf')
        self.driver.save_screenshot("captura3.png")
        self.driver.find_element(By.NAME,'index').click()
        self.driver.save_screenshot("captura4.png")
        # Confirma la acción
        self.driver.find_element(By.NAME,'index').click()
        self.driver.save_screenshot("captura.png")
        
        check=False
        
        try:
            self.driver.find_element(By.CLASS_NAME,'warning')
        except NoSuchElementException:
            check =  True

        self.assertTrue(check)