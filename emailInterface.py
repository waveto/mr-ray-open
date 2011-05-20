'''
Methods used in deploying emails
'''
import datetime
import logging

import config
from dbtools import waveTools

from google.appengine.api import mail

def sendFirstNotificationEmail(url, wave_id, wavelet_id, send_to, who_modified, wave_title, message=""):
    '''
    Sends the first notification email to the user
    @param url: this users unique url
    @param wave_id: the id of the wave that the email is about
    @param wavelet_id: the id of the wavelet that the email is about
    @param send_to: the email receipient to sent the email to
    @param who_modified: who modified the wave and triggered the email
    @param wave_title: the title of the wave
    @param message="": the personalized message that was sent by the adder
    '''
    if _isEmailValid(send_to):
        logging.info("Sending first notification email to " + send_to)
        #Fetch the meta wave object
        metaWave = waveTools.get(wave_id, wavelet_id)
        
        #Sort the message content variables for sending
        wave_title = wave_title or "Untitled"
        message = message or "No message was left"
        display_name = _getDisplayName(metaWave, who_modified)
        invitor = display_name + " (" + who_modified + ")"
        
        text_variables = {  'title'     : wave_title,
                            'invitor'   : invitor,
                            'message'   : message,
                            'url'       : url,
                            'time'      : datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                            'robot_web' : config.ROBOT_WEB}
        
        #Generate the address and subject
        sender_address = config.ROBOT_EMAIL_SENDER_NAME + " <" + config.ROBOT_EMAIL_SEND_NOTIFICATION + ">"
        subject = "Invitation to join: " + wave_title
        
        #Send!
        mail.send_mail( sender_address,
                        send_to,
                        subject,
                        FIRST_NOTIFICATION_PLAIN % text_variables,
                        html=FIRST_NOTIFICATION_HTML % text_variables)
        logging.info("Mail sent successfully to " + send_to)


def sendNotificationEmail(url, wave_id, wavelet_id, send_to, who_modified, wave_title, who_modified_display=None):
    '''
    Sends a notification email to the user
    @param url: this users unique url
    @param wave_id: the id of the wave that the email is about
    @param wavelet_id: the id of the wavelet that the email is about
    @param send_to: the email receipient to sent the email to
    @param who_modified: who modified the wave and triggered the email
    @param wave_title: the title of the wave
    @param who_modified_display=None: a friendly name of who modified the wave. If None then a friendly name is retrieved from wave meta
    '''
    if _isEmailValid(send_to):
        logging.info("Sending notification email to " + send_to)
        #Fetch the meta wave object
        metaWave = waveTools.get(wave_id, wavelet_id)
        
        #Sort the message content variables for sending
        wave_title = wave_title or "Untitled"
        display_name = who_modified_display or _getDisplayName(metaWave, who_modified)
        invitor = display_name + " (" + who_modified + ")"
        
        text_variables = {  'title'     : wave_title,
                            'modifier'  : invitor,
                            'url'       : url,
                            'time'      : datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                            'robot_web' : config.ROBOT_WEB}
        
        #Generate the address and subject
        sender_address = config.ROBOT_EMAIL_SENDER_NAME + " <" + config.ROBOT_EMAIL_SEND_NOTIFICATION + ">"
        subject = "Update: " + wave_title
        
        mail.send_mail( sender_address,
                        send_to,
                        subject,
                        REPLY_NOTIFICATION_PLAIN % text_variables,
                        html=REPLY_NOTIFICATION_HTML % text_variables)
        logging.info("Mail sent successfully to " + send_to)

def _getDisplayName(metaWave, who_modified):
    '''
    @param metaWave: a metaWave object from the datastore
    @param who_modified: the person who modified the message
    @return the friendly name or who_modified if not found
    '''
    try:
        return metaWave.participant_profiles.get(who_modified, None).get('displayName', None) or who_modified
    except:           
        return who_modified

def _isEmailValid(email):
    '''
    Performs some validation checks on the email address. This could be used
    to prevent blacklisted address' in the future
    @param email: the email address to check
    
    @return True if and only if the email address is valid
    '''
    return mail.is_email_valid(email)




