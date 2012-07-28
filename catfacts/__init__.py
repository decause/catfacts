import yaml
import json
from twilio.rest import TwilioRestClient
import twilio.twiml
from shove import Shove
from flask import Flask, request, abort
from random import choice


class CatFactsREST(object):

    def __init__(self, config):
        self.config = config
        dburi = self.config['dburi']
        self.db = Shove(dburi)
        self.app = Flask(__name__)
        self.twilio = TwilioRestClient(
                self.config['sid'],
                self.config['token'])
        if 'numbers' not in self.db:
            self.db['numbers'] = []
        if 'facts' not in self.db:
            print "No catfacts found, run catfacts load"
            exit()
        self.db.sync()


        self.routes = {
                "/api/numbers": (self.add_number, {"methods": ['POST']}),
                "/api/numbers/<num>": (self.remove_number, {"methods":
                    ['DELETE']}),
                "/api/callback": (self.twilio_callback, {"methods": ['GET']})}
        map(
                lambda route: self.app.route(
                    route,
                    **self.routes[route][1])(self.routes[route][0]),
                self.routes)


    def add_number(self):
        """
        POST: /api/numbers
        """
        try:
            data = json.loads(request.data)
        except:
            return json.dumps(dict(
                success=False,
                message="Invalid data recieved"))
        try:
            number = data['number']
            if number not in self.db['numbers']:
                self.db['numbers'].append(number)
                self.db.sync()
                self.twilio.sms.messages.create(
                to=number,
                body="Congrats, you have been signe dup for catfacts, the Premire cat information service, you will receive hourly cat information")
                return json.dumps(dict(
                    success=True,
                    message="Added {0} to catfacts".format(number)))
            else:
                return json.dumps(dict(
                    success=False,
                    message="{0} is already signe dup for catfacts".format(number)))

        except KeyError:
            return json.dumps(dict(
                success=False,
                message="Not Enough paramters"))

    def remove_number(self, num):
        """
        DELETE: /api/numbers/<number>
        """
        if num in self.db:
            self.db['numbers'].remove(num)
            self.db.sync()
            return json.dumps(dict(
                success=True,
                message="Removed {0} from catfacts".format(num)))
        else:
            return json.dumps(dict(
                success=False,
                message="{0} is not signed up for catfacts".format(num)))

    def twilio_callback(self):
        """
        POST: /api/callback
        """
        response = twilio.twiml.Response()
        response.sms(choice(self.db['facts']))
        return str(response)

    def start(self):
        self.app.run(
                host=self.config['host'],
                port=self.config['port'])


def main():
    from sys import argv
    config = yaml.load(file("/etc/catfacts.yaml").read())
    if argv[1] == "rest":
        cf = CatFactsREST(config)
        cf.start()
    elif argv[1] == "load":
        pass
    elif argv[1] == "cron":
        pass
