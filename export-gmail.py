#!/bin/env python 

import sys, datetime, re
import imaplib
import email
import hashlib
import sqlite3 as DBA
import dateutil.parser as dparser
from optparse import OptionParser

    
def usage():
    print "\nUsage %s username password folder [save]\n" % sys.argv[0]
    sys.exit(0)


    
" this is the name of the database that you want to save the emails into "

db_name = 'gmail.db'


"""
Return a list of all the email uids that have been previously saved in the 
local db

We use this list to decide if we have already got/downloaded these messages before

"""

def ct(text):
    date = (dparser.parse(text))
    return date.isoformat()


def get_db(db_name):
    
    " for MYSQL assumes a database called myname exists - change the rest of the params as needed "
    conn = DBA.connect(db_name)  if  'sqlite3' == DBA.__name__ else DBA.connect(host=h, user=mu, passwd=mp, db=db) # name of the data base

    return conn

def get_ids_from_db(f):
    l = []
    try:
        conn = get_db(db_name)
        
        c = conn.cursor()
        
        t = "%s" % f
        
        q = "SELECT id FROM %s" % (t,)
    
        c.execute(q)
        
        l = [x[0] for x in c.fetchall()]
        
        conn.close()
    except DBA.OperationalError, e:
        print e
   
    return l

def create_global_table(f):
    conn = get_db(db_name)
    
    c = conn.cursor()

    """
    Create a table in the database with the same name as the gmail folder     
    Where:
        id         - unique id generated over the column data
        subject    - email subject
        dt         - the timestamp from the email
        body       - the extracted email body
        email      - this is the raw email information received from gmail - unparsed.
    """
    
    
    t = "%s" % f
    
    constraint = ' UNIQUE ' if  'sqlite3' == DBA.__name__ else ' PRIMARY KEY '
    
    q = "CREATE TABLE %s (id INTEGER %s, subject text, dt datetime, body text, email text)" % (t, constraint,)
    try:
        c.execute(q)
    except DBA.OperationalError, e:
        " ignore the error if the table exists already "
        pass
    conn.close()
        


def save(f, id, email_message, subject, date, body):
    conn = get_db(db_name)
    
    c = conn.cursor()
    t = "%s" % f
    " when inserting we will use positional placement "        
    tuple = (id, subject, ct(date), body, str(email_message))

    placeholder = '?' if  'sqlite3' == DBA.__name__ else '%s'

    try:
        qs = "INSERT INTO %s (id, subject, dt, body, email) VALUES (%s,%s,%s,%s,%s)" % (t, placeholder, placeholder, placeholder, placeholder, placeholder)
        c.execute(qs, tuple)
    except DBA.IntegrityError, e:
        " A fail due to unique constraint firing - ignore - this is OK "
        pass
    
    conn.commit()
    conn.close()
    

def parse_body(raw):
    lines = raw.as_string().splitlines()
    for i, l in enumerate(lines):
        " For me the part of the body I am interested in follows 'Content-Transfer-Encoding' "
        if 'Content-Transfer-Encoding' in l:
            i += 1
            break
    s = raw.as_string()
    
    body = "\n".join(lines[i:])
    return body

def connect_to_gmail(f):
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(u, p)  
    
    """
    connect to folder with matching label
    """
    mail.select(f) 
    return mail

def get_gmail_uids(mail):
    """ 
    search and return all email uids
    """
    
    result, data = mail.uid('search', None, "ALL") 
#    result, data = mail.uid('search', None, '(HEADER Subject "Something that is in my Subject line")')
    
    target_uids = data[0].split()
    len_uids = len(target_uids)
    
    print "%s messages in folder '%s'" % (len_uids, f,)
    return target_uids



def main():
    
    mail = connect_to_gmail(f)
    target_uids = get_gmail_uids(mail)
    
    
    """ 
    If we have opted to save the emails in a local db then find out what we saved before
    so we don't bother to save them again
    """
    if save_in_db:
        
        create_global_table(f)

        from sets import Set  
        already_saved_uids = get_ids_from_db(f)
        uids_list_int = [int(id) for id in target_uids]
        
        " figure out what uids are new that we should get "
        target_uids = list(Set(uids_list_int).difference(Set(already_saved_uids)))
        print "Updating %s of a possible %s\n" % (len(target_uids), len(uids_list_int))     

    for email_uid in target_uids:
        result, email_data = mail.uid('fetch', email_uid, '(RFC822)')
        
        raw_email = email_data[0][1]
        email_message = email.message_from_string(raw_email)
        
        body = parse_body(email_message)
        date = email_message['date']
        subject = email_message['subject']
    
        print '%-8s: %s\n' % ('FROM', email_message['from'])
        print '%-8s: %s\n' % ('DATE', date)
        print '%-8s: %s\n' % ('SUBJECT', subject)
        print '%-8s: %s\n' % ('BODY', body)
    
        if save_in_db:
            save(f, email_uid, email_message, subject, date, body)
   
if __name__ == "__main__":

    parser = OptionParser()

    parser.add_option("--mysql-host", action="store", dest="HOST", help="MySQL host")
    parser.add_option("-u", "--gmail-username", action="store", dest="USER", help="Gmail username")
    parser.add_option("-p", "--gmail-password", action="store", dest="PASSWORD", help="Gmail password")
    parser.add_option("-f", "--gmail-folder", action="store", dest="FOLDER", help="Gmail folder")
    parser.add_option("--save", action="store_true", dest="SAVE", default=True, help="Gmail folder")
    parser.add_option("--mysql-username", action="store", dest="MYSQLUSER", help="MySQL username")
    parser.add_option("--mysql-password", action="store", dest="MYSQLPASSWORD", help="MySQL password")
    parser.add_option("--database", action="store", default="myname", dest="DATABASE", help="MySQL database")

    (options, args) = parser.parse_args()
    
    h = options.HOST
    u = options.USER
    f = options.FOLDER
    p = options.PASSWORD
    mu = options.MYSQLUSER
    mp = options.MYSQLPASSWORD
    db = options.DATABASE
    save_in_db = options.SAVE

    use_sqlite = len(h) == 0
    
    try:
        if not use_sqlite:
            import MySQLdb as DBA
            print "MYSQL Support found"
    except:
        print "No MYSQL Support found"


    try:
        main()
    except:
        parser.print_help()
