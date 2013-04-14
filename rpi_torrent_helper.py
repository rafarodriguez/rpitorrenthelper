#!/usr/bin/env python

from datetime import datetime
from subprocess import call
import feedparser
import json
import urllib
import smtplib
import sys

SUBSCRIPTION_LIST_FILE = '/home/pi/scripts/rpitorrenthelper/subscription_list.json'

def GetFeedList():
  feed_list = []
  with open(SUBSCRIPTION_LIST_FILE) as json_file:
    feed_list = json.load(json_file)
    json_file.close()
  return feed_list

def UpdateSyncDates(torrents):
  if len(torrents):
    max_date = (torrents[0]["date"], torrents[0]["date_parsed"])
    for torrent in torrents:
      if torrent["date_parsed"] > max_date[1]:
        max_date = (torrent["date"], torrent["date_parsed"])
    with open(SUBSCRIPTION_LIST_FILE, 'r+') as json_file:
      json_data = json.load(json_file)
      for feed in json_data:
        feed['last_sync'] = max_date[0]
      # Delete file before dumping update json
      json_file.seek(0)
      json_file.truncate()
      json.dump(json_data, json_file, indent=2)
      json_file.close()

def GetTorrents(feed_list):
  torrents = []
  for feed in feed_list:
    last_sync = feedparser._parse_date(feed['last_sync'])
    feedparser_dict = feedparser.parse(feed['link'])
    for entry in feedparser_dict.entries:
      # Torrent links are stored as a link element or as an enclosure
      if entry.published_parsed > last_sync:
        if '.torrent' in entry.link:
          torrents.append({"link": entry.link,
                           "date": entry.published,
                           "date_parsed": entry.published_parsed})
        elif (len(entry.enclosures) and
                 entry.enclosures[0]['type'] == 'application/x-bittorrent'):
          torrents.append({"link": entry.enclosures[0]['href'],
                           "date": entry.published,
                           "date_parsed": entry.published_parsed})
    # Get highest date of this feed, update json, and return only torrents
  UpdateSyncDates(torrents)
  torrents = [torrent["link"] for torrent in torrents]
  return torrents

def AddTorrentsToTransmission(torrents):
  for torrent in torrents:
      torrent = '\"%s\"' % torrent
      call(['transmission-remote', '-a', torrent])

def main():
  feed_list = GetFeedList()
  torrents = GetTorrents(feed_list)
  AddTorrentsToTransmission(torrents)


if __name__ == "__main__":
 sys.exit(main())
