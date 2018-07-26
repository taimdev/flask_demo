#!/usr/bin/python3

# written by Taimur Azhar z5116684 finished 30/10/2017
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

# Import all necessary libraries and functions
import os, sqlite3, re, datetime, jinja2
from flask import Flask, render_template, session, redirect, url_for, request
from time import gmtime, strftime

# Set this dir, to whatever it is being run on
students_dir = "dataset-small";

# Start the Flask app
app = Flask(__name__)

# The initial page, which asks the user to login
@app.route('/', methods=['GET'])
def start():
    # Return the login page
    return render_template("login.html")

# The search page, takes in the query and return the template with the query
@app.route('/search', methods=['GET','POST'])
def search():
    # Return to the first page, if a user is not logged in
    if 'zid' not in session:
        return redirect('')
    # Pull the search request
    search_req = request.form.get('search', '')
    # Return the search page, with the query
    return render_template("search.html", search_query=search_req)

# login page which redirects to home page if login works
# or returns the login page again with the suitable error    
@app.route("/login", methods=['POST'])
def login():
    # Pull the username and password entered from the form
    login_zid = request.form.get('zid', '')
    password = request.form.get('password', '')
    # Pull information about the given student from the database while checkign existence
    stu_details = read_student_details(login_zid)

    # If the function returns a value, then the student exists
    if (stu_details):
        # if the password equals the password field
        if (password == stu_details[6]):
            # User is legit so put it into session
            session['zid'] = login_zid
            # If it works redirect to the home page
            return redirect('home')
        else:
            # wrong password
            return "Try again wrong password <br>" + render_template('login.html')
    else:
        # student doesnt exist
        return "That username does not exist sorry <br>" + render_template('login.html')

# Logout page
@app.route("/logout", methods=['POST'])
def logout():
    # Clear the session and redirect to the initial page
    session.clear()
    return redirect('')

# Render a form to accept data for a new user
@app.route("/new_user", methods=['POST', "Get"])
def new_user():
    return render_template("new_user.html")

