import os
import unittest
from bs4 import BeautifulSoup

from app.CoursePoll import UCMCoursePoll
from app import app, db
from app.models import School, Department, Course, CourseRequest
from config import basedir


class UCMCoursePollTest(unittest.TestCase):
    is_setup = False
    poller = None


    def setUp(self):
        if not self.is_setup:
            app.config['TESTING'] = True
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
            self.app = app.test_client()
            db.create_all()

            self.poller = UCMCoursePoll(True)
            self.test_data = BeautifulSoup(open('./test/data/UCMSampleData.html', 'r').read())

            self.is_setup = True


    def tearDown(self):
        db.session.remove()
        db.drop_all()


    def test_real_request(self):
        self.poller.GetCourseData()

        self.assertTrue(self.poller.request_data is not None)


    def test_sample_data(self):
        tmp = self.poller.request_data

        self.poller.request_data = self.test_data

        self.poller.ParseData()

        self.assertTrue('Chinese' in self.poller.data)

        courses = self.poller.data['Chinese']

        self.assertTrue(len(courses) == 2, 'Found %d Courses' % (len(courses)))
        self.assertTrue(courses[0]['crn'] == 10311, 'Found crn %d' % (courses[0]['crn']))
        self.assertTrue(courses[0]['dept'] == 'CHN', 'Found dept %s' % (courses[0]['dept']))
        self.assertTrue(courses[0]['course'] == '001', 'Found course %s' % (courses[0]['course']))
        self.assertTrue(courses[0]['section'] == '01', 'Found section %s' % (courses[0]['section']))
        self.assertTrue(courses[0]['is_lecture'], 'Found is_lecture %d' % (courses[0]['is_lecture']))
        self.assertTrue(courses[0]['title'] == 'Elementary Chinese I',
                        'Found title %s' % (courses[0]['title']))
        self.assertFalse(courses[1]['open'])
        
        self.poller.UpdateDatabase()
        course = Course.query.filter_by(crn=10701).first()
        db.session.add(CourseRequest(email='test', course_id = course.id))
        self.poller.data['Chinese'][1]['open'] = True
        self.poller.UpdateDatabase()

        self.assertTrue(len(self.poller.requests) == 1)

        self.poller.UpdateDatabase()

        self.poller.request_data = tmp


if __name__ == '__main__':
    unittest.main()
