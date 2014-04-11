# coding: utf-8

import os
from UserDict import DictMixin
from fnmatch import fnmatch
from datetime import datetime

from pyramid.threadlocal import get_current_registry
from pyramid.traversal import resource_path
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime, Date
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy import UniqueConstraint
from sqlalchemy import Table, select
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import backref
from sqlalchemy.orm import deferred
from sqlalchemy.orm import object_mapper
from sqlalchemy.orm import relation, relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_
from sqlalchemy.sql import select
from sqlalchemy.util import classproperty
from transaction import commit
from zope.deprecation.deprecation import deprecated
from zope.interface import implements

from kotti import Base
from kotti import DBSession
from kotti import get_settings
from kotti import metadata
from kotti.interfaces import INode
from kotti.interfaces import IContent
from kotti.interfaces import IDocument
from kotti.interfaces import IFile
from kotti.interfaces import IImage
from kotti.interfaces import IDefaultWorkflow
from kotti.migrate import stamp_heads
from kotti.security import PersistentACLMixin
from kotti.security import has_permission
from kotti.security import view_permitted
from kotti.security import Principals, get_principals
from kotti.sqla import ACLType
from kotti.sqla import JsonType
from kotti.sqla import MutationList
from kotti.sqla import NestedMutationDict
from kotti.util import ViewLink
#from kotti.util import _
from kotti.util import camel_case_to_name
from kotti.util import get_paste_items
from kotti.util import camel_case_to_name
from kotti.resources import Document

from mba import _


friend = Table(
        'friends', Base.metadata,
        Column('user_a_id', Integer, ForeignKey('mba_users.id'), primary_key=True),
        Column('user_b_id', Integer, ForeignKey('mba_users.id'), primary_key=True),
        )


class UserInterest(Base):
    interest_id = Column(Integer, ForeignKey('interests.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('mba_users.id'), primary_key=True)
    interest = relationship('Interest', backref='interest_items')
    name = association_proxy('interest', 'name')

    @classmethod
    def _interest_find_or_create(cls, name):
        with DBSession.no_autoflush:
            interest = DBSession.query(Interest).filter_by(name=name).first()
        if interest is None:
            interest = Interest(name=name)
        return cls(interest=interest)


class Interest(Base):
    __table_args__ = (
        UniqueConstraint('name'),
        )
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(UnicodeText())

    @property
    def users(self):
        return [rel.user for rel in self.interest_items]


#This is a base class for all users
class MbaUser(Base):

    __mapper_args__ = dict(
        order_by='mba_users.name',
        polymorphic_on='type',
        polymorphic_identity='mba_users',
        #with_polymorphic='*',
        )

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100), unique=True)
    password = Column(Unicode(100))
    avatar = Column(String(100))
    active = Column(Boolean)
    confirm_token = Column(Unicode(100))
    title = Column(Unicode(100), nullable=False)
    email = Column(Unicode(100), unique=True)
    groups = Column(JsonType(), nullable=False)
    creation_date = Column(DateTime(), nullable=False)
    last_login_date = Column(DateTime())
    sex = Column(Integer())
    type = Column(String(50), nullable=False)
    
    _interests = relationship("UserInterest", backref='user')
    interests = association_proxy(
        '_interests',
        'name',
        creator=UserInterest._interest_find_or_create,
        )

    friends = relationship("MbaUser", secondary=friend,
                primaryjoin=id==friend.c.user_a_id,
                secondaryjoin=id==friend.c.user_b_id,
            )

    def __init__(self, name, password=None, active=True, confirm_token=None,
                 title=u"", email=None, groups=(), **kwargs):
        self.name = name
        if password is not None:
            password = get_principals().hash_password(password)
        self.password = password
        self.active = active
        self.confirm_token = confirm_token
        self.title = title
        self.email = email
        self.groups = groups
        self.creation_date = datetime.now()
        self.last_login_date = None
        super(MbaUser, self).__init__(**kwargs)

    def __repr__(self):  # pragma: no cover
        return '<MbaUser %r>' % self.name

friend_union = select([
                friend.c.user_a_id,
                friend.c.user_b_id
                ]).union(
                        select([
                            friend.c.user_b_id,
                            friend.c.user_a_id,
                            ])
                ).alias()

MbaUser.all_friends = relationship('MbaUser',
                        secondary=friend_union,
                        primaryjoin=MbaUser.id==friend_union.c.user_a_id,
                        secondaryjoin=MbaUser.id==friend_union.c.user_b_id,
                        viewonly=True)


class City(Base):
    __tablename__ = 'city'
    __table_args__ = (
        UniqueConstraint('name'),
        )
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    acts = relationship("Act", backref='city', order_by='desc(Act.creation_date)')


class Participate(Base):
    __tablename__ = 'participate'
    user_id = Column(Integer, ForeignKey('students.id'), primary_key=True)
    act_id = Column(Integer, ForeignKey('acts.id'), primary_key=True)
    creation_date = Column(DateTime(), nullable=False, default=datetime.now)
    #用户参加活动之后可进行评分
    rating = Column(Integer())
    user = relationship("Student", backref='partin')


class ActStatus:
    DRAFT, PUBLIC, FINISH, CANCEL = 0, 1, 2, 3


