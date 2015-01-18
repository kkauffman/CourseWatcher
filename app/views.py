from flask import render_template, request, session, redirect

from . import app, db, default_error, send_email
from .models import School, Department, Course, CourseRequest


@app.route('/')
def index():
    """ Renders the home page where the user selects their school. """
    return render_template('index.html', schools=School.query.all())


def GetSchool(school):
    """ Converts a school name into the database object if it exists. """
    return School.query.filter_by(name=school).first()


def GetCourses(school, department):
    """ Gets a department's courses from its name and the schools name. """
    school = GetSchool(school)
    if school is None:
        return None

    department = Department.query.filter(Department.school_id == school.id,
                                         Department.name == department).first()
    if department is None:
        return None

    return department.courses.all()


@app.route('/<school_name>/')
def department_page(school_name):
    """ Renders the page where the user selects their department. """
    school = School.query.filter(School.name == school_name).first()
    if school is None:
        return default_error, 400

    return render_template('departments.html', departments=school.departments.all())


@app.route('/<school>/<department>')
def course_page(school, department):
    """ Renders the page where the user selects their course. """
    courses = GetCourses(school, department)
    if courses is None:
        return default_error, 400

    return render_template('courses.html', courses=courses)


@app.route('/email', methods=['POST'])
def email_page():
    """ Renders the email page. """
    if 'course' in request.form:
        return render_template('email.html', course_id=request.form['course'])

    return default_error, 400


@app.route('/confirmation', methods=['POST'])
def confirmation_page():
    """ Renders the confirmation page if the users request is successful or an already exists page. """
    if 'course' in request.form and 'email' in request.form:
        email = request.form['email']
        course_id = request.form['course']

        course = Course.query.filter(Course.id == course_id).first()
        if course is None:
            return default_error, 400

        previous_request = CourseRequest.query.filter(CourseRequest.email == email,
                                                      CourseRequest.course_id == course_id).first()
        if previous_request is not None:
            return render_template('alreadyexists.html', course=course, email=email)

        db.session.add(CourseRequest(email=email, course_id=course_id))
        db.session.commit()

        send_email([email], 'Course Watcher Conformation',
                   'This email confirms that we will send you an email when %s opens.'
                   % (course.name))

        return render_template('confirmation.html', course=course, email=email)

    return default_error, 400
