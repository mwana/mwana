# vim: ai ts=4 sts=4 et sw=4
import logging
import logging.handlers

class TlsSMTPHandler(logging.handlers.SMTPHandler):
    """
    Code borrowed from:
    http://www.velocityreviews.com/forums/t707606-logging-module-smtphandler-and-gmail-in-python-2-6-a.html
    http://mynthon.net/howto/-/python/python%20-%20logging.SMTPHandler-how-to-use-gmail-smtp-server.txt
    You cannot use gmail account for sending emails with logging module. It is
    because google requires TLS connection and logging module doesn't support it.
    To use gmail you have to extend logging.handlers.SMTPHandler class and
    override SMTPHandler.emit() method.
    """
    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            import string # for tls add this line
            try:
                from email.utils import formatdate
            except ImportError:
                formatdate = self.date_time
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            string.join(self.toaddrs, ","),
                            self.getSubject(record),
                            formatdate(), msg)
            if self.username:
                smtp.ehlo() # for tls add this line
                smtp.starttls() # for tls add this line
                smtp.ehlo() # for tls add this line
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