# Pull the data, and then create a user with the data given
@app.route("/create_user", methods=['POST', 'GET'])
def create_user():
    # Pull all the data from the forms
    # If a value is not given, return an empty string
    zID = request.form.get('zID', '')
    Name = request.form.get('Name', '')
    Email = request.form.get('Email', '')
    Suburb = request.form.get('Suburb', '')
    Longitude = request.form.get('Longitude', '')
    Latitude = request.form.get('Latitude', '')
    Program = request.form.get('Program', '')
    Birthday = request.form.get('Birthday', '')
    Password = request.form.get('Password', '')
    Courses = request.form.get('Courses', '')

    # Connect the databse
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    # Get all the users
    cursor.execute(''' SELECT zid FROM users ''')
    # This is all the users
    users = cursor.fetchall()

    # These are the compulsory fields
    if zID == '' or Name == '' or Email == '' or Password == '':
        return render_template("create_user.html", msg="zID, Name, Email and Password have to be filled in")
    # Make sure the zID matches the standards
    if not re.search('^z\d{7}$', zID):
        return render_template("create_user.html", msg="Invalid zID")
    # Make sure the user does not already exist
    for entry in users:
        if (zID in entry):
            return render_template("create_user.html", msg="zID already exists")
    # Email has to be of the type Something@Somewhere.Somewhere
    if not re.search('.+?@.+?\..+?', Email):
        return render_template("create_user.html", msg="Email is not valid")
    # Password cannot be empty
    if Password == '':
        return render_template("create_user.html", msg="Enter a valid password")
    # Add the brackets around the courses
    Courses = re.sub('$', ')', Courses)
    Courses = re.sub('^', '(', Courses)
    #print(zID, Name, Email, Suburb, Longitude, Latitude, Password, Program, Birthday, Courses, None, None)
    # Add the user to the database
    cursor.execute('''INSERT INTO users(zid, name, email,suburb, hlong, hlat, password, program, birthday, courses, friends, dp_link)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(zID, Name, Email, Suburb, Longitude, Latitude, Password, Program, Birthday, Courses, None, None))
    stu_db.commit()
    return render_template("create_user.html", msg="User has been created, Log In")

# Home page which has the latest posts
@app.route("/home")
def home():
    # Return to the first page, if a user is not logged in
    if 'zid' not in session:
        return redirect('')
    posts_by_friends = friends_posts(session['zid'])
    return render_template("home.html", posts_by_friends=posts_by_friends)

# Unfriending Page
@app.route("/unfriend", methods=['POST'])
def unfriend():
    # Return to the first page, if a user is not logged in
    if 'zid' not in session:
        return redirect('')
    # Get the zID of the person whose page we are on
    profile_zid = request.form.get('profile_zid')
    # Get the databse
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT friends FROM users WHERE zid = ? or zid = ?''',(session['zid'], profile_zid))
    # This array contains the friends list of both the logged in user and user whose page we were on
    friends_rows = cursor.fetchall()

    # Turn the string into an array
    friend1 = re.sub(r'\(','',friends_rows[0][0])
    friend1 = re.sub(r'\)','',friend1)
    friend_list1 = re.split(', ',friend1)
    # Turn the string into an array
    friend2 = re.sub(r'\(','',friends_rows[1][0])
    friend2 = re.sub(r'\)','',friend2)
    friend_list2 = re.split(', ',friend2)

    try:
        # If removing the logged in user works, then this is the friend list of the page user
        friend_list1.remove(session['zid'])
        # Make the array a string again
        other_user = ", ".join(friend_list1)
    except:
        # Else this is the friend list of the logged in user
        friend_list1.remove(profile_zid)
        # Make the array a string again
        curr_user = ", ".join(friend_list1)

    try:
        # If removing the logged in user works, then this is the friend list of the page user
        friend_list2.remove(session['zid'])
        # Make the array a string again
        other_user = ", ".join(friend_list2)
    except:
        # Else this is the friend list of the logged in user
        friend_list2.remove(profile_zid)
        # Make the array a string again
        curr_user = ", ".join(friend_list2)

    # Touch ups on the string you have created
    curr_user = re.sub(r'$', ")", curr_user)
    curr_user = re.sub(r'^', "(", curr_user)
    other_user = re.sub(r'$', ")", other_user)
    other_user = re.sub(r'^', "(", other_user)

    # Commit the changes
    cursor.execute('''UPDATE users SET friends = ? WHERE zid = ? ''', (curr_user, session['zid']))
    cursor.execute('''UPDATE users SET friends = ? WHERE zid = ? ''', (other_user, profile_zid))
    stu_db.commit()

    return redirect(request.referrer)

# Friending Page
@app.route("/friend", methods=['POST'])
def friend():
    # Return to the first page, if a user is not logged in
    if 'zid' not in session:
        return redirect('')

    # Get the zID of the person whose page we are on
    profile_zid = request.form.get('profile_zid')
    # Connect the database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    # This is the array of the logged in user
    cursor.execute(''' SELECT friends FROM users WHERE zid = ? ''',(session['zid'],))
    friends_row1 = cursor.fetchone()
    # This is the array of the user whose page we are on
    cursor.execute(''' SELECT friends FROM users WHERE zid = ? ''',(profile_zid,))
    friends_row2 = cursor.fetchone()

    # If the logged user has no friends, then just just insert the friend into the string
    if (friends_row1[0] == None):
        curr_user = "({})".format(profile_zid)
    else:
        # Create a string from the array
        friend1 = re.sub(r'\(','',friends_row1[0])
        friend1 = re.sub(r'\)','',friend1)
        friend_list1 = re.split(', ',friend1)
        # Add the friend to the array
        friend_list1.append(profile_zid)
        # Convert back into a string
        curr_user = ", ".join(friend_list1)
        curr_user = re.sub(r'$', ")", curr_user)
        curr_user = re.sub(r'^', "(", curr_user)

    # If the user whose page we on has no friends, then just just insert the logged in user into the string
    if (friends_row2[0] == None):
        other_user = "({})".format(session['zid'])
    else:
        # Create a string from the array
        friend2 = re.sub(r'\(','',friends_row2[0])
        friend2 = re.sub(r'\)','',friend2)
        friend_list2 = re.split(', ',friend2)   
        # Add the friend to the array     
        friend_list2.append(session['zid'])
        # Convert back into a string
        other_user = ", ".join(friend_list2)
        other_user = re.sub(r'$', ")", other_user)
        other_user = re.sub(r'^', "(", other_user)

    # Commit changes
    cursor.execute('''UPDATE users SET friends = ? WHERE zid = ? ''', (curr_user, session['zid']))
    cursor.execute('''UPDATE users SET friends = ? WHERE zid = ? ''', (other_user, profile_zid))
    stu_db.commit()

    return redirect(request.referrer)

