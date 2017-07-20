import praw
import math
import os # This is used only to get the local directory of a file, nothing malicious.
import time
import random

subreddits = ["test"] # PUT SUBREDDITS IN HERE!!!

username = "USERNAME"
password = "PASSWORD"

cwd = os.getcwd()
try:
    words = open(cwd + r'\responses.txt', 'r')
except:
    print("Error loading responses file.")
lines = words.readlines()
words.close()
del words
try:
    words2 = open(cwd + r'\subject_list.txt', 'r')
except:
    print("Error loading subject list.")
subject_list = words2.readlines()
words2.close()
for x, line in enumerate(subject_list):
    line.replace('-', ' ')
    line.replace('_', ' ')
    line.replace('.', ' ')
    subject_list[x] = line
del words2
comment_total = 10
comment_skip = 37
if (comment_skip > 1):
    comment_skip = random.randint(comment_skip - 1, comment_skip + 1) # Gives a bit of randomness to skip so that repeated runnings with same skip will not place the same comment
largest_subject = len(max(subject_list, key=len))

def binary_search(search_item): # This is used to check through the subject_list document to help get the subject of a comment
    start_point = 0
    end_point = len(subject_list) - 1
    for y in range(0, int(round(math.log(len(subject_list), 2))) + 1): # This calculates the maximum possible iterations it would take to find a word, if it gets past that the search has failed.
        midpoint = (start_point + end_point)//2 # Calculates the midpoint as an integer
        current_subject = subject_list[midpoint].strip('\n')
        for x in range(0, min(len(search_item), len(current_subject))): # Moves through each character in word comparing to search term, many words will have similar matching characters at the beggining
            if (current_subject[x] != search_item[x]): # Checks if word has been found at current midpoint
                if(ord(search_item[x]) < ord(current_subject[x])):
                    end_point = midpoint - 1
                else:
                    start_point = midpoint + 1
                break # Stops the current search at this word as a match has not been found and there's no point continuing
            elif (x == min(len(search_item), len(current_subject)) - 1): # If the search gets to the end of the word then we know it has found the right term
                if (len(current_subject) > len(search_item)): # If the midpoint is on a word longer than the search_item it will move the end point below because that's the solution to the problem
                    end_point = midpoint - 1
                elif (len(current_subject) < len(search_item)):
                    start_point = midpoint + 1
                else:
                    return True
    return False

def check_for_nouns(words):
    # Goes throug every word and checks from back of list, this confuses me i don't know how i made it and somehow it works
    # ¯\_(ツ)_/¯
    matches = []
    for x, word in enumerate(words): # Goes through every word
        word_ranges = []
        current_word_range = word
        word_ranges.append(current_word_range)
        i = 1
        while (x + i < len(words)) and (len(current_word_range + words[x + i]) + 1 <= largest_subject):
            current_word_range = ' ' + words[x + i]
            word_ranges.append(current_word_range)
            i += 1
            
        for word_range in reversed(word_ranges):
            if (binary_search(word_range) == True):
                matches.append(word_range)
                break
            
    if (len(matches) > 0):
        return max(matches, key=len)
    else:
        return "that"

def replace_character(output_text, comment, format_point, subject): # Replaces formatting tags with their correct replacement
    first_half = output_text[:(format_point - 1)]
    second_half = output_text[(format_point + 2):]
    replacement = ""
    if (output_text[format_point] == 'u'):
        temp_word = comment.author.name.lower()
        for i, char in enumerate(temp_word): # Makes it so when a user name is stated no symbols are included and it is all lower case to make it seem more natural, the name is also cut of where a second part is included.
            if (96 < ord(char) < 123): # Only adds word if it is a letter in the alphabet
                replacement += char
            elif (replacement != ""):
                if (i < len(temp_word) - 1) and (ord(temp_word[i + 1]) > 96) and (ord(temp_word[i + 1]) < 123): # Checks if there is a letter in the next character, these avoid cutting of names with letters replaced with numbers and letters with underscores
                    replacement += char
                else:
                    break
    elif (output_text[format_point] == 's'):
        replacement = subject
    else:
        replacement = "ERROR WITH FORMATTING TAG REPLACEMENT - UNRECOGNISED TAG [" + output_text[format_point] + "]."
    output_text = first_half + replacement + second_half
    return output_text

