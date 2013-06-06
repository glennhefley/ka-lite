"""
These will be run when you run "manage.py test [main].
These require a test server to be running, and multiple ports
  need to be available.  Run like this:
./manage.py test main --liveserver=localhost:8004-8010
".
"""
import sys
import random
import requests
import urllib
import unittest
import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from django.core.urlresolvers import reverse
from django.test import TestCase, LiveServerTestCase
from django.core.management import call_command
from django.test.client import Client

import settings
from utils import caching
from kalite.main import topicdata
from utils.testing import KALiteLocalTestCase, add_to_local_settings



class SimpleTest(LiveServerTestCase):

    @unittest.skipIf(settings.CACHE_TIME==0, "Test only relevant when caching is enabled")
    def test_cache_invalidation(self):

        # Get a random youtube id
        n_videos = len(topicdata.NODE_CACHE['Video'])
        video_slug = topicdata.NODE_CACHE['Video'].keys()[random.randint(0,n_videos-1)]
        youtube_id = topicdata.NODE_CACHE['Video'][video_slug]['youtube_id']
        video_path = topicdata.NODE_CACHE['Video'][video_slug]['path']

        # Clean the cache for this item
        caching.expire_page(path=video_path)
        
        # Create the cache item, and check it
        self.assertTrue(not caching.has_cache_key(path=video_path))
        urllib.urlopen(self.live_server_url + video_path).close()
        self.assertTrue(caching.has_cache_key(path=video_path))

        # Invalidate the cache item, and check it
        #caching.expire_page(path=video_path)
        caching.invalidate_cached_video_page(youtube_id) # test the convenience function
        
        self.assertTrue(not caching.has_cache_key(path=video_path))

    
    @unittest.skipIf(settings.CACHE_TIME==0, "Test only relevant when caching is enabled")
    def test_cache_across_clients(self):

        # Get a random youtube id
        n_videos = len(topicdata.NODE_CACHE['Video'])
        video_slug = topicdata.NODE_CACHE['Video'].keys()[random.randint(0,n_videos-1)]
        youtube_id = topicdata.NODE_CACHE['Video'][video_slug]['youtube_id']
        video_path = topicdata.NODE_CACHE['Video'][video_slug]['path']

        # Clean the cache for this item
        caching.expire_page(path=video_path)
        self.assertTrue(not caching.has_cache_key(path=video_path), "No cache key after expiring the page")
                
        # Set up the cache with Django client
        Client().get(video_path)
        self.assertTrue(caching.has_cache_key(path=video_path), "Cache key exists after Django Client get")
        caching.expire_page(path=video_path) # clean cache
        self.assertTrue(not caching.has_cache_key(path=video_path), "No cache key after expiring the page")
                
        # Get the same cache key when getting with urllib, and make sure the cache is created again
        urllib.urlopen(self.live_server_url + video_path).close()
        self.assertTrue(caching.has_cache_key(path=video_path), "Cache key exists after urllib get")
        caching.expire_page(path=video_path) # clean cache
        self.assertTrue(not caching.has_cache_key(path=video_path), "No cache key after expiring the page")
        
        # 
        requests.get(self.live_server_url + video_path)
        self.assertTrue(caching.has_cache_key(path=video_path), "Cache key exists after urllib get")
        caching.expire_page(path=video_path) # clean cache
        self.assertTrue(not caching.has_cache_key(path=video_path), "No cache key after expiring the page")

    
class DeviceUnregisteredTest(KALiteLocalTestCase):
    """Validate all the steps of registering a device."""

    def test_device_registration(self):
        """
        Tests that a device is initially unregistered, and that it can
        be registered through automatic means.
        """

        home_url = self.reverse("homepage")

        # First, get the homepage without any automated information.
        self.browser.get(home_url) # Load page
        self.assertIn("Home", self.browser.title, "Homepage title")
        message = self.browser.find_element_by_id("container").find_element_by_xpath("//div[contains(@class,'message')]")
        self.assertIn("warning", message.get_attribute("class"), "warning message exists")
        self.assertIn("complete the setup", message.text, "warning message is for completing the setup.")
        
        # Make sure nobody is logged in
        login = self.browser.find_element_by_id("nav_login")
        self.assertIn("not-logged-in", login.get_attribute("class"), "Not (yet) logged in")
        
        # Now, log in as admin
        login.click()
        self.assertTrue(self.wait_for_page_change(home_url), "Clicked to change pages")
        self.assertIn("/login/", self.browser.current_url, "Login page url--we are on the login page")
        self.assertIn("Login", self.browser.title, "Login page title--we are on the login page")
        
        self.browser_activate_element(id="id_username")
        self.browser_send_keys(self.admin_user.username)
        self.browser_send_keys(Keys.TAB)
        self.browser_send_keys(self.admin_user.password)
        self.browser_send_keys(Keys.TAB)
        self.browser_send_keys(Keys.RETURN)
        
#        import pdb; pdb.set_trace()       
        

    
class DeviceAutoregisterTest(KALiteLocalTestCase):
    """"""
    
    def setUp(self):
        add_to_local_settings("INSTALL_CERTIFICATES", ["dummy_certificate"])
        super(DeviceAutoregisterTest,self).setUp()
    
    def tearDown(self):
        #import pdb; pdb.set_trace()
        #pass
        super(DeviceAutoregisterTest,self).tearDown()
        
    def test_device_registration(self):
        """
        Tests that a device is initially unregistered, and that it can
        be registered through automatic means.
        """

        home_url = self.reverse("homepage")