# The function for the profile page. The defualt profile is that of the logged in user
@app.route("/profile")
@app.route("/profile/<student_id>")
def profile(student_id=None):
    # Return to the first page, if a user is not logged in
    if 'zid' not in session:
        return redirect('')
    # If a profile is not specified, then the current user is the logged user
    if not student_id:
        student_id = session['zid']
        # Going to trigger the page with options
        control = 1
    elif student_id == session['zid']:
        # Case where the person is accessing their profile through url
        control = 1
    else:
        # Do not allow user only priveleges
        control = 0

    # Pull the details of the student whose page is being requested
    stu_details = read_student_details(student_id)
    # If the student actually exists pull other data
    if (stu_details):      
        # Pull the posts of the student whose page is being requested
        post_details = read_student_posts(student_id)
        # Pull the comments of the student whose page is being requested
        comment_details = read_student_comments(student_id)
        # Pull the replies of the student whose page is being requested
        reply_details = read_student_replies(student_id)
        # Return a list of the persons friends
        friend_list = read_student_friends(student_id)
        #print(post_details)
    else:
        return render_template('error.html', error_msg = "User does not exist")

    return render_template('profile.html', profile_details=stu_details, post_details=post_details,
    comment_details=comment_details, reply_details=reply_details, friend_list=friend_list, control=control, curr_user = session['zid'])

# Function for new posts
@app.route("/make_post", methods=['GET','POST'])
def make_post():
    # Return to the first page, if a user is not logged in
    if 'zid' not in session:
        return redirect('')
    # Get the message from the form
    post_msg = request.form.get('post_msg_form')
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    # Find out how many posts have been made so far
    cursor.execute(''' SELECT post_id FROM posts WHERE p_zid = ? ORDER BY post_id DESC''', (session['zid'],))
    # This should be the number of posts
    num_posts = cursor.fetchone()
    # If posts is None, it means that person has not made a post yet, so initialise a post array where the post num is zero
    if (num_posts == None):
        num_posts = [0,0]
    # Push the changes
    cursor.execute('''INSERT INTO posts(p_zid, message, from_zid, ptime, plong, plat, post_id)
                      VALUES(?,?,?,?,?,?,?)''',(session['zid'], post_msg, session['zid'], 
                        strftime("%Y-%m-%d %H:%M:%S"), None, None, num_posts[0] + 1))
    stu_db.commit()
    return redirect(request.referrer)

# Function for new comments 
@app.route("/make_comment", methods=['GET','POST'])
def make_comment():
    # Return to the first page, if a user is not logged in
    if 'zid' not in session:
        return redirect('')
    # Get the message from the form
    comment_msg = request.form.get('comment_msg_form')
    # Also retrieve the details of the post being commented on
    p_zid = request.form.get("student_post")
    post_id = request.form.get("post_number")
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    # Find out how many posts have been made so far
    cursor.execute(''' SELECT comment_id FROM comments WHERE p_zid = ? AND post_id = ? ORDER BY comment_id DESC''', (p_zid, post_id))
    # This should be the number of posts
    num_comments = cursor.fetchone()
    # If comments is None, it means that there has not been a comment on the post yet, so set the count as zero
    if (num_comments == None):
        num_comments = [0,0]

    # Push the changes
    cursor.execute('''INSERT INTO comments(p_zid, message, from_zid, ptime, post_id, comment_id)
                      VALUES(?,?,?,?,?,?)''',(p_zid, comment_msg, session['zid'], 
                        strftime("%Y-%m-%d %H:%M:%S"), post_id, num_comments[0] + 1))
    stu_db.commit()
    return redirect(request.referrer)

