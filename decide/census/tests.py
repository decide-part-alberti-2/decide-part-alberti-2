from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from .models import Census
from voting.models import Question, Voting
from base import mods
from django.test import LiveServerTestCase
from base.tests import BaseTestCase
from datetime import datetime
from django.contrib import admin
from .admin import export_to_csv, export_to_pdf, get_related_object, CensusAdmin
from io import StringIO
from django.http import HttpResponse
import csv
import os


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
        # Ejecuta la acción de exportar a CSV
        self.driver.find_element(By.NAME,'action').click()
        self.driver.find_element(By.NAME,'action').send_keys('export_to_pdf')
        self.driver.find_element(By.NAME,'index').click()
        # Confirma la acción
        self.driver.find_element(By.NAME,'index').click()
        
        check=False
        
        try:
            self.driver.find_element(By.CLASS_NAME,'warning')
        except NoSuchElementException:
            check =  True

        self.assertTrue(check)

    
    def test_import_from_csv(self):
        # Agrega lógica para crear un archivo CSV temporal con datos de prueba
        csv_data = "voting_id,voter_id\n4,1\n5,1"
        csv_file_path = os.getcwd()+"test_census_import.csv"
        with open(csv_file_path, "w") as csv_file:
            csv_file.write(csv_data)

        try:
            # Abre la página de administración
            self.driver.get(self.live_server_url + '/admin/login/?next=/admin/')
            self.driver.set_window_size(1400, 800)

            # Inicia sesión en el administrador
            self.driver.find_element(By.ID, 'id_username').click()
            self.driver.find_element(By.ID, 'id_username').send_keys('admin')
            self.driver.find_element(By.ID, 'id_password').click()
            self.driver.find_element(By.ID, 'id_password').send_keys('qwerty')
            self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

            # Navega a la sección de censos
            self.driver.get(self.live_server_url + '/census/import_census/')

            # Carga el archivo CSV en el formulario
            self.driver.find_element(By.ID, 'file').send_keys(csv_file_path)

            # Envía el formulario de importación
            submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_button.click()

            # Verifica el mensaje de éxito o cualquier otro indicador en la página
            self.assertEquals(self.driver.find_element(By.TAG_NAME, 'h1').text, "Import Census Result")
        finally:
            # Borra el archivo CSV temporal después del test
            os.remove(csv_file_path)
            
    def test_ldap_check_votacion_pass(self):

        antes = Census.objects.count()
        u = User(username='gauss')
        u.set_password('123')
        u.save()

        admin = User(username='administrador')
        admin.set_password('1234567asd')
        admin.is_staff = True
        admin.save()

        q = Question(desc='test question')
        q.save()
        v = Voting(name='titulo 1', desc='Descripcion1',question=q)
        v.save()


        self.client.force_login(admin)
        votacion = Voting.objects.all().filter(end_date__isnull=True)[0].id
        data = {'voting': votacion, 'urlLdap': 'ldap.forumsys.com:389', 'branch': 'ou=mathematicians,dc=example,dc=com',
                'treeSuffix': 'cn=read-only-admin,dc=example,dc=com','pwd': 'password'}
        response = self.client.post('/census/addLDAPcensusVotacion/', data)
        despues = Census.objects.count()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(antes+1,despues)


    def test_ldap_check_votacion_wrong_login(self):

        antes = Census.objects.count()
        u = User(username='manolito')
        u.set_password('123')
        u.save()


        q = Question(desc='test question')
        q.save()
        v = Voting(name='titulo 1', desc='Descripcion1',question=q)
        v.save()


        self.client.force_login(u)
        votacion = Voting.objects.all().filter(end_date__isnull=True)[0].id
        data = {'voting': votacion, 'urlLdap': 'ldap.forumsys.com:389', 'branch': 'ou=mathematicians,dc=example,dc=com',
                'treeSuffix': 'cn=read-only-admin,dc=example,dc=com','pwd': 'password'}
        response = self.client.post('/census/addLDAPcensusVotacion/', data)
        despues = Census.objects.count()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(antes,despues)
    

    def test_ldap_check_votacion_get(self):

        antes = Census.objects.count()
        u = User(username='einstein')
        u.set_password('123')
        u.save()


        admin = User(username='administrado')
        admin.set_password('1234567asd')
        admin.is_staff = True
        admin.save()

        #Hacemos la request
        self.client.force_login(admin)
        response = self.client.get('/census/addLDAPcensusVotacion/')
        despues = Census.objects.count()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(antes,despues)


    

