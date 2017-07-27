from ....utils import get_copy
from .base import RaspbianConverter


class Wireless(RaspbianConverter):
    netjson_key = 'interfaces'

    def to_intermediate(self):
        result = []
        interfaces = get_copy(self.netjson, self.netjson_key)
        new_interface = {}
        for interface in interfaces:
            if interface.get('type') == 'wireless' and interface.get('wireless').get('mode') is not 'adhoc':
                new_interface.update({
                    'ifname': interface.get('name'),
                    'iftype': interface.get('type'),
                })
                wireless = interface.get('wireless')
                new_interface.update({
                    'ssid': wireless.get('ssid'),
                    'radio': wireless.get('radio'),
                    'mode': wireless.get('mode'),
                    'hidden': wireless.get('hidden', False),
                    'rts_threshold': wireless.get('rts_threshold', -1),
                    'frag_threshold': wireless.get('frag_threshold', -1),
                    'encryption': self._get_encryption(wireless)
                })
                radios = get_copy(self.netjson, 'radios')
                if radios:
                    req_radio = [radio for radio in radios if radio['name'] == wireless.get('radio')][0]
                    new_interface.update({
                        'protocol': req_radio.get('protocol').replace(".", ""),
                        'hwmode': self._get_hwmode(req_radio),
                        'channel': req_radio.get('channel'),
                        'channel_width': req_radio.get('channel_width')
                    })
                    if 'country' in req_radio:
                        new_interface.update({'country': req_radio.get('country')})
                result.append(new_interface)
        return (('wireless', result),)

    def _get_hwmode(self, radio):
        protocol = radio.get('protocol')
        if protocol in ['802.11a', '802.11b', '802.11g']:
            return protocol[-1:]
        elif radio.get('channel') <= 13:
            return 'g'
        else:
            return 'a'

    def _get_encryption(self, wireless):
        encryption = wireless.get('encryption', None)
        new_encryption = {}
        if encryption is None:
            return new_encryption
        disabled = encryption.get('disabled', False)
        protocol = encryption.get('protocol')
        if disabled or protocol == 'none':
            return new_encryption
        protocol, method = protocol.split("_")
        print(protocol, method)
        if 'wpa' in protocol:
            if 'personal' in method:
                new_encryption.update({
                    'auth_algs': '1',
                    'wpa': '1' if protocol == 'wpa' else '2',
                    'wpa_key_mgmt': 'WPA-PSK',
                    'wpa_passphrase': encryption.get('key'),
                })
                if encryption.get('cipher'):
                    wpa_pairwise = str(encryption.get('cipher').replace('+', ' ')).upper()
                    new_encryption.update({'wpa_pairwise': wpa_pairwise})
        return new_encryption
