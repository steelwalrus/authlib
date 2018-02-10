from authlib.specs.rfc5849 import TemporaryCredentialMixin


class TemporaryCredential(dict, TemporaryCredentialMixin):
    def get_client_id(self):
        return self.get('oauth_consumer_key')

    def get_redirect_uri(self):
        return self.get('oauth_callback')

    def get_user_id(self):
        return self.get('user_id')

    def check_verifier(self, verifier):
        return self.get('oauth_verifier') == verifier

    def get_oauth_token(self):
        return self.get('oauth_token')

    def get_oauth_token_secret(self):
        return self.get('oauth_token_secret')


def register_temporary_credential_hooks(
        authorization_server, cache, key_prefix='temporary_credential:'):

    def create_temporary_credential(token, client_id, redirect_uri):
        key = key_prefix + token['oauth_token']
        token['oauth_consumer_key'] = client_id
        if redirect_uri:
            token['oauth_callback'] = redirect_uri

        cache.set(key, token, timeout=86400)  # cache for one day
        return TemporaryCredential(token)

    def get_temporary_credential(oauth_token):
        if not oauth_token:
            return None
        key = key_prefix + oauth_token
        value = cache.get(key)
        if value:
            return TemporaryCredential(value)

    def delete_temporary_credential(oauth_token):
        if oauth_token:
            key = key_prefix + oauth_token
            cache.delete(key)

    def create_authorization_verifier(credential, grant_user, verifier):
        key = key_prefix + credential.get_oauth_token()
        credential['oauth_verifier'] = verifier
        credential['user_id'] = grant_user.get_user_id()
        cache.set(key, credential, timeout=86400)
        return credential

    authorization_server.register_hook(
        'create_temporary_credential', create_temporary_credential)
    authorization_server.register_hook(
        'get_temporary_credential', get_temporary_credential)
    authorization_server.register_hook(
        'delete_temporary_credential', delete_temporary_credential)
    authorization_server.register_hook(
        'create_authorization_verifier', create_authorization_verifier)


def register_exists_nonce(
        authorization_server, cache, key_prefix='nonce:', expires=300):

    def exists_nonce(nonce, timestamp, client_id, oauth_token):
        key = '{}{}-{}-{}'.format(key_prefix, nonce, timestamp, client_id)
        if oauth_token:
            key = '{}-{}'.format(key, oauth_token)
        rv = cache.has(key)
        cache.set(key, 1, timeout=expires)
        return rv

    authorization_server.register_hook('exists_nonce', exists_nonce)