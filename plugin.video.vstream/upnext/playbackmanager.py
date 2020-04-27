# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

from __future__ import absolute_import, division, unicode_literals
from xbmc import sleep
from upnext.stillwatching import StillWatching
from upnext.upnext import UpNext
from upnext.utils import addon_path, calculate_progress_steps, clear_property, event, get_setting, log as ulog, set_property, get_property
from tvwatch.utils import get_season_episode

class PlaybackManager:

    def __init__(self, player):
        self.player = player

        while not self.check_consistency():
            sleep(300)

        self.episode = {}
        self.episode["season"], self.episode["episode"], self.episode["title"] = get_season_episode(player.sTitle)
        self.episode["episode"] += 1
        self.episode["art"] = {}
        self.episode["art"]["fanart"] = player.sThumbnail
        self.episode["art"]["landscape"] = player.sThumbnail
        self.episode["art"]["clearart"] = player.sThumbnail
        self.episode["art"]["clearlogo"] = player.sThumbnail
        self.episode["art"]["poster"] = player.sThumbnail
        self.episode["art"]["thumb"] = player.sThumbnail
        self.episode["runtime"] = self.notification_time()
        self.max_played_in_a_row = get_setting('playedInARow')
        self.next_episode = False
        self.stop = False

    def log(self, msg, level=2):
        ulog(msg, name=self.__class__.__name__, level=level)

    def check_consistency(self):
        consistent = False

        totalTime = self.player.getTotalTime()
        currentTime = self.player.getTime()

        if totalTime > 0:
            if (float('%.2f' % (currentTime / totalTime)) <= 0.90):
                consistent = True

        return consistent

    def notification_time(self):
        # Use a customized notification time, when configured
        if (self.player.totalTime > 60) and (get_setting('customAutoPlayTime') == 'true'):
            if self.player.totalTime > 60 * 60:
                return int(get_setting('autoPlayTimeXL'))
            if self.player.totalTime > 40 * 60:
                return int(get_setting('autoPlayTimeL'))
            if self.player.totalTime > 20 * 60:
                return int(get_setting('autoPlayTimeM'))
            if self.player.totalTime > 10 * 60:
                return int(get_setting('autoPlayTimeS'))
            return int(get_setting('autoPlayTimeXS'))

        # Use one global default, regardless of episode length
        return int(get_setting('autoPlaySeasonTime'))

    def is_playback_paused(self):
        return False
        try:
            start_time = self.player.getTime()
            sleep(1000)
            return (self.player.getTime() == start_time)
        except Exception:
            return False

    def manage_next_episode_notification(self):
        if (self.player.totalTime > 60) and (self.player.totalTime - self.player.currentTime < self.episode["runtime"]) and not self.stop:
            self.stop = True
            if get_property('enableNextUp') == 'true':
                self.next_episode = self.launch_up_next()
        return self.next_episode

    def launch_up_next(self):
        # We have a next up episode choose mode
        if get_setting('simpleMode') == '0':
            next_up_page = UpNext('script-upnext-upnext-simple.xml', addon_path(), 'default', '1080i')
            still_watching_page = StillWatching('script-upnext-stillwatching-simple.xml', addon_path(), 'default', '1080i')
        else:
            next_up_page = UpNext('script-upnext-upnext.xml', addon_path(), 'default', '1080i')
            still_watching_page = StillWatching('script-upnext-stillwatching.xml', addon_path(), 'default', '1080i')

        showing_next_up_page, showing_still_watching_page = self.show_popup_and_wait(self.episode,
                                                                                     next_up_page,
                                                                                     still_watching_page)
        next_episode = self.extract_play_info(next_up_page, showing_next_up_page,
                                              showing_still_watching_page, still_watching_page)

        self.log("next_episode "+str(next_episode))
        return next_episode

    def show_popup_and_wait(self, episode, next_up_page, still_watching_page):
        try:
            play_time = self.player.getTime()
            total_time = self.player.getTotalTime()
        except Exception:
            self.log('exit early because player is no longer running', 2)
            return False, False
        progress_step_size = calculate_progress_steps(total_time - play_time)
        next_up_page.set_item(episode)
        next_up_page.set_progress_step_size(progress_step_size)
        still_watching_page.set_item(episode)
        still_watching_page.set_progress_step_size(progress_step_size)
        played_in_a_row = get_property('tvwatch2_played_in_a_row')
        if not played_in_a_row:
            played_in_a_row = "0"
            set_property('tvwatch2_played_in_a_row', played_in_a_row)
        self.log('max current played in a row %s' % self.max_played_in_a_row, 2)
        self.log('current played in a row %s' % played_in_a_row, 2)
        showing_next_up_page = False
        showing_still_watching_page = False
        if int(played_in_a_row) <= int(self.max_played_in_a_row):
            self.log('showing next up page as played in a row is %s' % played_in_a_row, 2)
            next_up_page.show()
            set_property('plugin.video.tvwatch2.dialog', 'true')
            showing_next_up_page = True
        else:
            self.log('showing still watching page as played in a row %s' % played_in_a_row, 2)
            still_watching_page.show()
            set_property('plugin.video.tvwatch2.dialog', 'true')
            showing_still_watching_page = True
        while (self.player.isPlaying() and (total_time - play_time > 1)
               and not next_up_page.is_cancel() and not next_up_page.is_watch_now()
               and not still_watching_page.is_still_watching() and not still_watching_page.is_cancel()):
            try:
                play_time = self.player.getTime()
                total_time = self.player.getTotalTime()
            except Exception:
                if showing_next_up_page:
                    next_up_page.close()
                    showing_next_up_page = False
                if showing_still_watching_page:
                    still_watching_page.close()
                    showing_still_watching_page = False
                break

            remaining = total_time - play_time
            runtime = episode['runtime']
            if not self.is_playback_paused():
                if showing_next_up_page:
                    next_up_page.update_progress_control(remaining=remaining, runtime=runtime)
                elif showing_still_watching_page:
                    still_watching_page.update_progress_control(remaining=remaining, runtime=runtime)
            sleep(100)
        return showing_next_up_page, showing_still_watching_page

    def extract_play_info(self, next_up_page, showing_next_up_page, showing_still_watching_page, still_watching_page):
        next_episode = True

        if showing_next_up_page:
            next_up_page.close()
            if next_up_page.is_cancel():
                next_episode = False
            else:
                played_in_a_row = int(get_property('tvwatch2_played_in_a_row')) + 1
                set_property('tvwatch2_played_in_a_row', str(played_in_a_row))
        elif showing_still_watching_page:
            set_property('tvwatch2_played_in_a_row', '1')
            still_watching_page.close()
            if not still_watching_page.is_cancel() and not still_watching_page.is_still_watching():
                next_episode = False

        clear_property('plugin.video.tvwatch2.dialog')
        return next_episode
