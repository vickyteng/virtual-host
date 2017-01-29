"""
This is the Alexa Virtual Host Skill.
"""

from __future__ import print_function
import random
import boto3
from boto3.dynamodb.conditions import Key, Attr
import pycurl
import urllib
import json
import StringIO


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_link_account_response(output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'LinkAccount',
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome! I am your virtual host for today. " \
                    "Please ask me questions by saying, " \
                    "what are the house rules or where is the bathroom?"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please ask me questions by saying, " \
                    "what are the house rules or where is the bathroom?"
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using the Virtual Host. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def find_the_object(intent, session):
    card_title = intent['name']
    session_attributes = {}
    reprompt_text = None
    speech_output = ""
    should_end_session = True
    
    email = get_user_info(intent, session)
    
    if email == "":
        speech_output = "To start using this skill please use the website " \
                    "to authenticate on Amazon. "
        return build_response(session_attributes, build_link_account_response(
            speech_output, reprompt_text, should_end_session))
    elif 'Item' in intent['slots']:
        print("EMAIL")
        print(email)

        if 'value' in intent['slots']['Item']:
            object_requested = intent['slots']['Item']['value']
        else:
            object_requested = "does not exist"
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('HouseItems')
        
        response = table.get_item(
            Key={
                'name': object_requested,
                'information': object_requested
            }
        )

        try:
            location = response['Item']['detail1']
            speech_output = location
            should_end_session = True
        except KeyError:
            speech_output = "Either it has not been listed yet or it does not exist."
            should_end_session = True
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('HouseItems')
            
            response = table.put_item(
                Item={
                    'name': object_requested,
                    'information': object_requested,
                    'detail1': 'Either it has not been listed yet or it does not exist.'
                }
            )
            
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_house_rules(intent, session):
    card_title = intent['name']
    session_attributes = {}
    reprompt_text = None
    speech_output = "test"
    should_end_session = True
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('HouseItems')
    
    response = table.get_item(
        Key={
            'name': 'house rules',
            'information': 'house rules'
        }
    )

    try:
        location = response['Item']['detail1']
        speech_output = location
        should_end_session = True
    except KeyError:
        speech_output = "Either it has not been listed yet or it does not exist."
        should_end_session = True
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_user_info(intent, session):
    session_attributes = {}
    reprompt_text = None
    speech_output = "the test"
    should_end_session = True
    
    try:
        access_token = session['user']['accessToken']
        card_title = intent['name']
        speech_output = "success"
        
        b = StringIO.StringIO()
        
        c = pycurl.Curl()
        c.setopt(pycurl.URL, "https://api.amazon.com/user/profile")
        c.setopt(pycurl.URL, "https://api.amazon.com/auth/o2/tokeninfo?access_token=" + urllib.quote_plus(access_token))
        c.setopt(pycurl.SSL_VERIFYPEER, 1)
        c.setopt(pycurl.WRITEFUNCTION, b.write)
        
        c.perform()
        d = json.loads(b.getvalue())
        
        if d['aud'] != 'amzn1.application-oa2-client.54af438d459f4b9a991a6412abde7826' :
            # the access token does not belong to us
            raise BaseException("Invalid Token")
        
        # exchange the access token for user profile
        b = StringIO.StringIO()

        c = pycurl.Curl()
        c.setopt(pycurl.URL, "https://api.amazon.com/user/profile")
        bearer = "Authorization: bearer " + access_token
        c.setopt(pycurl.HTTPHEADER, [str(bearer)])
        c.setopt(pycurl.SSL_VERIFYPEER, 1)
        c.setopt(pycurl.WRITEFUNCTION, b.write)
        
        c.perform()
        d = json.loads(b.getvalue())
        
        # print("THE MOMENT OF TRUTH")
        # print (d['name'])
        # print (d['email'])
        # print (d['user_id'])
        # speech_output = "Your name is " + d['name'] + " and your email address is " + d['email']
        
        # return build_response(session_attributes, build_speechlet_response(
        #     card_title, speech_output, reprompt_text, should_end_session))
        email = d['email']
        
        return email
    except KeyError:
        # speech_output = "To start using this skill please use the website " \
        #             "to authenticate on Amazon. "
        # return build_response(session_attributes, build_link_account_response(
        #     speech_output, reprompt_text, should_end_session))
        return ""
        
def get_host_info(intent, session):
    card_title = intent['name']
    session_attributes = {}
    reprompt_text = None
    speech_output = ""
    should_end_session = True
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('HouseItems')
    
    response = table.get_item(
        Key={
            'name': 'Contact Information',
            'information': 'Contact Information'
        }
    )
    
    if len(intent['slots']['Contact']) == 2:
        arr = str.split(str(intent['slots']['Contact']['value']))
    
    # print ("information")
    # print (arr)
    # print (len(arr))

    if len(intent['slots']['Contact']) == 1 or 'name' in arr:
        try:
            host_name = response['Item']['HostName']
            speech_output += "The name of the host is " + host_name + ". "
            print ("IT WORKS")
            print (host_name)
            print ("speech_output")
            print (speech_output)
        except KeyError:
            speech_output += "The host name is not found."
            print ("IT DOESN'T WORK")

    if len(intent['slots']['Contact']) == 1 or 'email' in arr:
        try:
            email = response['Item']['Email']
            speech_output += "The host's email is " + email + ". "
        except KeyError:
            speech_output += "The host email is not found."
        
    if len(intent['slots']['Contact']) == 1 or 'phone' in arr:
        try:
            phone_number = response['Item']['Phone']
            speech_output += "The host's phone number is " + phone_number + ". "
        except KeyError:
            speech_output += "The host phone number is not found."
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "IAmTheGuestIntent":
        return get_welcome_response()
    elif intent_name == "WhereIsObjectIntent":
        return find_the_object(intent, session)
    elif intent_name == "HouseRulesIntent":
        return get_house_rules(intent, session)
    elif intent_name == "GetUserCredentialsIntent":
        return get_user_info(intent, session)
    elif intent_name == "GetHostContactInfo":
        return get_host_info(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
