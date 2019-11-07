import os
import jinja2
import webapp2
import logging
import json
import base64

from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import Http
from apiclient import discovery

from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images

from google.appengine.api import users, app_identity

ASSIGNMENTS = {
    'a1' : {'SPREADSHEET_ID': '1ddelHaR10-7iKHH_ceaROjMFSJzhEOrOXSgGoS327-g', 'RANGE_NAME': 'Sheet1!A2:F'},
    'a2' : {'SPREADSHEET_ID': '1O0hjndFsfZbj-S3HisCAlNpImcv_JEZXkqSEICgWoJo', 'RANGE_NAME': 'Sheet1!A2:G'},
}

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CLIENT_SECRET_FILE = "client_secret.json"
SPREADSHEET_ID = '1ddelHaR10-7iKHH_ceaROjMFSJzhEOrOXSgGoS327-g'
RANGE_NAME = 'Sheet1!A2:F'

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Student(ndb.Model):
    student_id = ndb.StringProperty()
    name = ndb.StringProperty()

class Order(ndb.Model):
    student_id = ndb.StringProperty()
    order_json = ndb.StringProperty()
    date_created = ndb.DateTimeProperty(auto_now_add=True)

class DemoRecord(ndb.Model):
    student_id = ndb.StringProperty()
    demo_record = ndb.StringProperty()
    date_created = ndb.DateTimeProperty(auto_now_add=True)

class Registration(ndb.Model):
    student_id = ndb.StringProperty()
    email = ndb.StringProperty()
    username = ndb.StringProperty()
    password = ndb.StringProperty()
    date_created = ndb.DateTimeProperty(auto_now_add=True)

class RegistrationWithImage(ndb.Model):
    student_id = ndb.StringProperty()
    email = ndb.StringProperty()
    country = ndb.StringProperty()
    description = ndb.StringProperty()
    image = ndb.BlobProperty()
    date_created = ndb.DateTimeProperty(auto_now_add=True)

def get_marks_from_google_sheet(student_id, assignment):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CLIENT_SECRET_FILE, SCOPES)
    http = credentials.authorize(Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?' 'version=v4')
    service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

    logging.info(assignment)

    sheet = ASSIGNMENTS['a' + str(assignment)];

    logging.info(sheet)

    result = service.spreadsheets().values().get(spreadsheetId=sheet['SPREADSHEET_ID'], range=sheet['RANGE_NAME']).execute()
    values = result.get('values', [])

    if not values:
        return None
    else:
        for row in values:
            if (row[0] == student_id):
                logging.info(row)
                return row

def get_rows_from_google_sheets(sheet_id, range):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CLIENT_SECRET_FILE, SCOPES)
    http = credentials.authorize(Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?' 'version=v4')
    service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range).execute()
    values = result.get('values', [])

    return values

