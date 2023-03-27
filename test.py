import h2.connection
from h2.events import (
    ResponseReceived, DataReceived, StreamEnded, StreamReset, WindowUpdated,
    SettingsAcknowledged,
)
from twisted.internet import reactor, defer
from twisted.internet.endpoints import connectProtocol, SSL4ClientEndpoint
from twisted.internet.ssl import optionsForClientTLS
from twisted.internet.protocol import Protocol
from twisted.internet.ssl import CertificateOptions

class H2Request(Protocol):
    def __init__(self):
        self.conn = h2.connection.H2Connection()
        self.known_proto = None
        self.request_made = False
        self.request_complete = False
        self.flow_control_deferred = None
        self.target = None
        self.headers = None
        self.body = None

    def connectionMade(self):
        """
        Called by Twisted when the TCP connection is established. We can start
        sending some data now: we should open with the connection preamble.
        """
        self.conn.initiate_connection()
        self.transport.write(self.conn.data_to_send())

    def dataReceived(self, data):
        """
        Called by Twisted when data is received on the connection.

        We need to check a few things here. Firstly, we want to validate that
        we actually negotiated HTTP/2: if we didn't, we shouldn't proceed!

        Then, we want to pass the data to the protocol stack and check what
        events occurred.
        """
        if not self.known_proto:
            self.known_proto = self.transport.negotiatedProtocol
            assert self.known_proto == b'h2'

        events = self.conn.receive_data(data)

        for event in events:
            
            if isinstance(event, ResponseReceived):
                self.handleResponse(event.headers)
            elif isinstance(event, DataReceived):
                self.handleData(event.data)
            elif isinstance(event, StreamEnded):
                self.endStream()
            elif isinstance(event, SettingsAcknowledged):
                self.settingsAcked(event)
            elif isinstance(event, StreamReset):
                reactor.stop()
                raise RuntimeError("Stream reset: %d" % event.error_code)
            elif isinstance(event, WindowUpdated):
                self.windowUpdated(event)

        data = self.conn.data_to_send()
        if data:
            self.transport.write(data)

    def settingsAcked(self, event):
        """
        Called when the remote party ACKs our settings. We send a SETTINGS
        frame as part of the preamble, so if we want to be very polite we can
        wait until the ACK for that frame comes before we start sending our
        request.
        """
        if not self.request_made:
            self.sendRequest()

    def handleResponse(self, response_headers):
        """
        Handle the response by printing the response headers.
        """
        for name, value in response_headers:
            print("%s: %s" % (name.decode('utf-8'), value.decode('utf-8')))

        print("")

    def handleData(self, data):
        """
        We handle data that's received by just printing it.
        """
        print(data, end='')

    def endStream(self):
        """
        We call this when the stream is cleanly ended by the remote peer. That
        means that the response is complete.

        Because this code only makes a single HTTP/2 request, once we receive
        the complete response we can safely tear the connection down and stop
        the reactor. We do that as cleanly as possible.
        """
        self.request_complete = True
        self.conn.close_connection()
        self.transport.write(self.conn.data_to_send())
        self.transport.loseConnection()

    def windowUpdated(self, event):
        """
        We call this when the flow control window for the connection or the
        stream has been widened. If there's a flow control deferred present
        (that is, if we're blocked behind the flow control), we fire it.
        Otherwise, we do nothing.
        """
        if self.flow_control_deferred is None:
            return

        # Make sure we remove the flow control deferred to avoid firing it
        # more than once.
        flow_control_deferred = self.flow_control_deferred
        self.flow_control_deferred = None
        flow_control_deferred.callback(None)

    def connectionLost(self, reason=None):
        """
        Called by Twisted when the connection is gone. Regardless of whether
        it was clean or not, we want to stop the reactor.
        """
        if reactor.running:
            reactor.stop()

    def sendRequest(self):
        self.conn.send_headers(1, self.headers)
        self.request_made = True

        if self.body != None:
            self.sendBody()

    def sendBody(self):
        """
        Send some file data on the connection.
        """
        # Firstly, check what the flow control window is for stream 1.
        window_size = self.conn.local_flow_control_window(stream_id=1)

        # Next, check what the maximum frame size is.
        max_frame_size = self.conn.max_outbound_frame_size

        # We will send no more than the window size or the remaining file size
        # of data in this call, whichever is smaller.
        
        body_length = len(self.body)
        bytes_to_send = min(window_size, body_length)
        sent_bytes = 0

        # We now need to send a number of data frames.
        while bytes_to_send > 0:
            chunk_size = min(bytes_to_send, max_frame_size)
            data_chunk = self.body[sent_bytes:sent_bytes+chunk_size]
            self.conn.send_data(stream_id=1, data=data_chunk)

            bytes_to_send -= chunk_size
            body_length -= chunk_size
            sent_bytes += chunk_size

        # We've prepared a whole chunk of data to send. If the file is fully
        # sent, we also want to end the stream: we're done here.
        if body_length == 0:
            self.conn.end_stream(stream_id=1)
        else:
            # We've still got data left to send but the window is closed. Save
            # a Deferred that will call us when the window gets opened.
            self.flow_control_deferred = defer.Deferred()
            self.flow_control_deferred.addCallback(self.sendBody)

        self.transport.write(self.conn.data_to_send())

def main():
    target = "localhost"
    
    request = H2Request()
    request.target = target
    request.headers = [
            (':method', 'GET'),
            (':authority', target),
            (':scheme', 'https'),
            (':path', "/"),
        ]
    
    options = optionsForClientTLS(
        hostname="localhost"
    )

    connectProtocol(
        SSL4ClientEndpoint(reactor, target, 8088, options),
        request
    )
    
    reactor.run()

main()