# Function for new replies
@app.route("/make_reply", methods=['GET','POST'])
def make_reply():
    # Return to the first page, if a user is not logged in
    if 'zid' not in session:
        return redirect('')
    # Get the message from the form
    reply_msg = request.form.get('reply_msg_form')
    # Also retrieve information about the post and comment being replied to
    p_zid = request.form.get("student_post")
    post_id = request.form.get("post_number")
    comment_id = request.form.get("comment_number")
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    # Find out how many posts have been made so far
    cursor.execute(''' SELECT reply_id FROM replies WHERE p_zid = ? AND post_id = ? AND comment_id = ? ORDER BY comment_id DESC''', (p_zid, post_id, comment_id))
    # This should be the number of posts
    num_replies = cursor.fetchone()
    # If replies  is None, it means that there has not been a reply on the post/comment yet, so set the count as zero
    if (num_replies == None):
        num_replies = [0,0]
    # Push the changes
    cursor.execute('''INSERT INTO replies(p_zid, message, from_zid, ptime, post_id, comment_id, reply_id)
                      VALUES(?,?,?,?,?,?,?)''',(p_zid, reply_msg, session['zid'], 
                        strftime("%Y-%m-%d %H:%M:%S"), post_id, comment_id, num_replies[0] + 1))
    stu_db.commit()
    return redirect(request.referrer)

# Convert any \n in the code to a <br>
@app.template_filter('newline_to_break')
def newline_to_break(original):
    if (original != None):
        # If the message exists replace the space characters
        original = jinja2.Markup(original.replace('\\n', '</br>'))
        original = jinja2.Markup(original.replace('\\r', '</br>'))
    return original

# Function to return the details of the requested zid
def read_student_details(zid_request):
    # Connect the database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT * FROM users''')
    # Returns a table of all the information of all the users
    users_rows = cursor.fetchall()
    # If the zid matches one in the database, return its row of data
    for details in users_rows:
        if (zid_request == details[0]):
            return details
    # If the user was not found return None
    return None

# Function to return all the posts on the "wall" of a certain person
def read_student_posts(zid_request):
    # Connect the database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT * FROM posts WHERE p_zid = ? ORDER BY ptime DESC''', (zid_request,))
    # Returns all the post information in reverse order where the zid matches
    post_rows = cursor.fetchall()
    # If the zid matches one in the databse, return its row of data
    return post_rows

# Function to return all the comments on the "wall" of a certain person
def read_student_comments(zid_request):
    # Connect the database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT * FROM comments WHERE p_zid = ? ORDER BY ptime ASC''', (zid_request,))
    # Returns all the comment information in normal order where the zid matches
    comment_rows = cursor.fetchall()
    # If the zid matches one in the databse, return its row of data
    return comment_rows

# Function to return all the replies on the "wall" of a certain person
def read_student_replies(zid_request):
    # Connect the database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT * FROM replies WHERE p_zid = ?ORDER BY ptime ASC''', (zid_request,))
    # Returns all the reply information in normal order where the zid matches
    reply_rows = cursor.fetchall()
    # If the zid matches one in the databse, return its row of data
    return reply_rows

# Function which returns an array of the friends of the given zid
def read_student_friends(zid_request):
    # Connect the database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT friends FROM users WHERE zid = ?''', (zid_request,))
    # Selecting the friends field where zid matches
    reply_rows = cursor.fetchone()
    # If the zid matches one in the databse, return its row of data
    if (reply_rows[0] != None):
        # Turn it into an array
        friend_str = re.sub(r'\(','',reply_rows[0])
        friend_str = re.sub(r'\)','',friend_str)
        friend_list = re.split(', ',friend_str)
    else:
        # Return an empty array if no friends
        friend_list = []
    return friend_list

