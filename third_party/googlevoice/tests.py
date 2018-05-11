from googlevoice import Voice, util
from os import path, remove
from unittest import TestCase, main

class VoiceTest(TestCase):
    voice = Voice()
    voice.login()
    outgoing = util.input('Outgoing number (blank to ignore call tests): ')
    forwarding = None
    if outgoing:
        forwarding = util.input('Forwarding number [optional]: ') or None
    
    if outgoing:
        def test_1call(self):
            self.voice.call(self.outgoing, self.forwarding)

        def test_sms(self):
            self.voice.send_sms(self.outgoing, 'i sms u')

        def test_2cancel(self):
            self.voice.cancel(self.outgoing, self.forwarding)
    
    def test_special(self):
        self.assertTrue(self.voice.special)
        
    def test_inbox(self):
        self.assertTrue(self.voice.inbox)
    
    def test_balance(self):
        self.assertTrue(self.voice.settings['credits'])
        
    def test_search(self):
        self.assertTrue(len(self.voice.search('joe')))
    
    def test_disable_enable(self):
        self.voice.phones[0].disable()
        self.voice.phones[0].enable()
    
    def test_download(self):
        msg = list(self.voice.voicemail.messages)[0]
        fn = '%s.mp3' % msg.id
        if path.isfile(fn): remove(fn)
        self.voice.download(msg)
        self.assertTrue(path.isfile(fn))
    
    def test_zlogout(self):
        self.voice.logout()
        self.assertTrue(self.voice.special is None)
        
    def test_config(self):
        from .conf import config
        self.assertTrue(config.forwardingNumber)
        self.assertTrue(str(config.phoneType) in '1237')
        self.assertEqual(config.get('wtf'), None)
        
if __name__ == '__main__': main()