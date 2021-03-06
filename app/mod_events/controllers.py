# Import flask dependencies
from flask import Blueprint, request, flash, g, session, redirect, url_for
from flask_restplus import Namespace, Resource, fields, reqparse

# Import the database object from the main app module
from app import db

# Import module models (i.e. User)
from app.mod_events.models import EventType, Event
from app.mod_core.models import Tag

# Import utils
from app.utils import fill_object
from app.utils import abort_if_none
from app.utils import msg

# Define the blueprint: 'event', set its url prefix: app.url/event
mod_event = Blueprint('event', __name__, url_prefix='/event')
ns = Namespace('event', description='Operations related to events')

tag_m = ns.model('tag', {
    'name': fields.String,
    'slug': fields.String
})

event_m = ns.model('event', {
    'id_event': fields.Integer,
    'title': fields.String(required=True),
    'description': fields.String(required=True),
    'date_start': fields.DateTime(required=True),
    'date_end': fields.DateTime(required=True),
    'location': fields.String(required=True),
    'url': fields.String(required=True),
    'need_help': fields.Boolean(required=True),
    'id_event_type': fields.Integer,
    'tags': fields.List(fields.Nested(tag_m)),
    'files': fields.List(fields.Integer)
})

event_m_expect = ns.model('event', {
    'title': fields.String(required=True),
    'description': fields.String(required=True),
    'date_start': fields.DateTime(required=True),
    'date_end': fields.DateTime(required=True),
    'location': fields.String(required=True),
    'url': fields.String(required=True),
    'need_help': fields.Boolean(required=True),
    'id_event_type': fields.Integer,
    'tags': fields.List(fields.Nested(tag_m)),
    'files': fields.List(fields.Integer)
})

event_type_m = ns.model('event_type', {
    'id_event_type': fields.Integer,
    'name': fields.String,
    'description': fields.String
})
event_type_m_expect = ns.model('event_type', {
    'name': fields.String,
    'description': fields.String
})


# TODO: Fazer parte referentes a upload de arquivos
# TODO: Definir como será o json do query
@ns.route('/<int:id>')
@ns.doc(params={'id': 'Event ID'})
@ns.response(403, 'User is not logged or not have permission')
@ns.response(400, 'ID is not int')
@ns.response(404, 'Not Found')
class EventController(Resource):
    @ns.response(200, 'Returns the event model on the body of the response', event_m)
    @ns.marshal_with(event_m)
    def get(self, id):
        '''Get an event by ID'''
        ev = Event.query.filter(Event.disabled == False).filter(Event.id_event == id).first()
        abort_if_none(ev, 404, 'Not Found')
        return ev

    @ns.response(200, 'Successfully updated', event_m)
    @ns.header('Authorization', 'The authorization token')
    @ns.expect(event_m_expect)
    def put(self, id):
        '''Update an event by ID'''
        ev = Event.query.filter(Event.disabled == False).filter(Event.id_event == id).first()
        abort_if_none(ev, 404, 'Not Found')
        fill_object(ev, request.json)
        db.session.commit()
        return msg('success!')

    @ns.response(200, 'Disabled on db')
    @ns.header('Authorization', 'The authorization token')
    def delete(self, id):
        '''Delete an event by ID'''
        ev = Event.query.filter(Event.disabled == False).filter(Event.id_event == id).first()
        abort_if_none(ev, 404, 'Not Found')
        ev.disabled = True
        db.session.commit()
        return msg('disabled')


@ns.route('/')
@ns.response(403, 'User is not logged or not have permission')
@ns.response(404, 'Not Found')
class EventPostController(Resource):
    @ns.response(400, 'The query json is wrong')
    @ns.response(200, 'Return an event list that matched criteria', event_m)
    @ns.marshal_with(event_m)
    def get(self):
        '''Get an event list'''
        return Event.query.filter(Event.disabled == False).all()

    @ns.response(400, 'The model is malformed')
    @ns.response(200, 'Added', event_m)
    @ns.header('Authorization', 'The authorization token')
    @ns.expect(event_m_expect)
    def post(self):
        '''Create a new event'''
        ev = Event()
        ev.disabled = False

        tags = request.json['tags'][:] # copy the tags dict
        del request.json['tags']
        for tm in tags:
            t = Tag.query\
                .filter(Tag.name == tm['name'])\
                .filter(Tag.disabled == False)\
                .first()

            if t is not None:
                ev.tags.append(t)
                continue

            tag = Tag()
            fill_object(tag, tm)
            ev.tags.append(tag)

        et = EventType.query.filter(EventType.id_event_type == request.json['id_event_type']).first()
        abort_if_none(et, 404, 'Event Type Not Found')

        fill_object(ev, request.json)
        # submit objects to db
        db.session.add(ev)
        db.session.commit()

        return msg(ev.id_event, 'id')


@ns.route('/type/<int:id>')
@ns.doc(params={'id': 'Event Type ID'})
@ns.response(403, 'User is not logged or not have permission')
@ns.response(400, 'ID is not int')
@ns.response(404, 'Not Found')
@ns.header('Authorization', 'The authorization token')
class EventTypeController(Resource):

    @ns.response(200, 'Returns the event model on the body of the response', event_type_m)
    @ns.marshal_with(event_type_m)
    def get(self, id):
        '''Get an event_type by ID'''
        et = EventType.query.filter(EventType.disabled == False).filter(EventType.id_event_type == id)
        et = et.first()
        abort_if_none(et, 404, 'Not Found')
        return et

    @ns.response(200, 'Event altered')
    @ns.expect(event_type_m_expect)
    def put(self, id):
        '''Update an event_type by ID'''
        et = EventType.query.filter(EventType.disabled == False).filter(EventType.id_event_type == id)
        et = et.first()
        abort_if_none(et, 404, 'Not Found')
        fill_object(et, request.json)
        db.session.commit()
        return msg('altered')

    @ns.response(200, 'Event disabled')
    def delete(self, id):
        '''Delete an event_type by ID'''
        et = EventType.query.filter(EventType.disabled == 0).filter(EventType.id_event_type == id)
        et = et.first()
        abort_if_none(et, 404, 'Not Found')
        et.disabled = True
        db.session.commit()
        return msg('disabled')


@ns.route('/type/')
@ns.response(403, 'User is not logged or not have permission')
@ns.header('Authorization', 'The authorization token')
class EventTypePostController(Resource):

    @ns.response(400, 'One of the arguments is malformed')
    @ns.response(200, 'Return an list of events that matched criteria', event_type_m)
    @ns.marshal_with(event_type_m)
    def get(self):
        '''Get a event_type list'''
        return EventType.query.filter(EventType.disabled == False).all()


    @ns.response(400, 'The model is malformed')
    @ns.response(200, 'Event inserted')
    @ns.expect(event_type_m_expect)
    def post(self):
        '''Create a new event_type'''
        et = EventType.query.filter(EventType.name == request.json['name'])
        et = EventType(request.json['name'], request.json['description'])
        et.disabled = False
        # abort_if_none(et, 404, 'Not Found')
        db.session.add(et)
        db.session.commit()
        return msg(et.id_event_type, 'id')