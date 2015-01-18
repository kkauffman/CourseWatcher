from flask import render_template, request, session, redirect

from . import app, db, default_error, send_email
from .models import School, Department, Course, CourseRequest

@app.route('/')
def index():
    return render_template('index.html', schools=School.query.all())

def GetSchool(school):
    return School.query.filter_by(name = school).first()    

def GetCourses(school, department):
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
    school = School.query.filter(School.name == school_name).first()
    if school == None:
        return default_error, 400

    return render_template('departments.html', departments=school.departments.all())

@app.route('/<school>/<department>')
def course_page(school, department):
    courses = GetCourses(school, department)
    if courses is None:
        return default_error, 400

    return render_template('courses.html', courses=courses)

@app.route('/email', methods=['POST'])
def email_page():
    if 'course' in request.form:
        return render_template('email.html', course_id=request.form['course'])
    
    return default_error, 400

@app.route('/confirmation', methods=['POST'])
def confirmation_page():
    if 'course' in request.form and 'email' in request.form:
        email = request.form['email']
        course_id = request.form['course']

        course = Course.query.filter(Course.id == course_id).first()
        if course == None:
            return default_error, 400

        previous_request = CourseRequest.query.filter(CourseRequest.email == email,
                                                      CourseRequest.course_id == course_id).first()
        if previous_request != None:
            return render_template('alreadyexists.html', course=course, email=email)

        db.session.add(CourseRequest(email=email, course_id=course_id))
        db.session.commit()

        send_email([email], 'Course Watcher Conformation',
                   'This email confirms that we will send you an email when %s opens.'
                   % (course.name))

        return render_template('confirmation.html', course=course, email=email)

    return default_error, 400