# Function which returns the name of a zid
def zid_to_name(zid_request):
    # Connect the database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT name FROM users WHERE zid = ?''', (zid_request,))
    # Retrieve just the name, where the zid matches
    name = cursor.fetchone()
    try:
        return name[0]
    except:
        # If a name doesnt get registered, return the zid
        return zid_request

# Function converts a message's zid's into names with links
def message_conversion(message):
    # Connect the database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT zid FROM users''')
    # A list of all the zids
    zids = cursor.fetchall()
    # Set the final message to the given msg
    final_msg = message
    # Each zid in the databse
    for zid in zids:
        # If the zid is found
        if (final_msg != None):
            if re.search(zid[0], final_msg):
                # Recover the name associated to the zid
                name = zid_to_name(zid[0])
                # Replace the zid with the link to the name
                url_part = url_for("profile", student_id = zid[0])
                final_msg = re.sub(zid[0], '''<a href = '{}'> {} </a>'''.format(url_part, name), final_msg)
        else:
            return final_msg
    return final_msg

# Function coverts the date text format into a datetime format
def date_conversion(date):
    # date format 2016-10-05T14:37:05+0000
    # date format YYYY-MM-DD HH:MM:SS
    date_arr = list(date)
    year = int(''.join(date_arr[0:4]))
    month = int(''.join(date_arr[5:7]))
    day = int(''.join(date_arr[8:10]))
    hour = int(''.join(date_arr[11:13]))
    minute = int(''.join(date_arr[14:16]))
    second = int(''.join(date_arr[17:19]))
    converted_date = datetime.datetime(year, month, day, hour, minute, second)
    return converted_date
#print(date_conversion("2016-10-05T14:37:05+0000"))

# Function which returns the link of the dp of the given person, and is also a link
def dp_url(zid):
    # Get the details from an above function
    user_details = read_student_details(zid)
    # If the details exist, and there is a image link provided
    if (user_details != None and user_details[11] != None):
        # Link to their profile
        link_url = url_for('profile', student_id=zid)
        # Link to their dp
        img_url = url_for('static', filename=user_details[11])
        # Combine the two into one link
        img_link = '''<a href="{}"> 
                    <img src="{}" alt="{}" width="80" height="80"> </a>'''.format(link_url, img_url, zid_to_name(zid))
        return img_link
    else:
        # Link to their profile
        link_url = url_for('profile', student_id=zid)
        # Link to their dp which is a defualt doggo photo
        img_url = url_for('static', filename='doggo.jpg')
        # Combine the two into one link
        img_link = '''<a href="{}"> 
                    <img src="{}" alt="{}" width="80" height="80"> </a>'''.format(link_url, img_url, zid_to_name(zid))
        return img_link

# Function which returns all the users which match a search request
def search_users(query):
    # Connect the database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT * FROM users''')
    # All the information
    users_rows = cursor.fetchall()
    toggle = 0
    # The list which contains the final results
    q_results = []
    # For each user in the database
    for users in users_rows:
        # If they exist
        if users != None:
            # If the query matches their zid or name
            if re.search(query, users[0],re.IGNORECASE) or re.search(query, users[1],re.IGNORECASE):
                # create a full link to their account and add to the account
                # Photo with link
                dp_link = dp_url(users[0])
                # Name with link
                url_name = url_for("profile", student_id = users[0])
                name_link =''' <a href = '{}'> {} </a>'''.format(url_name, users[1])
                # Put them together
                final_link = dp_link + " " + name_link
                # Add to array
                q_results.append(final_link)
                # This means at least one user was found, so a non empty array will be returned
                toggle = 1
    if (toggle == 1):
        return q_results
    else:
        q_results = ["Sorry your query did not result in any hits"]
        return q_results

