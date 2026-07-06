import os
import unittest
import uuid

from website import create_app
from website.models import create_job, create_user, get_job_by_id


class EgyLanceAppTests(unittest.TestCase):
    def setUp(self):
        os.chdir('d:/egylance')
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_home_page_renders(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_signup_page_renders(self):
        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)

    def test_privacy_and_terms_pages_render(self):
        self.assertEqual(self.client.get('/privacy-policy').status_code, 200)
        self.assertEqual(self.client.get('/terms').status_code, 200)

    def test_job_detail_page_renders(self):
        unique = uuid.uuid4().hex[:8]
        freelancer_id = create_user(f'testerfreelancer{unique}', f'testerfreelancer{unique}@example.com', 'Pass123!', role='freelancer', full_name='Tester')
        job_id = create_job(freelancer_id, 'Website design', 'Modern landing page', 'Design', '250', 'Cairo')
        with self.client.session_transaction() as session:
            session['user_id'] = freelancer_id
        response = self.client.get(f'/jobs/{job_id}')
        self.assertEqual(response.status_code, 200)

    def test_freelancer_can_post_without_verification(self):
        unique = uuid.uuid4().hex[:8]
        freelancer_id = create_user(f'poster{unique}', f'poster{unique}@example.com', 'Pass123!', role='freelancer', full_name='Poster')
        with self.client.session_transaction() as session:
            session['user_id'] = freelancer_id
        response = self.client.post('/jobs', data={
            'title': 'Logo design',
            'description': 'Clean logo concept',
            'category': 'Design',
            'budget': '150',
            'location': 'Alexandria',
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/jobs/', response.headers['Location'])

    def test_google_auth_route_redirects_to_signup_when_unconfigured(self):
        response = self.client.get('/auth/google', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/signup', response.headers['Location'])

    def test_freelancer_dashboard_lists_their_services(self):
        unique = uuid.uuid4().hex[:8]
        freelancer_id = create_user(f'owner{unique}', f'owner{unique}@example.com', 'Pass123!', role='freelancer', full_name='Owner')
        job_id = create_job(freelancer_id, 'UI polish', 'Refine the mobile experience', 'Design', '180', '')
        with self.client.session_transaction() as session:
            session['user_id'] = freelancer_id
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'/jobs/{job_id}'.encode(), response.data)

    def test_job_detail_tracks_views(self):
        unique = uuid.uuid4().hex[:8]
        freelancer_id = create_user(f'viewer{unique}', f'viewer{unique}@example.com', 'Pass123!', role='freelancer', full_name='Viewer')
        job_id = create_job(freelancer_id, 'Landing page help', 'Improve conversion copy', 'Marketing', '300', '')
        with self.client.session_transaction() as session:
            session['user_id'] = freelancer_id
        response = self.client.get(f'/jobs/{job_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_job_by_id(job_id)['views_count'], 1)


if __name__ == '__main__':
    unittest.main()