class ImportHandler(webapp2.RequestHandler):
    def get(self):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CLIENT_SECRET_FILE, SCOPES)
        http = credentials.authorize(Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?' 'version=v4')
        service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

        result = service.spreadsheets().values().get(spreadsheetId='1_Z-pb5KxpMwKi-hjmG24TSVHc1Sk9HB-SYAWYxw6uAA', range='ClassList!A:C').execute()
        values = result.get('values', [])

        if not values:
            return None
        else:
            Student(name = 'JFS', student_id = '1111').put()
            for row in values:
                s = Student(name = row[0], student_id = row[2])
                s.put()

def get_student(student_id):
    return Student.query(Student.student_id == student_id).get()

# Decreasing order by date
def get_registrations(student_id):
    return Registration.query(Registration.student_id == student_id).order(-Registration.date_created).fetch()

def get_registrations_with_image(student_id):
    return RegistrationWithImage.query(RegistrationWithImage.student_id == student_id).order(-Registration.date_created).fetch()

def get_registration_with_image(registration_id):
    return RegistrationWithImage.get_by_id(int(registration_id))

def get_demo_records(student_id):
    return DemoRecord.query(DemoRecord.student_id == student_id).order(-DemoRecord.date_created).fetch()

def get_orders(student_id):
    return Order.query(Order.student_id == student_id).order(-Order.date_created).fetch()

class OrderHandler(webapp2.RequestHandler):
    def post(self):
        student_id = self.request.get("student_id")
        order_json = self.request.get("order_json")

        if ((student_id is None or not student_id)or (order_json is None or not order_json)):
            self.response.set_status(500)
            self.response.out.write('All fields are required.')
        else:
            student = get_student(student_id)

            if (student is None):
                self.response.set_status(500)
                self.response.out.write('Student ID not found - ' + student_id)
            else:
                logging.info(student_id)
                logging.info(order_json)

                order = Order(student_id = student_id, order_json = order_json)
                k = order.put()

                logging.info(k)

                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(order_json)

class OrderListHandler(webapp2.RequestHandler):
    def get(self, student_id):
        if (get_student(student_id) is not None):
            orders = get_orders(student_id)

            for o in orders:
                logging.info(o.order_json)

            template_values = {
                'student_id': student_id,
                'orders': orders
            }

            template = JINJA_ENVIRONMENT.get_template('order/orders.html')
            self.response.write(template.render(template_values))
        else:
            self.response.set_status(500)
            self.response.out.write('Student ID not found - ' + student_id)

class RegisterHandler(webapp2.RequestHandler):
    def post(self):
        student_id = self.request.get("student_id")
        email = self.request.get("email")
        username = self.request.get("username")
        password = self.request.get("password")

        if ((student_id is None or not student_id)
                or (email is None or not email)
                or (username is None or not username)
                or (password is None or not password)):
            self.response.set_status(500)
            self.response.out.write('All fields are required.')
        else:
            if (get_student(student_id) is not None):
                encoded_password = base64.b64encode(password)

                r = Registration(student_id = student_id, email = email, username = username, password = encoded_password)
                k = r.put()

                logging.info(k)

                reg = {
                    'student_id': student_id,
                    'email': email,
                    'username': username,
                    'password': encoded_password
                }

                json_object = json.dumps(reg);

                logging.info(json_object)

                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(json_object)
            else:
                self.response.set_status(500)
                self.response.out.write('Student ID not found - ' + student_id)

class RegisterWithImageHandler(webapp2.RequestHandler):
    def post(self):
        student_id = self.request.get("student_id")
        email = self.request.get("email")
        country = self.request.get("country")
        description = self.request.get("description")
        avatarImage = self.request.get("avatarImage")

        if ((student_id is None or not student_id)
                or (email is None or not email)
                or (country is None or not country)
                or (description is None or not description)):
            self.response.set_status(500)
            self.response.out.write('All fields are required.')
        else:
            if (get_student(student_id) is not None):
                raw_file = self.request.get('avatarImage')

                r = RegistrationWithImage(student_id = student_id,
                    email = email,
                    country = country,
                    description = description,
                    image = raw_file)
                k = r.put()

                    # image = str(raw_file))

                reg = {
                    'student_id': student_id,
                    'email': email,
                    'country': country,
                    'description': description
                }

                json_object = json.dumps(reg);

                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(json_object)
            else:
                self.response.set_status(500)
                self.response.out.write('Student ID not found - ' + student_id)

class RegistrationListHandler(webapp2.RequestHandler):
    def get(self, student_id):
        if (get_student(student_id) is not None):
            registrations = get_registrations(student_id)

            template_values = {
                'student_id': student_id,
                'registrations': registrations
            }

            template = JINJA_ENVIRONMENT.get_template('registration/registrations.html')
            self.response.write(template.render(template_values))
        else:
            self.response.set_status(500)
            self.response.out.write('Student ID not found - ' + student_id)

class RegistrationWithImageListHandler(webapp2.RequestHandler):
    def get(self, student_id):
        if (get_student(student_id) is not None):
            registrations = get_registrations_with_image(student_id)

            template_values = {
                'student_id': student_id,
                'registrations': registrations
            }

            template = JINJA_ENVIRONMENT.get_template('registration/registrations-with-image.html')
            self.response.write(template.render(template_values))
        else:
            self.response.set_status(500)
            self.response.out.write('Student ID not found - ' + student_id)

class MarksHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())

    def post(self):
        student_id = self.request.get("student_id")
        assignment = self.request.get("assignment")

        logging.info(student_id)

        info_row = get_marks_from_google_sheet(student_id, assignment)

        if info_row is None:
            template_values = {
                'student_id': None,
            }
        else:
            template_values = {
                'student_id': info_row[0],
                'assignment': assignment,
                'comments': info_row[1],
                'mark': info_row[2],
                'q1': info_row[3],
                'q2': info_row[4],
                'q3': info_row[5],
            }

            if len(info_row) == 7:
                template_values['q4'] = info_row[6];

        template = JINJA_ENVIRONMENT.get_template('marks.html')
        self.response.write(template.render(template_values))

