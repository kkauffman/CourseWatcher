import re
import requests
from bs4 import BeautifulSoup

from app import db
from app.models import School, Department, Course, CourseRequest


class CoursePoll():
    """ A base class for all school course pollers. """
    create_db = False
    data = {}
    request_data = None
    requests = []

    def __init__(self, create_db=False):
        """ Creates the class, if create_db is true all entries are made on database update. """
        self.create_db = create_db

    def GetCourseData(self):
        """ Downloads all the school's course data. """
        raise NotImplementedError('Method needs to be overridden!')

    def ParseData(self):
        """ Parses the school's course data. """
        raise NotImplementedError('Method needs to be overridden!')

    def UpdateDatabase(self):
        """ Updates the database and creates all notifications/requests. """
        raise NotImplementedError('Method needs to be overridden!')

    def GetCourseRequests(self):
        """ Returns all course notifications/requests and then clears all stored ones. """
        self.GetCourseData()
        self.ParseData()
        self.UpdateDatabase()

        requests = self.requests
        self.request = []

        return requests

    def CreateRequests(self, course):
        """ Creates a tuple of course notifications/requests and their notification email. """
        requests = CourseRequest.query.filter(CourseRequest.course_id == course.id)

        email_msg = '%s has opened!' % (course.name)
        return (requests, email_msg)


class UCMCoursePoll(CoursePoll):
    """ Polls UC Merced for their course data. """

    # Parameters to get the list of all classes offered at UC Merced
    url = 'https://pbanssb.ucmerced.edu/pls/PROD/xhwschedule.P_ViewSchedule'
    payload = {'openclasses': 'N', 'subjcode': 'ALL', 'validterm': '201510'}
    headers = {'host': 'pbanssb.ucmerced.edu'}

    # In the returned page rows containing course data have this number of columns
    columns_in_table = 13

    # The column the CRN is in
    crn_offset = 0

    # The column the Course # is in and its format:
    # format is  (up to 4 letter)-(3 numbers)-(2 numbers + 1 or 0 letters)
    course_num_offset = 1
    course_num_re = re.compile(r'(\w{,4})-(\w{,4})-(\w{,4})')

    # The offset for course title
    title_offset = 2

    # The offset for the course's max enrollment
    max_enrl_offset = 10

    # The offset for current enrollment
    cur_enrl_offset = 11

    # A regular expression to parse the title of classes
    title_re = re.compile(r'^\<small\>(.+?)\<')

    # The name of the school database table
    school_name = 'UC Merced'

    # The data returned from Beautiful Soup
    request_data = None

    def __init__(self, create_db=False):
        CoursePoll.__init__(self, create_db)

    def GetCourseData(self):
        r = requests.post(self.url, data=self.payload, headers=self.headers)

        if r.status_code != requests.codes.ok:
            raise RuntimeError('Unable to get course data')

        self.request_data = BeautifulSoup(r.text)

    def ParseData(self):
        if self.request_data is None:
            raise RuntimeError('There is no data to parse.')

        for department in self.request_data.findAll('h3'):
            table = department.next_sibling.next_sibling
            courses = []

            if table.name != 'table':
                continue

            for row in table.find_all('tr'):
                course = row.findAll('td')

                if len(course) != self.columns_in_table:
                    continue

                course_data = {}

                match = self.course_num_re.match(course[self.course_num_offset].text)
                if not match:
                    continue

                course_data['dept'] = match.group(1)
                course_data['course'] = match.group(2)
                course_data['section'] = match.group(3)
                course_data['is_lecture'] = match.group(2).isdigit() and match.group(3).isdigit()

                # This grabs only the course name and not the extra optional text
                course_data['title'] = course[self.title_offset].text
                match = self.title_re.match(str(course[self.title_offset].next_element))

                if match:
                    course_data['title'] = match.group(1).decode('utf8')

                try:
                    course_data['crn'] = int(course[self.crn_offset].text)
                    cur_enrl = int(course[self.cur_enrl_offset].text)
                    max_enrl = int(course[self.max_enrl_offset].text)

                    course_data['open'] = cur_enrl < max_enrl
                except ValueError:
                    continue

                courses.append(course_data)

            self.data[department.text] = courses

    def UpdateDatabase(self):
        if self.data is None:
            raise RuntimeError('No data found to update database with')

        school = School.query.filter_by(name=self.school_name).first()

        if school is None:
            if self.create_db:
                school = School(name=self.school_name)
                db.session.add(school)
            else:
                raise RuntimeError('%s not found in database' % (self.school_name))

        for department_name in self.data:
            department = Department.query.filter_by(name=department_name,
                                                    school_id=school.id).first()

            for course in self.data[department_name]:
                if department is None:
                    if self.create_db:
                        department = Department(name=department_name,
                                                abrv=course['dept'],
                                                school_id=school.id)
                        db.session.add(department)
                    else:
                        raise RuntimeError('Department (%s) not found in database'
                                           % (department_name))

                db_course = Course.query.filter_by(crn=course['crn']).first()

                if db_course is None:
                    db_course = Course(crn=course['crn'], name=course['title'],
                                       number=course['course'],
                                       section=course['section'],
                                       is_lecture=course['is_lecture'],
                                       is_open=course['open'],
                                       department_id=department.id)
                    db.session.add(db_course)
                elif not db_course.is_open and course['open']:
                    self.requests.append(self.CreateRequests(db_course))
                    db_course.is_open = True

        db.session.commit()