def split_words(text): # Splits up words
    text.strip('\n')
    words = []
    start_writing = False
    current_word = ""
    for char in text:
        if (start_writing == False): # Starts writing once there are characters
            if (97 <= ord(char) <= 122) or (48 <= ord(char) <= 57):
                start_writing = True
                current_word += char
        else: # Stops writing once the end of a word is reached and that word is added to the list
            if (97 <= ord(char) <= 122) or (48 <= ord(char) <= 57) or (char == '\'') or (char == '/'): 
                current_word += char
            else:
                start_writing = False
                words.append(current_word)
                current_word = ""
    if (current_word != ""): # Adds the current_word if not already done
        words.append(current_word)
    return words

def matching_keywords(keywords, words, comment_body):
    for keyword in keywords:
        if (' ' in keyword): # If the keyword is longer than one word it just checks if that phrase is in the word
            if (keyword not in comment_body):
                return False
        else:
            for word in words:
                if (word != keyword):
                    return False
    return True

def generate_response(comment, is_reply): # Generates a response based on context
    global random
    question_trigger_words = ["how", "why", "what", "when"] # Words to look for in parent comment that will make it a question
    personal_trigger_words = ["i", "im", "i'm", "feel", "am"]
    directed_trigger_words = ["you", "are", "you're", "youre", "your"]
    phrases = []
    words = split_words(comment.body.lower()) # generates a list of individual words that is used for various things, all lower case
    is_question = False
    is_personal = False
    is_directed = False
    for word in words: # Checks if comment is a question, personal or directed
        for parameter in personal_trigger_words:
            if (word == parameter):
                is_personal = True
                break
        for parameter in directed_trigger_words:
            if (word == parameter):
                is_directed = True
                break
        for parameter in question_trigger_words:
            if (word == parameter):
                is_question = True
                break
    subject = check_for_nouns(words) # Gets the subject of the sentence
    for line in lines: # Generates a list of phrases that can be used and selected from given the context
        if (line[0] == '%'): # Stop if % sign found
            break
        if (line[0] != '~'): # Ignore line if ~ sign found
            parameters_raw = ""
            parameter_sets = []
            phrase = ""
            main_text = False
            parameters = ""
            for char in line: # This splits the parameters from the phrase and puts the invidual parameter sets (for OR logic)into a list called parameter_sets
                if (main_text == False):
                    if (char == '|'):
                        main_text = True
                        parameter_sets.append(parameters)
                        del parameters
                        del parameters_raw
                    elif (char == '/'):
                        parameter_sets.append(parameters)
                        parameters = ""
                    else:
                        parameters += char
                else:
                    phrase += char
            del main_text
            keywords = []
            got_keyword = False
            keyword = ""
            start_x = 0

            skip = True # This has to be used as a line needs to be skipped, but the point at which this is decided is inside another for loop, so a boolean must be used to store the outcome
            for parameters in parameter_sets:
                for x, char in enumerate(parameters): # Gets keywords and removes them from parameters
                    if (got_keyword == False):
                        if (char == '\"'):
                            start_x = x
                            got_keyword = True
                    else:
                        if (char == '\"'):
                            got_keyword = False
                            parameters = parameters[:start_x] + parameters[(x + 1):]
                            keywords.append(keyword.lower())
                            keyword = ""
                        else:
                            keyword += char
                del got_keyword
                del start_x
                del keyword
                if (is_reply) != ('.' in parameters): # Goes through parameters and skips iteration if they don't match, preventing the line from being added, somehow it works
                    continue
                elif (is_question) != ('?' in parameters):
                    continue
                elif (is_personal) != ('p' in parameters):
                    continue
                elif (is_directed) != ('d' in parameters):
                    continue
                elif (subject == "that") and ('s' in parameters): # The s parameter works differently to the others, any phrase with s will only be used if a subject exists in the parent
                    continue
                elif (len(keywords) > 0) and (matching_keywords(keywords, words, comment.body) == False): # Like with s, keywords are not exlucsive and other phrases without keywords can be used
                    continue
                skip = False
                break
            if (skip == False):
                phrases.append(phrase)
            else:
                continue
    if (len(phrases) > 0):
        output_text = random.choice(phrases) # Selects phrase to use randomely out of phrases
    else:
        return ""
    x = 0
    while x < len(output_text): # Replaces characters and chooses random phrases
        if (output_text[x] == '{'):
            choices = []
            choice = "" # This is used for two reasons, temporary and other temporary thing
            for i in range(x + 1, len(output_text)): 
                char2 = output_text[i]
                if (char2 == '}'):
                    choices.append(choice)
                    choice = random.choice(choices)
                    output_text = output_text[:x] + choice + output_text[i + 1:]
                    break
                elif (char2 == '/'):
                    choices.append(choice)
                    choice = ""
                else:
                    choice += char2
        elif (output_text[x] == '[') and (x < len(output_text) - 2) and (output_text[x + 2] == ']'): # This is what checks if there are actually characters present without checking the middle char.
            output_text = replace_character(output_text, comment, x + 1, subject)
        x += 1
    del x
    output_text = output_text.rstrip() # Removes whitespace to the right which just seem to be added on for i don't know why
    return output_text