# Function which searches through posts, comments and replies
# Might have been better to do through multiple functions for comments and replies
# Ran out of time, sorry for the markers, It works tho trust me
def search_posts(query):
    # Connect the database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT * FROM posts ORDER BY ptime DESC''')
    posts_rows = cursor.fetchall()
    toggle = 0
    # The list which contains the final results
    q_results = []
    # For each post in the database
    for post in posts_rows:
        if (post != None and post[1] != None):
            # If the query is found in either the message or in the sender
            if re.search(query, post[1],re.IGNORECASE) or re.search(query, message_conversion(post[1]),re.IGNORECASE) or re.search(query, post[0], re.IGNORECASE) or re.search(query, zid_to_name(post[0]), re.IGNORECASE):
                q_results.append(post)
                # This means at least one user was found, so a non empty array will be returned
                toggle = 1
            else:
                # For each comment
                for comment in get_comments(post[0], post[6]):
                    if (comment[1] != None and comment[1] != None):
                        # If the query is found in either the message or in the sender
                        if re.search(query, comment[1],re.IGNORECASE) or re.search(query, message_conversion(comment[1]),re.IGNORECASE) or re.search(query, comment[2], re.IGNORECASE) or re.search(query, zid_to_name(comment[2]), re.IGNORECASE):
                            # This means at least one user was found, so a non empty array will be returned
                            toggle = 1           
                            # This makes sure that posts are not doubled up if there are multiple hits                
                            if (post not in q_results):
                                q_results.append(post)
                            else :
                                # Save time
                                break
                        else:
                            for reply in get_replies(comment[0], comment[4], comment[5]):
                                if (reply[1] != None and reply[1] != None):
                                    # If the query is found in either the message or in the sender
                                    if re.search(query, reply[1],re.IGNORECASE) or re.search(query, message_conversion(reply[1]),re.IGNORECASE) or re.search(query, reply[2], re.IGNORECASE) or re.search(query, zid_to_name(reply[2]), re.IGNORECASE):
                                        # This means at least one user was found, so a non empty array will be returned
                                        toggle = 1 
                                        # This makes sure that posts are not doubled up if there are multiple hits  
                                        if (post not in q_results):
                                            q_results.append(post)
                                        else :
                                            # Save time
                                            break
    if (toggle == 1):
        return q_results
    else:
        q_results = ["Sorry your query did not result in any hits"]
        return q_results

# Function which returns all the posts which the friends of the user have posted
def friends_posts(zid):
    # Get the list of friends
    friend_list = read_student_friends(zid)
    # Add the current person to the friend list to also retrieve their posts
    friend_list.append(zid)
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    # Have to put a variable amount of ? in for the length of the friend list
    sql = ''' SELECT * FROM posts WHERE p_zid in ({seq}) ORDER BY ptime DESC'''.format(seq=','.join(['?']*len(friend_list)))
    # Grabs all the posts from all friends
    cursor.execute(sql, friend_list)
    post_rows = cursor.fetchall()
    return post_rows

# Function which returns all the comments underneath a post
def get_comments(zid, post_id):
    # Connect database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT * FROM comments WHERE p_zid = ? AND post_id = ? ORDER BY ptime ASC''', (zid,post_id))
    # List of comments which are under the post for a specific user
    comment_rows = cursor.fetchall()
    return comment_rows
    
# Function which returns all the replies undernead a comment
def get_replies(zid, post_id, comment_id):
    # Connect database
    stu_db = sqlite3.connect('data/stu_db')
    cursor = stu_db.cursor()
    cursor.execute(''' SELECT * FROM replies WHERE p_zid = ? AND post_id = ? AND comment_id = ? ORDER BY ptime ASC''', (zid, post_id, comment_id))
    reply_rows = cursor.fetchall()
    # List of replies which are under the post and comment for a specific user
    return reply_rows




# List of functions which get used in Jinja
app.jinja_env.globals.update(zid_to_name=zid_to_name)
app.jinja_env.globals.update(message_conversion=message_conversion)
app.jinja_env.globals.update(dp_url=dp_url)
app.jinja_env.globals.update(search_users=search_users)
app.jinja_env.globals.update(search_posts=search_posts)
app.jinja_env.globals.update(get_comments=get_comments)
app.jinja_env.globals.update(get_replies=get_replies)    
if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD']=True
    app.run(debug=True)