class ValidationKeyListHandler(webapp2.RequestHandler):
    def get(self, student_id):
        if (get_student(student_id) is not None):
            rows = get_rows_from_google_sheets('1D5jxK53uZhKHRQiO7usIyb_CxI6ca7gZXUFpYEhZSMY', 'Clean!E1:F')

            data = {}
            for r in rows:
                data[r[0]] = r[1]

            json_object = json.dumps(data);

            self.response.headers['Access-Control-Allow-Origin'] = '*'
            self.response.headers['Access-Control-Allow-Headers'] = '*'
            self.response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json_object)
        else:
            self.response.set_status(500)
            self.response.out.write('Student ID not found - ' + student_id)

class FormDemoHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('<h1>HTTP GET FROM class</h1>')
        self.response.out.write(self.request.GET)

        # # Check for specific parameter
        # param = self.request.get("student_id")
        # if (param):
        #     self.response.write('<h1 style="color:green">student_id = ' + param + '</h1>')
        # else:
        #     self.response.set_status(500)
        #     self.response.out.write('<h1 style="color:red">student_id is empty</h1>')

    def post(self):
        self.response.out.write('<h1>HTTP POST - From class</h1>')
        self.response.out.write(self.request.POST)

        # # Check for specific parameter
        # param = self.request.get("student_id")
        # if (param):
        #     self.response.write('<h1 style="color:green">student_id = ' + param + '</h1>')
        # else:
        #     self.response.set_status(500)
        #     self.response.out.write('<h1 style="color:red">student_id is empty</h1>')

class FormDemoAddHandler(webapp2.RequestHandler):
    def get(self, student_id):
        if (get_student(student_id) is not None):
            demo_records = get_demo_records(student_id)

            template_values = {
                'student_id': student_id,
                'demo_records': demo_records
            }

            template = JINJA_ENVIRONMENT.get_template('demo_records/records.html')
            self.response.write(template.render(template_values))
        else:
            self.response.set_status(500)
            self.response.out.write('Student ID not found - ' + student_id)

    def post(self):
        student_id = self.request.get('student_id')

        if (get_student(student_id) is not None):
            demo_record = str(self.request.POST)

            r = DemoRecord(student_id = student_id, demo_record = demo_record)
            k = r.put()

            logging.info(k)

            reg = {
                'student_id': student_id,
                'demo_record': demo_record
            }

            json_object = json.dumps(reg);

            logging.info(json_object)

            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json_object)
        else:
            self.response.set_status(500)
            self.response.out.write('Student ID not found - ' + student_id)

class ImageHandler(webapp2.RequestHandler):
    def get(self, registration_id):
        r = get_registration_with_image(registration_id)

        #self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(r.image)

app = webapp2.WSGIApplication([
    ('/import', ImportHandler),
    ('/marks', MarksHandler),
    ('/order', OrderHandler),
    ('/orders/(\d+)', OrderListHandler),
    ('/keys/(\d+)', ValidationKeyListHandler),
    # ('/keys/(\d+)', ValidationKeyHandler),
    ('/register', RegisterHandler),
    ('/registrations/(\d+)', RegistrationListHandler),
    ('/form_demo', FormDemoHandler),
    ('/demo', FormDemoAddHandler),
    ('/demos/(\d+)', FormDemoAddHandler),
    ('/register_with_image', RegisterWithImageHandler),
    ('/registrations_with_image/(\d+)', RegistrationWithImageListHandler),
    ('/image/(\d+)', ImageHandler),
    # ('/uploads/(\d+)/(\d+)', ImageListHandler), # student_id, registration_id GET registration
], debug=True)