def attempt_comments(comments):
    actual_coms = 0
    for coms, comment in enumerate(comments, 1): # Move through each comment in subreddit
        for x in reversed(range(0, coms + 1)):
            if (int(coms) % int(comment_skip) == 0) and comment.author.name != username:
                reply = generate_response(comment, False)       
                if(reply != ""):
                    print("        Attempting Comment...")
                    try:
                        comment.reply(reply)
                    except praw.errors.RateLimitExceeded:
                        print("This account has exceeded its maximum amount of comments in a time on /r/" + subreddit_name + ", terminating commenting on this sub.")
                        return actual_coms
                    else:
                        print("        Commented.")
                        actual_coms += 1
                        break
    return actual_coms

def run_program():
    global subreddits
    r = praw.Reddit(user_agent = "Hola, mi llamo es señor Cielos Azules")
    print("Connecting to Reddit...")
    while True:
        try:
            r.login(username, password, disable_warning=True)
        except praw.errors.InvalidUserPass:
            print("Error trying to login, check Username and Password.")
        except:
            print("Error trying to connect to Reddit")
        else:
            print("Connected.")
            break
        print("Trying again...")
        time.sleep(1)
    if (comment_total > 0):
        for subreddit_name in subreddits: # Moves through subreddits to comment on
            print("Getting /r/" + subreddit_name + " information...")
            subreddit = r.get_subreddit(subreddit_name)
            
            print("Getting comment information...")
            comments = subreddit.get_comments(limit=(comment_total*comment_skip))
            
            print("Starting automated commenting system...")
            
            print("    Repying to thread comments...")

            actual_comments = attempt_comments(comments) # This is where the comments are actually made
                
            print("    " + str(actual_coms) + " comments have been made in /r/" + subreddit_name + ".")
            print(" ")
    else:
        print("Skipping commenting.")
    actual_coms = 0
    print("")
    print("Getting inbox information...")
    inbox = r.get_unread()
    print("    Looking at inbox...")
    replied = False
    for coms, comment in enumerate(inbox): # Replies to comments
        reply = generate_response(comment, True)
        if (reply == ""):
            continue
        else:
            try:
                comment.reply(reply)
                replied = True # This keeps track of unread messages that have attempted to be replied to so that it can be stated if there are not any to reply to.
            except praw.errors.RateLimitExceeded:
                print("        Tried to reply to a comment but cannot in this subreddit as the maximum number of comments has been exceeded.")
            else:
                print("        Replied to inbox comment.")
                comment.mark_as_read()
                actual_coms += 1
        print("")
    if (replied == False):
        print("    There are no unread messages in the inbox.")
    print("Completed Program...")

# By Dom Newman (dont hurt me)
run_program()
