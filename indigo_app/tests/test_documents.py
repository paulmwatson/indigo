from django.test import testcases, override_settings


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class LibraryTest(testcases.TestCase):
    fixtures = ['work', 'user', 'drafts', 'published']

    def setUp(self):
        self.assertTrue(self.client.login(username='email@example.com', password='password'))

    def test_import_view(self):
        response = self.client.get('/documents/import/')
        self.assertEqual(response.status_code, 200)

    def test_published_document(self):
        response = self.client.get('/documents/1/')
        self.assertEqual(response.status_code, 200)

    def test_draft_document(self):
        response = self.client.get('/documents/10/')
        self.assertEqual(response.status_code, 200)
