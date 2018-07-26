#!/usr/bin/python3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, sqlite3, re, datetime, jinja2, shutil
from flask import Flask, render_template, session, redirect, url_for, request
from time import gmtime, strftime

students_dir = "dataset-small";

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

# Open and create a database to store all this shit
stu_db = sqlite3.connect('data/stu_db')
# Idk why i was getting a table already exists error
cursor = stu_db.cursor()
cursor.execute('''DROP TABLE IF EXISTS users''')
cursor.execute('''DROP TABLE IF EXISTS posts''')
cursor.execute('''DROP TABLE IF EXISTS comments''')
cursor.execute('''DROP TABLE IF EXISTS replies''')
stu_db.commit()
# Create a table for this info
cursor = stu_db.cursor()
cursor.execute('''
    CREATE TABLE users(zid TEXT PRIMARY KEY, name TEXT, email TEXT, suburb TEXT, 
    hlong TEXT, hlat TEXT, password TEXT, program TEXT, birthday TEXT, courses TEXT, 
    friends TEXT, dp_link TEXT);
    ''')
cursor.execute('''
    CREATE TABLE posts(p_zid TEXT , message TEXT, from_zid TEXT, ptime TEXT,
    plong TEXT, plat TEXT, post_id INT);
    ''')
cursor.execute('''
    CREATE TABLE comments(p_zid TEXT , message TEXT, from_zid TEXT, ptime TEXT,
    post_id INT, comment_id INT);
    ''')
cursor.execute('''
    CREATE TABLE replies(p_zid TEXT , message TEXT, from_zid TEXT, ptime TEXT,
     post_id INT, comment_id INT, reply_id INT);
    ''')
stu_db.commit()
# Open the information for the students
students = sorted(os.listdir(students_dir))
for stu_id in students:
    # The path in which the files are located
    stu_path = students_dir+ "/" + stu_id
    details_filename = os.path.join(stu_path, "student.txt")
    # Open the students main information file and store in a database
    with open(details_filename) as f:
        details = f.read()
        #print(details)
        try:
            birthday = re.search("birthday: (.*?)\n", details).group(1)
        except:
            birthday = None
        try:
            courses = re.search("courses: (.*?)\n", details).group(1)
        except:
            courses = None
        try:
            email = re.search("email: (.*?)\n", details).group(1)
        except:
            email = None
        try:
            suburb = re.search("suburb: (.*?)\n", details).group(1)
        except:
            subrub = None
        try:
            hlong = re.search("longitude: (.*?)\n", details).group(1)
        except:
            hlong = None
        try:
            hlat = re.search("latitude: (.*?)\n", details).group(1)
        except:
            hlat = None
        try:
            name = re.search("name: (.*?)\n", details).group(1)
        except:
            name = None
        try:
            zid = re.search("zid: (.*?)\n", details).group(1)
        except:
            zid = None
        try:
            friends = re.search("friends: (.*?)\n", details).group(1)
        except:
            friends = None
        try:
            password = re.search("password: (.*?)\n", details).group(1)
        except:
            password = None
        try:
            program = re.search("program: (.*?)\n", details).group(1)
        except:
            program = None
        cursor = stu_db.cursor()
        cursor.execute('''INSERT INTO users(zid, name, email, suburb, hlong, hlat, password, program, birthday, courses, friends)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)''',(zid, name, email, suburb, 
        hlong, hlat, password, program, birthday, courses, friends)
        )
        stu_db.commit()
    # Retrieve list of all files in the directory
    post_files = list(reversed(sorted(os.listdir(stu_path))))
    # Remove the student file since it is not a post
    post_files.remove("student.txt")
    # If there is an image in the folder, link it into the database
    if "img.jpg" in post_files:
        # Path to the image
        dp_link = os.path.join(students_dir, stu_id, "img.jpg")
        # Add it into the table
        cursor = stu_db.cursor()
        cursor.execute('''UPDATE users SET dp_link = ? WHERE zid = ?''', (dp_link, stu_id))
        stu_db.commit()
        # Remove it from the list
        post_files.remove("img.jpg")

    # Now to deal with the posts and comments
    cursor = stu_db.cursor()
    # For the remaining files in the directory
    for post in post_files:
        # This is the filename for the file
        posts_filename = os.path.join(stu_path, post)
        # Open the file and extract data
        with open(posts_filename) as f:
            details = f.read()
            try:
                message = re.search("message: (.*?)\n", details).group(1)
            except:
                message = None
            try:
                from_zid = re.search("from: (.*?)\n", details).group(1)
            except:
                from_zid = None
            try:
                ptime = date_conversion(re.search("time: (.*?)\n", details).group(1))
            except:
                ptime = None
            try:
                plong = re.search("longitude: (.*?)\n", details).group(1)
            except:
                plong = None
            try:
                plat = re.search("latitude: (.*?)\n", details).group(1)
            except:
                plat = None
        # Distinguish between posts, comments, replies
        if re.match("\d.txt", post):
            # If it is a post, it only has one digit, and is placed into a table with the deets
            m = re.search("^(\d).txt$", post)
            cursor.execute('''INSERT INTO posts(p_zid, message, from_zid,
            ptime, plong, plat, post_id) 
            VALUES(?,?,?,?,?,?,?)''',(stu_id, message, from_zid, ptime, plong, plat, m.group(1)))  
        elif re.match("\d-\d.txt", post):
            # If it is a comment, it  has two digits, and is placed into a table with the deets
            m = re.search("^(\d)-(\d).txt$", post)
            cursor.execute('''INSERT INTO comments(p_zid, message, from_zid,
            ptime, post_id, comment_id) 
            VALUES(?,?,?,?,?,?)''',(stu_id, message, from_zid, ptime, m.group(1), m.group(2)))       
        elif re.match("\d-\d-\d.txt", post):
            # If it is a replt, it has three digits, and is placed into a table with the deets
            m = re.search("^(\d)-(\d)-(\d).txt$", post)
            cursor.execute('''INSERT INTO replies(p_zid, message, from_zid,
            ptime, post_id, comment_id, reply_id) 
            VALUES(?,?,?,?,?,?,?)''',(stu_id, message, from_zid, ptime, m.group(1), m.group(2), m.group(3)))
    stu_db.commit()      
stu_db.close()

