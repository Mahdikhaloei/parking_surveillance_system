import json
import os
import sys
import logging
import django
import requests
from datetime import datetime
from requests.auth import HTTPDigestAuth
from django.core.files.base import ContentFile
from django.core.wsgi import get_wsgi_application
from django.db.utils import OperationalError
from django.core.exceptions import ObjectDoesNotExist

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def setup_django():
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    path = "/home/parking/backend"
    if path not in sys.path:
        sys.path.append(path)

    os.chdir(path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    django.setup()
    get_wsgi_application()


setup_django()
from apps.parking.models import CameraModel, EventModel


class DahuaCamera:
    def __init__(self, ip, username, password, port, event_code):
        self.ip = ip
        self.port = port
        self.event_code = event_code
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = HTTPDigestAuth(self.username, self.password)

    def get_snapshot(self, channel):
        """Capture a snapshot from the camera."""
        url = f"http://{self.ip}:{self.port}/cgi-bin/snapshot.cgi?channel={channel}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            logger.info(f"Snapshot captured successfully from channel {channel}")
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching snapshot: {e}")
            return None

    def monitor_events(self):
        """Monitor events from the camera."""
        url = f"http://{self.ip}:{self.port}/cgi-bin/eventManager.cgi?action=attach&codes=[{self.event_code}]"
        try:
            response = self.session.get(url, stream=True)
            logger.info(f"Connected to camera {self.ip} event stream")
            event_list = []
            for line in response.iter_lines():
                if line:
                    event_list.append(line.decode("utf-8"))
                else:
                    event = "\n".join(event_list)
                    self._process_event(event)
                    event_list = []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to event stream: {e}")

    def _process_event(self, event):
        """Process an event and save it to the database."""
        if "Code=CrossLineDetection" in event and "action=Start" in event:
            try:
                data_json_str = event[event.find("data=") + len("data="):event.rfind("}") + 1]
                data_dict = json.loads(data_json_str)
                tripwire_name = data_dict.get("Name", "")

                camera_instance = CameraModel.objects.get(tripwire=tripwire_name)

                image_data = self.get_snapshot(channel=camera_instance.channel)
                if image_data:
                    self._save_event(camera_instance, event, image_data)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse event JSON: {event}")
            except ObjectDoesNotExist:
                logger.warning(f"No camera found for tripwire: {tripwire_name}")
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    def _save_event(self, camera, event_info, image_data):
        """Save event data to the database."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"snapshot_{timestamp}.jpg"

            event_instance = EventModel(camera=camera, info=event_info)
            event_instance.snapshot.save(file_name, ContentFile(image_data), save=True)
            event_instance.save()

            logger.info(f"Event saved: {event_instance}")
        except OperationalError as e:
            logger.error(f"Database error: {e}")
        except Exception as e:
            logger.error(f"Error saving event: {e}")

def main():
    DVR_IP = os.getenv("DVR_IP")
    DVR_PORT = os.getenv("DVR_PORT")
    USERNAME = os.getenv("DVR_USERNAME")
    PASSWORD = os.getenv("DVR_PASSWORD")
    EVENT_CODE = "CrossLineDetection"

    if not all([DVR_IP, DVR_PORT, USERNAME, PASSWORD]):
        logger.error("Missing environment variables for DVR connection")
        sys.exit(1)

    camera = DahuaCamera(ip=DVR_IP, username=USERNAME, password=PASSWORD, port=DVR_PORT, event_code=EVENT_CODE)
    camera.monitor_events()

if __name__ == "__main__":
    main()
