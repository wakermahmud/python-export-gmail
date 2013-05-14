python-export-gmail
===================

Export emails from the GMAIL service using python and IMAP. Optionally save gmails to a local db for faster refresh.

Usage export-gmail.py username password folder [save]

where:<br>
  username: gmail username as used to log in to the gmail account<br>
  password: password associated with the username<br>
  folder:   the name of the folder you want to export, INBOX 'Holiday Snaps' or whatever<br>

  save:     supply this keyword if you want to save the downloaded email into into a local DB.<br>
            This is useful if you want to keep running this periodically and only get new messages.<br>

This is pretty much just a proof of concept and demonstrates how to export and save into sqlite or MySQL