# Act means activity
class Act(Document):
    id = Column('id', Integer, ForeignKey('documents.id'), primary_key=True)
    status = Column(Integer(), nullable=False)
    city_id = Column(Integer, ForeignKey('city.id'))
    city_name = association_proxy('city', 'name')

    type_info = Document.type_info.copy(
        name=u'Act',
        title=_(u'Act'),
        add_view=u'add_act',
        addable_to=[u'Act'],
        )
    
    _parts = relationship('Participate', backref='act')

    @property
    def parts(self):
        return [rel.user for rel in self._parts]

class Student(MbaUser):

    @classproperty
    def __mapper_args__(cls):
        return dict(
                order_by='mba_users.name',
                polymorphic_identity=camel_case_to_name(cls.__name__)
            )

    id = Column('id', Integer, ForeignKey('mba_users.id'), primary_key=True)
    school = Column(String(100))
    school_year = Column(Integer())
    
    real_name = Column(String(20), nullable=False)
    birth_date = Column(Date())
    identify = Column(String(30))
    phone = Column(Integer())
    home_number = Column(String(20))
    residence = Column(String(20))
    salary = Column(Integer())
    work_years = Column(String(20))
    company_phone = Column(String(30))
    keyword = Column(String(100))
    job_status = Column(String(100))

    resumes = relationship('Resume', backref='user')

    def __init__(self, name, real_name='', birth_date=None, school=None, school_year=0, **kwargs):
        self.real_name = real_name
        self.birth_date = birth_date
        self.school = school
        self.shcool_year = school_year
        super(Student, self).__init__(name, **kwargs)

    def __repr__(self):  # pragma: no cover
        return '<Student %r>' % self.name


# Tables about resume
# Education n -- 1 Resume 
class Education(Base):
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'))
    name = Column(String(100), nullable=False)
    location = Column(String(100))
    start_date = Column(DateTime())
    finish_date = Column(DateTime())
    major = Column(String(30))
    degree = Column(String(20))
    abroad =  Column(Boolean)
    summary = Column(UnicodeText())

# Job n -- 1 Resume 
class Job(Base):
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'))
    job_type = Column(String(50))
    location = Column(String(200))
    industy = Column(String(100))
    duty = Column(String(200))
    start_date = Column(DateTime())
    finish_date = Column(DateTime())
    description = Column(UnicodeText())
    is_current = Column(Boolean)

class Train(Base):
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'))
    start_date = Column(DateTime())
    finish_date = Column(DateTime())
    location = Column(String(200))
    course = Column(String(100))
    certificate = Column(String(50))
    summary = Column(UnicodeText())

class Language(Base):
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'))
    lang_type = Column(String(20))
    grasp = Column(String(20))
    read_cap = Column(String(20))
    write_cap = Column(String(20))

# resume many to many skill
class ResumeSkill(Base):
    resume_id = Column(Integer, ForeignKey('resumes.id'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('skills.id'), primary_key=True)
    skill = relationship('Skill', backref='resume_items')
    name = association_proxy('skill', 'name')

    @classmethod
    def _skill_find_or_create(cls, name):
        with DBSession.no_autoflush:
            skill = DBSession.query(Skill).filter_by(name=name).first()
        if skill is None:
            skill = Skill(name=name)
        return cls(skill=skill)

class Skill(Base):
    __table_args__ = (
        UniqueConstraint('name'),
        )
    id = Column(Integer, primary_key=True)
    name = Column(String(250))

    @property
    def resumes(self):
        return [rel.resume for rel in self.resume_items]

class Resume(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('mba_users.id'))
    title = Column(String(250))
    create_date = Column(DateTime())
    modify_date = Column(DateTime())
    _skills = relationship('ResumeSkill', backref='resume')
    skills = association_proxy(
        '_skills',
        'name',
        creator=ResumeSkill._skill_find_or_create,
        )

    # String like jobid1,jobid2,jobid3 5,6,3,1 
    job_order = Column(String(100))
    jobs = relationship('Job')
    education = relationship('Education')
    trains = relationship('Train')
    langs = relationship('Language')

    def order_jobs(self):
        jobs = self.jobs
        ids = dict([(obj.id,obj) for obj in jobs])
        rlts = []
        for s in self.job_order.split(','):
            id = int(s)
            if id in ids:
                rlts.append(ids[id])
        return (rlts+list(set(jobs).difference(set(rlts))))

#用户投给职位的简历
class PositionResume(Base):
    position_id = Column(Integer, ForeignKey('positions.id'), primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'), primary_key=True)
    create_date = Column(DateTime())
    #反馈状态
    status = Column(Integer())
    resume = relationship('Resume', backref='postition_items')
    user = association_proxy('resume', 'user')

#工作职位表
class Position(Document):
    id = Column('id', Integer, ForeignKey('documents.id'), primary_key=True)
    status = Column(Integer(), nullable=False)
    resumes = relationship('PositionResume', backref='position')
    users = association_proxy('resumes', 'user')

    type_info = Document.type_info.copy(
        name=u'Position',
        title=_(u'Position'),
        add_view=u'add_position',
        addable_to=[u'Position'],
        )
