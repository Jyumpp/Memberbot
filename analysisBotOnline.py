import requests
import re
import sys
import time
from pprint import pprint
from flask import Flask
import socket
from time import time
from random import randint
# Global variable that stores the API token
at = ""
last_call = 0.0

####### Interact with user for necessary parameters for analysis

at = str('PtMTYlpfC75HoIZS3I9wUVEgkiayNX6h8MGFISAD')

application = Flask(__name__)

# Initial menu for fetching the API token and the desired group to be analyzed
def menu():
    print(print_all_groups_with_number_beside_each())
    global system_time
    system_time = int(time.time())
    global lookback_time
    global largest_likes
    largest_likes = 0
    global largest_name
    global at

    at = str('PtMTYlpfC75HoIZS3I9wUVEgkiayNX6h8MGFISAD')
    print(print_all_groups_with_number_beside_each())
    groups_data = print_all_groups_with_number_beside_each()
    try:
        group_number = 0
        group_id = get_group_id(groups_data, group_number)
        prepare_analysis_of_group(groups_data, group_id)
    except ValueError:
        print("Not a number")


# List all groups open to user
def print_all_groups_with_number_beside_each():
    response = requests.get('https://api.groupme.com/v3/groups?token=' + at)

    data = response.json()

    return data


####### Methods for getting group information

# Find the name of groups
def get_group_name(groups_data, group_id):
    return "MEMBERS ONLY"


# Find the ID of the selected group to proceed with analysis
def get_group_id(groups_data, group_number):
    group_id = groups_data['response'][group_number]['id']
    #fix
    return str(28539669)
    #return str(26698784)


def get_number_of_messages_in_group(groups_data, group_id):
    i = 0
    while True:
        if group_id == groups_data['response'][i]['group_id']:
            return groups_data['response'][i]['messages']['count']
        i += 1


def get_group_members(groups_data, group_id):
    i = 0
    while True:
        if group_id == groups_data['response'][i]['group_id']:
            return groups_data['response'][i]['members']
        i += 1


####### Analyzing group messages

# Fetching basic metrics of the group
def prepare_analysis_of_group(groups_data, group_id):
    # Return basic information of the group
    group_name = get_group_name(groups_data, group_id)
    number_of_messages = get_number_of_messages_in_group(groups_data, group_id)
    print("Analyzing " + str(number_of_messages) + " messages from " + group_name)
    # Map the users
    members_of_group_data = get_group_members(groups_data, group_id)
    user_dictionary = prepare_user_dictionary(members_of_group_data)
    # Analyze the group's messages
    user_id_mapped_to_user_data = analyze_group(group_id, user_dictionary, number_of_messages)
    # Return the data
    display_data(user_id_mapped_to_user_data)


# Map users
def prepare_user_dictionary(members_of_group_data):
    user_dictionary = {}
    i = 0
    while True:
        try:
            # Get information of the user
            user_id = members_of_group_data[i]['user_id']
            nickname = members_of_group_data[i]['nickname']
            user_dictionary[user_id] = [nickname, 0.0, 0.0, 0.0, 0.0, {}, {}, 0.0]
            # Optional metrics that can be measured for each user:
            # [0] = nickname, 
            # [1] = total messages sent in group, like count, 
            # [2] = likes per message,
            # [3] = average likes received per message, 
            # [4] = total words sent, 
            # [5] = dictionary of likes received from each member
            # [6] = dictionary of shared likes, 
            # [7] = total likes given

        except IndexError:
            return user_dictionary
        i += 1
    return user_dictionary


