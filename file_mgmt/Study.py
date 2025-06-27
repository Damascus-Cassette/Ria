from sqlalchemy import (Column, ForeignKey, Integer, String, create_engine, Table)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

db_url  = 'sqlite:///database.db'
engine  = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class student_course_link(Base):
    __tablename__ = 'student_course'     #Can also be displayed as a class inheriting from base so as to hold more functions
    id         = Column('id', Integer, primary_key = True)
    student_id = Column('student_id', Integer, ForeignKey('students.id'))
    course_id  = Column('course_id',  Integer, ForeignKey('courses.id'))

class Student(Base):
    __tablename__ = 'students'
    id      = Column(Integer, primary_key = True)
    name    = Column(String)
    courses = relationship("Course", secondary = 'student_course', back_populates='students')

class Course(Base):
    __tablename__ = 'courses'
    id       = Column(Integer, primary_key = True)
    title    = Column(String)
    students = relationship("Student",secondary = 'student_course',back_populates='courses')

Base.metadata.create_all(engine)

# math    = Course(title='math')
# physics = Course(title='physx')
# Bill = Student(name='Bill', courses=[math,physics]) 
# Rob  = Student(name='Rob',  courses=[math])

# session.add_all([math,physics,Bill,Rob])
# session.commit()

rob = session.query(Student).filter_by(name='Bill').first()


physx = session.query(Course).filter_by(title='physx').first()

rob.courses.append(physx)
rob.courses.append(physx)
rob.courses.append(physx)

for c in rob.courses:
    print(rob.name, 'is in course', c.title)