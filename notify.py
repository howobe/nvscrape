import abc
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from slack import WebClient
from slack.errors import SlackApiError
import logging

slackLogger = logging.getLogger("slack")
emailLogger = logging.getLogger("email")


class NotifierInterface(metaclass=abc.ABCMeta):

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'send') and
                callable(subclass.send) or
                NotImplemented)

    @abc.abstractmethod
    def send(self):
        raise NotImplementedError


class EmailNotification(NotifierInterface):

    def __init__(self, emailAddress: str, emailPsk: str, port: int = 465):
        self.user = {"email": emailAddress, "psk": emailPsk}
        self.port = port

    def addRecipients(self, *args):
        if not hasattr(self, "recipients"):
            self.recipients = []
        self.recipients.extend(args)

    def setSubject(self, subject: str):
        self.subject = subject

    def setBody(self, body: str):
        self.body = body

    def send(self):
        message = MIMEMultipart()
        message["From"] = self.user["email"]
        message["To"] = ", ".join(self.recipients)
        message["Subject"] = self.subject
        message.attach(MIMEText(self.body, "plain"))
        msg = message.as_string()

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtplib.gmail.com", self.port, context=context)\
                as server:
            server.login(self.user["email"], self.user["psk"])
            server.sendmail(self.user["email"], self.recipients, msg)


class SlackNotification(NotifierInterface):

    def __init__(self, apiToken: str):
        self.client = WebClient(apiToken)
        slackLogger.info("Initiating Slack WebClient...")

    def setBody(self, message):
        self.message = message
        slackLogger.debug("Message set: " + self.message)

    def send(self):
        try:
            self.client.chat_postMessage(
                channel='#notifications',
                text=self.message)
        except SlackApiError as e:
            assert e.response["ok"] is False
            assert e.response["error"]
            slackLogger.exception(e)
