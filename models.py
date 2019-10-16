from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class User(db.Model):
	__tablename__ = 'user'
	user_id = Column(Integer, primary_key=True)
	username = Column(String(24), nullable=False)
	email = Column(String(80), nullable=False)
	pw_hash = Column(String(64), nullable=False)
	name = Column(String(80), nullable=False)
	user_type = Column(String(10), nullable=False)

	def __repr__(self):
		return '<User %r>'%self.username


class Event(db.Model):
	__tablename__ = 'event'
	event_id = Column(Integer, primary_key=True)
	date = Column(Date, unique=True, nullable=False)
	name = Column(String(100), nullable=False)

	requestor_id = Column(Integer, ForeignKey(User.user_id), nullable=False)
	requestor = relationship('User', foreign_keys=[requestor_id])

	staff_id1 = Column(Integer, ForeignKey(User.user_id))
	staff1 = relationship('User', foreign_keys=[staff_id1])
	staff_id2 = Column(Integer, ForeignKey(User.user_id))
	staff2 = relationship('User', foreign_keys=[staff_id2])
	staff_id3 = Column(Integer, ForeignKey(User.user_id))
	staff3 = relationship('User', foreign_keys=[staff_id3])

	def __repr__(self):
		return '<Event %r, %r>'%(self.date, self.name)