################################################################################
# Email content (HTML)
################################################################################
FIRST_NOTIFICATION_HTML = \
"""
<table width="100%%" border="0" cellspacing="0" bordercolor="gray">
    <tr><td>
        <table width="100%%" border="0" cellspacing="10" style="font-family:arial, sans-serif; font-size:small;">
            <tr>
                <td width="77px" height="77px">
                    <img src="%(robot_web)sweb/media/icon.png" title="Mr Ray logo" alt="Mr Ray logo" height="75" width="75" style="border:1px solid #CAD0D9; font-size:xx-small;"/>
                </td>
                <td>
                    <p style="font-size:medium; font-weight:bold;">Mr Ray, the wav-e-mail bot</p>
                </td>
            </tr>
            <tr>
                <td colspan=2><p><b>You have been invited to take part in a conversation on Google Wave using the Mr-Ray service. This means you don't need a Google Wave account. All you have to do is click on the link provided and get started!</b></p><br /></td>
            </tr>
            <tr>
                <td style="color:gray;">Wave:</td><td>%(title)s</td>
            </tr>
            <tr>
                <td style="color:gray;">By:</td><td>%(invitor)s</td>
            </tr>
            <tr>
                <td style="color:gray;">Invitation Message:</td><td>%(message)s</td>
            </tr>
            <tr>
                <td style="color:gray;">Your link:</td><td>Please don't share <a href="%(url)s">your secret link!</a></td>
            </tr>
        </table>
    </td></tr>
    <tr><td style="color:gray; font-family:arial, sans-serif; font-size:xx-small; background-color:#F6F6F6">
        <p><b>What is Mr-Ray and why have I been sent this e-mail?</b></p>
        <p>Mr-Ray is a free service that allows you to communicate with Google Wave users without needing an account. Someone on Google Wave wanted to invite you into their conversation. You can find more details about <a href="http://wave.google.com/about.html">Google Wave</a> and the <a href="https://github.com/waveto/mr-ray-open">Mr-Ray</a> service using the links provided.</p>
        <p><b>Why shouldn't I share the link that was sent to me?</b><p>
        <p>This link is unique to you and your e-mail address. Sharing it will allow other people to reply as you.</p>
        <p><b>I don't want any more notifications about this wave, what should I do?</b></p>
        <p>Don't worry. Just ignore this e-mail. You will only receive more notifications if you visit the link we provided.</p>
        <br />
        <p>Mail sent at %(time)s</p>
        <p>Do not reply to this email address it is not monitored. You will not receive any new notifications about updates to the wave until you have visited the url.</p>
    </td></tr>
</table>
"""

REPLY_NOTIFICATION_HTML = \
"""
<table width="100%%" border="0" cellspacing="0" bordercolor="gray">
    <tr><td>
        <table width="100%%" border="0" cellspacing="10" style="font-family:arial, sans-serif; font-size:small;">
            <tr>
                <td width="77px" height="77px">
                    <img src="%(robot_web)sweb/media/icon.png" title="Mr Ray logo" alt="Mr Ray logo" height="75" width="75" style="border:1px solid #CAD0D9; font-size:xx-small;"/>
                </td>
                <td>
                    <p style="font-size:medium; font-weight:bold;">Mr Ray, the wav-e-mail bot</p>
                </td>
            </tr>
            <tr>
                <td colspan=2><p><b>A Wave that you follow has been updated. We thought you might want to see the changes!</b></p><br /></td>
            </tr>
            <tr>
                <td style="color:gray;">Wave:</td><td>%(title)s</td>
            </tr>
            <tr>
                <td style="color:gray;">By:</td><td>%(modifier)s</td>
            </tr>
            <tr>
                <td style="color:gray;">Your link:</td><td>Please don't share <a href="%(url)s">your secret link!</a></td>
            </tr>
        </table>
    </td></tr>
    <tr><td style="color:gray; font-family:arial, sans-serif; font-size:xx-small; background-color:#F6F6F6">
        <p><b>Why shouldn't I share the link that was sent to me?</b><p>
        <p>This link is unique to you and your e-mail address. Sharing it will allow other people to reply as you.</p>
        <p><b>I don't want any more notifications about this wave, what should I do?</b></p>
        <p>Don't worry. Just ignore this e-mail. You will only receive more notifications if you visit the link we provided.</p>
        <br />
        <p>Mail sent at %(time)s</p>
        <p>Do not reply to this email address it is not monitored. You will not receive any new notifications about updates to the wave until you have visited the url.</p>
    </td></tr>
</table>
"""

################################################################################
# Email content (Plain)
################################################################################
FIRST_NOTIFICATION_PLAIN = \
"""
You have been invited to take part in a conversation on Google Wave using the Mr-Ray service. This means you don't need a Google Wave account. All you have to do is click on the link provided and get started!

Wave: %(title)s
By: %(invitor)s
Invitation Message: %(message)s
Your link: Please don't share your secret link: %(url)s


************************
*What is Mr-Ray and why have I been sent this e-mail?
Mr-Ray is a free service that allows you to communicate with Google Wave users without needing an account. Someone on Google Wave wanted to invite you into their conversation. You can find more details about Google Wave(http://wave.google.com/about.html) and the Mr-Ray service(https://github.com/waveto/mr-ray-open) service using the links provided.
*Why shouldn't I share the link that was sent to me?
This link is unique to you and your e-mail address. Sharing it will allow other people to reply as you.
*I don't want any more notifications about this wave, what should I do?
Don't worry. Just ignore this e-mail. You will only receive more notifications if you visit the link we provided.


Mail sent at %(time)s
Do not reply to this email address it is not monitored. You will not receive any new notifications about updates to the wave until you have visited the url.
"""

REPLY_NOTIFICATION_PLAIN = \
"""
A Wave that you follow has been updated. We thought you might want to see the changes!

Wave: %(title)s
By: %(modifier)s
Your link: Please don't share your secret link: %(url)s


************************
*Why shouldn't I share the link that was sent to me?
This link is unique to you and your e-mail address. Sharing it will allow other people to reply as you.
*I don't want any more notifications about this wave, what should I do?
Don't worry. Just ignore this e-mail. You will only receive more notifications if you visit the link we provided.


Mail sent at %(time)s
Do not reply to this email address it is not monitored. You will not receive any new notifications about updates to the wave until you have visited the url.
"""