# Analyzing the messages
def analyze_group(group_id, user_id_mapped_to_user_data, number_of_messages):
    lookback_time = system_time - 86400

    response = requests.get('https://api.groupme.com/v3/groups/' + group_id + '/messages?token=' + at)
    data = response.json()
    message_with_only_alphanumeric_characters = ''
    message_id = 0
    iterations = 0.0
    while True:
        for i in range(20):  # in range of 20 because API sends 20 messages at once
            try:
                iterations += 1
                name = data['response']['messages'][i]['name']  # grabs name of sender
                message = data['response']['messages'][i]['text']  # grabs text of message
                time = data['response']['messages'][i]['created_at']
                # print(message)
                try:
                    #  strips out special characters
                    message_with_only_alphanumeric_characters = re.sub(r'\W+', ' ', str(message))
                except ValueError:
                    pass  # this is here to catch errors when there are special characters in the message e.g. emoticons
                sender_id = data['response']['messages'][i]['sender_id']  # grabs sender id
                list_of_favs = data['response']['messages'][i]['favorited_by']  # grabs list of who favorited message
                length_of_favs = len(list_of_favs)  # grabs number of users who liked message

                # grabs the number of words in message
                number_of_words_in_message = len(re.findall(r'\w+', str(message_with_only_alphanumeric_characters)))

                if sender_id not in user_id_mapped_to_user_data.keys():
                    user_id_mapped_to_user_data[sender_id] = [name, 0.0, 0.0, 0.0, 0.0, {}, {}, 0.0]

                # this if statement is here to fill the name in for the case where a user id liked a message but had
                # yet been added to the dictionary
                if user_id_mapped_to_user_data[sender_id][0] == '':
                    user_id_mapped_to_user_data[sender_id][0] = name

                for user_id in list_of_favs:
                    if user_id in user_id_mapped_to_user_data[sender_id][5].keys():
                        user_id_mapped_to_user_data[sender_id][5][user_id] += 1
                    else:
                        user_id_mapped_to_user_data[sender_id][5][user_id] = 1

                for user_id in list_of_favs:
                    for user_id_inner in list_of_favs:
                        if user_id not in user_id_mapped_to_user_data.keys():
                            # leave name blank because this means a user is has liked a message but has yet to be added
                            # to the dictionary. So leave the name blank until they send their first message.
                            user_id_mapped_to_user_data[user_id] = ['', 0.0, 0.0, 0.0, 0.0, {}, {}, 0.0]
                        if user_id == user_id_inner:
                            user_id_mapped_to_user_data[user_id][7] += 1
                            continue  # pass because you don't want to count yourself as sharing likes with yourself
                        try:
                            user_id_mapped_to_user_data[user_id][6][user_id_inner] += 1
                        except KeyError:
                            user_id_mapped_to_user_data[user_id][6][user_id_inner] = 1

                user_id_mapped_to_user_data[sender_id][1] += 1  # add one to sent message count
                if (lookback_time <= time):
                    user_id_mapped_to_user_data[sender_id][2] += length_of_favs
                user_id_mapped_to_user_data[sender_id][4] += number_of_words_in_message
                if (lookback_time > time):
                    return user_id_mapped_to_user_data
            except IndexError:
                print("COMPLETE")
                print
                for key in user_id_mapped_to_user_data:
                    try:
                        user_id_mapped_to_user_data[key][3] = user_id_mapped_to_user_data[key][2] / \
                                                              user_id_mapped_to_user_data[key][1]
                    except ZeroDivisionError:  # for the case where the user has sent 0 messages
                        user_id_mapped_to_user_data[key][3] = 0
                return user_id_mapped_to_user_data

        if i == 19:
            message_id = data['response']['messages'][i]['id']
            remaining = iterations / number_of_messages
            remaining *= 100
            remaining = round(remaining, 2)
            print(str(remaining) + ' percent done')

        payload = {'before_id': message_id}
        response = requests.get('https://api.groupme.com/v3/groups/' + group_id + '/messages?token=' + at,
                                params=payload)
        data = response.json()


####### Information rendering/parsing

def display_data(user_id_mapped_to_user_data):
    largest_likes = 0
    for key in user_id_mapped_to_user_data:
        print(user_id_mapped_to_user_data[key][0] + ' Data:')

        print('Total Likes Received: ' + str(user_id_mapped_to_user_data[key][2]))
        if (user_id_mapped_to_user_data[key][2] > largest_likes):
            largest_likes = user_id_mapped_to_user_data[key][2]
            largest_name = user_id_mapped_to_user_data[key][0]
        print
        print
    message = largest_name + " had the most likes today, with a total of " + '%g' % (largest_likes)
    if (largest_likes == 0):
        message = "Really? No one liked anything today?"
    print(message)
    urlSend = """{"text" : """"" + "\"" + message + """", "bot_id" : "b12f2d05467fc2e4724a03b5b8"}"""
    #requests.post("https://api.groupme.com/v3/bots/post", urlSend)
    print(urlSend)


# Uncomment this line below to view the raw dictionary
# pprint(user_id_mapped_to_user_data)

def print_to_groupme(text):
    #fix
    urlSend = """{"text" : """"" + "\"" + text + """", "bot_id" : "5910fc995b6c99f04fd368c820"}"""
    requests.post("https://api.groupme.com/v3/bots/post", urlSend)

def pic_to_groupme(text, image_url):
    #fix
    urlSend = """{"text" : """"" + "\"" + text + """", "bot_id" : "5910fc995b6c99f04fd368c820", "attachments" : [ { "type" : "image", "url" : """ +"\""+ image_url +"\"" + "}]}"
    print(urlSend)
    requests.post("https://api.groupme.com/v3/bots/post", urlSend)

def random_disco_url():
    urls = [
        "disco1",
        "disco2",
        "disco3",
        "disco4",
        "disco5",
        "disco6",
        "disco7",
        "disco8",
        "disco9",
        "disco10"
    ]
    return urls[randint(1,10)]

@application.route('/hello')
def hello():
    return "Hello World!"



@application.route('/memberbot', methods=['POST'])
def memberbot():
    global last_call
    response = requests.get('https://api.groupme.com/v3/groups/' + str(28539669) + '/messages?token=' + at,
                                params={'limit':1})
    data = response.json()

    message = data['response']['messages'][0]['text'].lower()

    if('memberbot' in message and time() >= 600 + last_call):
        print_to_groupme("Are you talking about me?")
        last_call = time()

    if(message[0:6] == '!disco'):
        pic_to_groupme(random_disco_url(), "https://i.groupme.com/700x490.jpeg.d244ccb563c946daace337da90a9def9")
    
    
    return response
print(last_call)
hostname = socket.gethostname()
IP = socket.gethostbyname(hostname)
application.run(host='localhost', port=8080, debug=True)


