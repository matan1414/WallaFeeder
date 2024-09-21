import logging
import Enums
from bs4 import BeautifulSoup
#from seleniumbase import Driver
import time


class RSSObject:
    def __init__(self):
        self.title = ''
        self.id = ''
        self.url = ''
        self.published_date = ''
        self.description = ''
        self.image_url = ''


class RSSClass:
    rss_object = RSSObject()

    def __init__(self, _logger):
        self.logger = _logger


    def print_class(self):
        object_members = (f'Title: {self.rss_object.title} '
                          f'\nID: {self.rss_object.id}'
                          f'\nDescription: {self.rss_object.description} '
                          f'\nImage URL: {self.rss_object.image_url} '
                          f'\nPublished Date: {self.rss_object.published_date} '
                          f'\n\n To the product -> {self.rss_object.url}')
        return object_members

    def fetch_item(self, url):
        self.logger.debug('Fetch Agora.com!')
        self.agora_object.__init__()
        count = 0

        try:
            driver = Driver(uc=True, headless=True)
            driver.get(url)
            # Parse the HTML code using BeautifulSoup
            driver.wait_for_element('table#objectsTable', timeout=30)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            for row in soup.find_all('tr', class_='objectsTitleTr'):
                count = count + 1

                product_tmp_url = row.find('td', class_='newWindow').find('a').attrs['href']
                if 'giventake' in product_tmp_url:
                    self.agora_object.giventake_url = True
                    self.agora_object.product_url = product_tmp_url
                else:
                    self.agora_object.giventake_url = False
                    self.agora_object.product_url = Enums.LemesiraURLs.agora_main + product_tmp_url
                # await update.message.reply_text(objects_text)
                if count == 1:
                    break
        except NameError:
            self.logger.error("Error fetching url")
        except Exception as e:
            self.logger.error("Something else went wrong, the error is: ", e)
            # await update.message.reply_text("Something else went wrong, the error is: ", e)
        finally:
            self.logger.debug(f'driver.quit()')
            driver.quit()

        try:
            driver_product = Driver(uc=True, headless=True)
            driver_product.get(self.agora_object.product_url)
            if self.agora_object.giventake_url:
                driver_product.wait_for_element('div#content', timeout=30)
                time.sleep(1)
                soup_product = BeautifulSoup(driver_product.page_source, 'html.parser')
                self.agora_object.product_title = soup_product.find('div', class_='titleLine line-clamp line-clamp-2').find('h2', class_='listingTitle').text
                self.agora_object.product_state = soup_product.find('div', class_='titleLine line-clamp line-clamp-2').find('span', 'listingCondition starPlatinum').attrs['title'][10:]
                self.agora_object.product_reg_date = soup_product.find('span', class_='dateTime').text[8:]
                self.agora_object.product_id = soup_product.find('div', class_='listing').attrs['id']
                self.agora_object.product_details = soup_product.find('div', class_='listingDescription line-clamp line-clamp-2').text
                self.agora_object.product_city = soup_product.find('span', class_='city').text
            else:
                driver_product.wait_for_element('table#objectsTable', timeout=30)
                time.sleep(1)
                soup_product = BeautifulSoup(driver_product.page_source, 'html.parser')
                self.agora_object.product_title = soup_product.find('td', class_='objectName').text
                self.agora_object.product_state = soup_product.find('td', class_='objectState').attrs['title']
                self.agora_object.product_reg_date = soup_product.find('td', class_='regDate').text
                self.agora_object.product_id = soup_product.find('table').find('table').attrs['id']
                self.agora_object.product_details = soup_product.find('td', class_='details').text
                self.agora_object.product_region = soup_product.find('td', class_='leftSection').find_all('li')[0].text[6:]
                self.agora_object.product_city = soup_product.find('td', class_='leftSection').find_all('li')[1].find('a').text


        except NameError:
            self.logger.error("Error fetching url")
        except Exception as e:
            self.logger.error("Something else went wrong, the error is: ", e)
            # await update.message.reply_text("Something else went wrong, the error is: ", e)
        finally:
            self.logger.debug(f'driver_product.quit()')
            self.logger.debug(self.print_class())
            driver_product.quit()

        return self.agora_object

    def handle_item(self, item: RSSObject, listing_type):
        city_topic = self.handle_city_topic(item.product_city, item.product_region)

        if item.product_url == '':
            return False, city_topic  # 'Could not get product_url'
        if self.is_new_product(item.product_id, listing_type):
            return item, city_topic
        else:
            self.logger.debug(f'product id: {item.product_id} in category: {listing_type} is not a new product, '
                              'waiting for a new one')
            return False, city_topic  # 'This is not a new product'

    def is_new_entry(self, entry_id, category):
        last_id = getattr(Enums.LastEntriesIDs, category, None)
        if entry_id != last_id:
            setattr(Enums.LastEntriesIDs, category, entry_id)
            return True

    def handle_city_topic(self, _product_city, _product_region=None):
        if _product_region == 'גליל, גולן ועמקים':
            city_topic = Enums.LemesiraMainGroup.RamatHagolanGalil
        elif _product_region == 'חיפה, כרמל וקריות':
            city_topic = Enums.LemesiraMainGroup.Haifa
        elif _product_city in Enums.CitiesAndRegions.PetahTikva:
            city_topic = Enums.LemesiraMainGroup.PetahTikva
        elif _product_city in Enums.CitiesAndRegions.Ashdod:
            city_topic = Enums.LemesiraMainGroup.Ashdod
        elif _product_city in Enums.CitiesAndRegions.Yehud:
            city_topic = Enums.LemesiraMainGroup.Yehud
        elif _product_city in Enums.CitiesAndRegions.BeerSheva:
            city_topic = Enums.LemesiraMainGroup.BeerSheva
        elif _product_city in Enums.CitiesAndRegions.Eilat:
            city_topic = Enums.LemesiraMainGroup.Eilat
        elif _product_city in Enums.CitiesAndRegions.Jerusalem:
            city_topic = Enums.LemesiraMainGroup.Jerusalem
        elif _product_city in Enums.CitiesAndRegions.Ariel:
            city_topic = Enums.LemesiraMainGroup.Ariel
        elif _product_city in Enums.CitiesAndRegions.Modiin:
            city_topic = Enums.LemesiraMainGroup.Modiin
        elif _product_city in Enums.CitiesAndRegions.TelAviv:
            city_topic = Enums.LemesiraMainGroup.TelAviv
        elif _product_city in Enums.CitiesAndRegions.Herzliya:
            city_topic = Enums.LemesiraMainGroup.Herzliya
        elif _product_city in Enums.CitiesAndRegions.Netanya:
            city_topic = Enums.LemesiraMainGroup.Netanya
        elif _product_city in Enums.CitiesAndRegions.KfarSaba:
            city_topic = Enums.LemesiraMainGroup.KfarSaba
        elif _product_city in Enums.CitiesAndRegions.RishonLezion:
            city_topic = Enums.LemesiraMainGroup.RishonLezion
        else:
            city_topic = Enums.LemesiraMainGroup.General

        return city_topic
