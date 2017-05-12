# -*- coding: utf-8 -*-
"""
Module for interacting with mattermost.

:copyright:
    The ObsPy Development Team (devs@obspy.org)
:license:
    GNU Lesser General Public License, Version 3
    (https://www.gnu.org/copyleft/lesser.html)
"""
import os
import json
import requests
import logging


class Mattermost(object):
    def __init__(self, verbose=False):
        self.logger = self._setup_logging(verbose)

        self.server_url = os.environ['MATTERMOST_SERVER_URL']
        self.logger.debug("Mattermost server URL: " + self.server_url)
        self.team_id = os.environ['MATTERMOST_TEAM_ID']
        self.logger.debug("Mattermost team id: " + self.team_id)
        self.channel_id = os.environ['MATTERMOST_CHANNEL_ID']
        self.logger.debug("Mattermost channelid: " + self.channel_id)
        self.user_id = os.environ['MATTERMOST_USER_ID']
        self.logger.debug("Mattermost user email: " + self.user_id)
        self.user_pass = os.environ['MATTERMOST_USER_PASS']
        self.logger.debug("Mattermost user pass: " + self.user_pass)

        # Login
        self.matterMostSession = requests.Session()
        self.matterMostSession.headers.update({"X-Requested-With": "XMLHttpRequest"})

        if 'SSL_CA' in os.environ:
            self.logger.debug("Using SSL key " + os.environ['SSL_CA'])
            self.matterMostSession.verify = os.environ['SSL_CA']

        url = self.server_url + '/api/v3/users/login'
        login_data = json.dumps({'login_id': self.user_id, 'password': self.user_pass})
        l = self.matterMostSession.post(url, data=login_data)
        self.logger.debug(l)
        # self.mattermostUserId = l.json()["id"]

    def _setup_logging(self, verbose):
        logger = logging.getLogger('Mattermost')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("Verbose logging")
        else:
            logging.getLogger().setLevel(logging.INFO)

        return logger

    def post(self, message):
        """
        Post a message to Mattermost. Adapted from http://stackoverflow.com/questions/42305599/how-to-send-file-through-mattermost-incoming-webhook
        :return: 
        """
        self.logger.debug("Posting message to mattermost: " + message)
        post_data = json.dumps({
                       'user_id': self.user_id,
                       'channel_id': self.channel_id,
                       'message': message,
                       'create_at': 0,
                   })
        url = self.server_url + '/api/v3/teams/' + self.team_id + '/channels/' + self.channel_id + '/posts/create'
        r = self.matterMostSession.post(self.server_url + '/api/v3/teams/' + self.team_id + '/channels/' + self.channel_id + '/posts/create', data=post_data)

        if r.status_code == 200:
            self.logger.debug(r.content)
        else:
            self.logger.warn(r.content)
