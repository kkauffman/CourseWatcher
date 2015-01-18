from app import db

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    departments = db.relationship('Department', backref='author',
                                  lazy='dynamic')

    def __repr__(self):
        return '<School %r>' % (self.name)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    abrv = db.Column(db.String(4), unique=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    courses = db.relationship('Course', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<Department %r>' % (self.name)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crn = db.Column(db.Integer())
    name = db.Column(db.String())
    number = db.Column(db.String(4))
    section = db.Column(db.String(4))
    is_lecture = db.Column(db.Boolean())
    is_open = db.Column(db.Boolean())
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    requests = db.relationship('CourseRequest', backref='author',
                               lazy='dynamic')

    def __repr__(self):
        return '<Course %r>' % (self.name)

class CourseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String())
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    
    def __repr__(self):
        return '<CourseRequest %r>' % (self.email)
